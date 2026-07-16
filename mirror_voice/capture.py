"""Optional real-time microphone front end (requires numpy and sounddevice)."""

from __future__ import annotations

import argparse
import queue
from time import monotonic

from .engine import MirrorVoiceEngine
from .model import AcousticFrame
from .osc import MirrorOSCSender


def analyze(samples, sample_rate: int, previous_rms: float = 0.0, silence_seconds: float = 0.0) -> AcousticFrame:
    import numpy as np

    mono = np.asarray(samples, dtype=np.float32).reshape(-1)
    if not len(mono):
        return AcousticFrame(silence_seconds=silence_seconds)
    rms_raw = float(np.sqrt(np.mean(np.square(mono))))
    rms = min(1.0, rms_raw * 8.0)
    windowed = mono * np.hanning(len(mono))
    spectrum = np.abs(np.fft.rfft(windowed))
    frequencies = np.fft.rfftfreq(len(mono), 1.0 / sample_rate)
    total = float(spectrum.sum())
    centroid = float((spectrum * frequencies).sum() / total) if total else 0.0

    pitch, confidence = 0.0, 0.0
    if rms_raw > .004:
        correlation = np.correlate(mono, mono, mode="full")[len(mono)-1:]
        low, high = max(1, sample_rate // 1000), min(len(correlation), sample_rate // 55)
        if high > low:
            lag = low + int(np.argmax(correlation[low:high]))
            pitch = sample_rate / lag
            confidence = min(1.0, float(correlation[lag] / max(correlation[0], 1e-9)))
    onset = min(1.0, max(0.0, rms - previous_rms) * 5.0)
    active = rms_raw > .008
    return AcousticFrame(
        rms=rms, pitch_hz=pitch, pitch_confidence=confidence, centroid_hz=centroid,
        onset_rate=onset, speech_rate=min(1.0, onset * .5 + rms * .5),
        silence_seconds=0.0 if active else silence_seconds,
    )


def main() -> None:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise SystemExit("Install microphone extras: pip install -e '.[voice]'") from exc
    parser = argparse.ArgumentParser(description="Microphone to Mirror Voice OSC")
    parser.add_argument("--device")
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--block-seconds", type=float, default=.1)
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    blocks, engine, sender = queue.Queue(maxsize=8), MirrorVoiceEngine(), MirrorOSCSender(port=args.port)

    def callback(data, frames, time_info, status):
        try: blocks.put_nowait(data[:, 0].copy())
        except queue.Full: pass

    previous_rms, silence = 0.0, 0.0
    try:
        with sd.InputStream(device=args.device, channels=1, samplerate=args.sample_rate, blocksize=int(args.sample_rate * args.block_seconds), callback=callback):
            while True:
                frame = analyze(blocks.get(), args.sample_rate, previous_rms, silence)
                silence = silence + args.block_seconds if frame.rms < .064 else 0.0
                frame.silence_seconds = silence
                previous_rms = frame.rms
                sender.send(engine.update(frame, now=monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        sender.close()


if __name__ == "__main__":
    main()
