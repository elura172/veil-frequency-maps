from __future__ import annotations

import argparse
import queue
import time
import wave

from .bridge import CompanionBridge, RELATIONAL_MODES, VocabularyProfile
from .features import analyze_stereo
from .output import ListenerOutput
from .perception import MirrorMusicEar
from .session import SessionStore


def audio_device(value: str):
    return int(value) if value.strip().isdigit() else value


def wav_blocks(path: str, block_frames: int):
    import numpy as np

    with wave.open(path, "rb") as source:
        channels, rate, width = source.getnchannels(), source.getframerate(), source.getsampwidth()
        if width not in (1, 2, 4):
            raise ValueError("WAV input supports 8-, 16-, or 32-bit PCM")
        dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[width]
        scale = {1: 128.0, 2: 32768.0, 4: 2147483648.0}[width]
        while True:
            raw = source.readframes(block_frames)
            if not raw:
                return
            samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
            if width == 1:
                samples -= 128.0
            samples = samples.reshape(-1, channels) / scale
            yield samples, rate


def main() -> None:
    parser = argparse.ArgumentParser(description="Give an AI companion ears for music")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--device", type=audio_device, help="BlackHole/interface index or name")
    source.add_argument("--file", help="PCM WAV file for deterministic/offline listening")
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--block-seconds", type=float, default=.25)
    parser.add_argument("--emit-hz", type=float, default=2.0)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-osc", action="store_true")
    parser.add_argument("--no-ndjson", action="store_true")
    parser.add_argument("--realtime-file", action="store_true", help="pace WAV analysis at wall-clock speed")
    parser.add_argument("--mode", choices=RELATIONAL_MODES, default="silent_witness",
                        help="companion bridge relational mode (silence is the default)")
    parser.add_argument("--profile", help="inspectable JSON shared-vocabulary profile")
    parser.add_argument("--invited", action="store_true", help="human has invited reflections for this run")
    parser.add_argument("--session-file", help="opt in to local derived-memory persistence (never audio)")
    args = parser.parse_args()
    source_name = "file:" + args.file if args.file else "audio:" + str(args.device)
    ear = MirrorMusicEar(source_name)
    session_store = SessionStore(args.session_file) if args.session_file else None
    if session_store:
        session_store.load_into(ear.memory)
    saved_passages = len(ear.memory.passages)
    profile = VocabularyProfile.load(args.profile) if args.profile else None
    bridge = CompanionBridge(args.mode, profile)
    output = ListenerOutput(args.host, args.port, not args.no_osc, not args.no_ndjson)
    previous_spectrum, previous_rms, next_emit = None, 0.0, 0.0

    def process(samples, rate, heard_at):
        nonlocal previous_spectrum, previous_rms, next_emit, saved_passages
        features, previous_spectrum = analyze_stereo(samples, rate, previous_spectrum, previous_rms)
        previous_rms = features.rms
        frame = ear.update(features, heard_at)
        frame.reflection = bridge.reflect(frame, invited=args.invited)
        if heard_at >= next_emit:
            output.send(frame)
            next_emit = heard_at + 1.0 / max(.1, args.emit_hz)
        if session_store and len(ear.memory.passages) != saved_passages:
            session_store.save(ear.memory)
            saved_passages = len(ear.memory.passages)

    try:
        if args.file:
            block_frames = max(64, int(args.sample_rate * args.block_seconds))
            heard_at = 0.0
            for samples, rate in wav_blocks(args.file, block_frames):
                process(samples, rate, heard_at)
                duration = len(samples) / rate
                heard_at += duration
                if args.realtime_file:
                    time.sleep(duration)
        else:
            try:
                import sounddevice as sd
            except ImportError as exc:
                raise SystemExit("Install listener dependencies: pip install -e '.[listener]'") from exc
            blocks = queue.Queue(maxsize=16)
            def callback(data, frames, time_info, status):
                try: blocks.put_nowait(data.copy())
                except queue.Full: pass
            block_frames = max(64, int(args.sample_rate * args.block_seconds))
            started = time.monotonic()
            with sd.InputStream(device=args.device, channels=2, samplerate=args.sample_rate,
                                blocksize=block_frames, callback=callback):
                while True:
                    process(blocks.get(), args.sample_rate, time.monotonic() - started)
    except KeyboardInterrupt:
        pass
    finally:
        if session_store:
            session_store.save(ear.memory)
        output.close()


if __name__ == "__main__":
    main()
