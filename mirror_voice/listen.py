"""Microphone -> local Whisper -> local LLM -> Mirror Hands."""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import queue
import threading
from time import monotonic

from .capture import analyze, audio_device
from .engine import MirrorVoiceEngine
from .llm import LocalChatSemanticEar
from .lexicon import analyze_text
from .model import AcousticFrame
from .osc import MirrorOSCSender


class PhraseSegmenter:
    def __init__(self, sample_rate: int, block_seconds: float, threshold: float = .008,
                 endpoint_seconds: float = .7, min_seconds: float = .35,
                 max_seconds: float = 12.0, preroll_seconds: float = .25):
        self.sample_rate, self.block_seconds, self.threshold = sample_rate, block_seconds, threshold
        self.endpoint_blocks = max(1, round(endpoint_seconds / block_seconds))
        self.min_samples, self.max_samples = int(min_seconds * sample_rate), int(max_seconds * sample_rate)
        self.preroll = deque(maxlen=max(1, round(preroll_seconds / block_seconds)))
        self.parts: list = []
        self.quiet_blocks = 0

    def push(self, samples, raw_rms: float):
        import numpy as np

        block = np.asarray(samples, dtype=np.float32).reshape(-1).copy()
        active = raw_rms >= self.threshold
        if not self.parts:
            if not active:
                self.preroll.append(block)
                return None
            self.parts = list(self.preroll) + [block]
            self.preroll.clear()
            self.quiet_blocks = 0
            return None
        self.parts.append(block)
        self.quiet_blocks = 0 if active else self.quiet_blocks + 1
        count = sum(len(part) for part in self.parts)
        if count >= self.max_samples or self.quiet_blocks >= self.endpoint_blocks:
            phrase = np.concatenate(self.parts)
            self.parts, self.quiet_blocks = [], 0
            self.preroll.append(block)
            return phrase if len(phrase) >= self.min_samples else None
        return None


def cached_mlx_model(name: str) -> str:
    root = Path.home() / ".cache/huggingface/hub" / ("models--" + name.replace("/", "--")) / "snapshots"
    snapshots = sorted(root.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True) if root.exists() else []
    return str(snapshots[0]) if snapshots else name


def transcribe_mlx(samples, model: str, language: str | None = None) -> str:
    import mlx_whisper

    options = {"path_or_hf_repo": model, "verbose": False}
    if language:
        options["language"] = language
    result = mlx_whisper.transcribe(samples, **options)
    return str(result.get("text", "")).strip()


def main() -> None:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise SystemExit("Install microphone extras: pip install -e '.[voice]'") from exc

    parser = argparse.ArgumentParser(description="Speak to local Whisper/Gemma and hear Mirror Voice in Ableton")
    parser.add_argument("--device", type=audio_device)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--block-seconds", type=float, default=.1)
    parser.add_argument("--threshold", type=float, default=.008)
    parser.add_argument("--endpoint-seconds", type=float, default=.7)
    parser.add_argument("--debug-levels", action="store_true", help="Print one-second RMS/VAD diagnostics")
    parser.add_argument("--whisper-model", default="mlx-community/whisper-small-mlx")
    parser.add_argument("--language")
    parser.add_argument("--local-model", default="google/gemma-4-e2b")
    parser.add_argument("--local-url", default="http://127.0.0.1:1234/api/v1/chat")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    audio_blocks, phrases, meanings = queue.Queue(maxsize=16), queue.Queue(maxsize=2), queue.Queue()
    # Language leads the instrument; acoustics and silence shade rather than
    # erase the most recently understood phrase.
    engine, sender = MirrorVoiceEngine(semantic_weight=.8), MirrorOSCSender(port=args.port)
    ear = LocalChatSemanticEar(args.local_model, args.local_url)
    segmenter = PhraseSegmenter(args.sample_rate, args.block_seconds, args.threshold, args.endpoint_seconds)
    whisper_model = cached_mlx_model(args.whisper_model)
    stopped = threading.Event()

    def transcriber():
        while not stopped.is_set():
            samples = phrases.get()
            if samples is None:
                return
            try:
                text = transcribe_mlx(samples, whisper_model, args.language)
                if text:
                    # Respond musically at Whisper speed; the slower LLM then
                    # arrives as a semantic refinement rather than a blocker.
                    meanings.put((text, analyze_text(text), None))
                    meanings.put((text, ear.analyze(text), None))
            except Exception as exc:
                meanings.put(("", None, str(exc)))

    worker = threading.Thread(target=transcriber, name="mirror-whisper", daemon=True)
    worker.start()

    def callback(data, frames, time_info, status):
        try:
            audio_blocks.put_nowait(data[:, 0].copy())
        except queue.Full:
            pass

    previous_rms, silence, latest = 0.0, 0.0, AcousticFrame()
    level_peak, level_blocks, next_level_report = 0.0, 0, monotonic() + 1.0
    print(json.dumps({"status": "listening", "whisper_model": whisper_model, "semantic_model": args.local_model}), flush=True)
    try:
        with sd.InputStream(device=args.device, channels=1, samplerate=args.sample_rate,
                            blocksize=int(args.sample_rate * args.block_seconds), callback=callback):
            while True:
                samples = audio_blocks.get()
                raw_rms = float(np.sqrt(np.mean(np.square(samples))))
                level_peak, level_blocks = max(level_peak, raw_rms), level_blocks + 1
                latest = analyze(samples, args.sample_rate, previous_rms, silence)
                silence = silence + args.block_seconds if raw_rms < args.threshold else 0.0
                latest.silence_seconds, previous_rms = silence, latest.rms
                phrase = segmenter.push(samples, raw_rms)
                if phrase is not None:
                    if args.debug_levels:
                        print(json.dumps({"vad": "phrase_complete", "seconds": round(len(phrase) / args.sample_rate, 2)}), flush=True)
                    try:
                        phrases.put_nowait(phrase)
                    except queue.Full:
                        print(json.dumps({"warning": "transcriber busy; phrase skipped"}), flush=True)
                semantic = None
                try:
                    while True:
                        text, candidate, error = meanings.get_nowait()
                        if error:
                            print(json.dumps({"semantic_warning": error}), flush=True)
                        elif candidate:
                            semantic = candidate
                            print(json.dumps({"transcript": text, "semantic": candidate.values}), flush=True)
                except queue.Empty:
                    pass
                sender.send(engine.update(latest, semantic=semantic, now=monotonic()))
                if args.debug_levels and monotonic() >= next_level_report:
                    print(json.dumps({"mic_peak_rms": round(level_peak, 5), "threshold": args.threshold,
                                      "vad_active": bool(segmenter.parts), "quiet_blocks": segmenter.quiet_blocks}), flush=True)
                    level_peak, level_blocks, next_level_report = 0.0, 0, monotonic() + 1.0
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        try:
            phrases.put_nowait(None)
        except queue.Full:
            pass
        sender.close()


if __name__ == "__main__":
    main()
