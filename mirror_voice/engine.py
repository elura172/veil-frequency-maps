from __future__ import annotations

import math
from time import monotonic

from .lexicon import analyze_text
from .model import AcousticFrame, MirrorState, QUALITIES, SemanticFrame, clamp


def acoustic_qualities(frame: AcousticFrame) -> dict[str, float]:
    pitch = clamp((math.log2(max(frame.pitch_hz, 55.0) / 55.0)) / 6.0) if frame.pitch_hz else 0.0
    centroid = clamp(math.log10(max(frame.centroid_hz, 80.0) / 80.0) / math.log10(10000.0 / 80.0)) if frame.centroid_hz else 0.0
    silence = 1.0 - math.exp(-max(0.0, frame.silence_seconds) / 4.0)
    return {
        "energy": clamp(frame.rms * .72 + frame.onset_rate * .18 + frame.speech_rate * .10),
        "brightness": clamp(centroid * .72 + pitch * frame.pitch_confidence * .28),
        "warmth": clamp((1.0 - centroid) * .5 + frame.rms * .22 + (1.0 - pitch) * .18 + silence * .10),
        "shimmer": clamp(centroid * .5 + frame.pitch_confidence * .25 + frame.onset_rate * .15 + silence * .10),
        "motion": clamp(frame.onset_rate * .45 + frame.speech_rate * .35 + abs(frame.rms - .35) * .20),
        "density": clamp(frame.rms * .4 + frame.speech_rate * .35 + frame.onset_rate * .25),
    }


class MirrorVoiceEngine:
    def __init__(self, half_life_seconds: float = 0.8, semantic_weight: float = 0.56):
        self.state = MirrorState()
        self.half_life = max(0.01, half_life_seconds)
        self.semantic_weight = clamp(semantic_weight)
        self.initialized = False

    def update(self, acoustic: AcousticFrame | None = None, text: str | None = None, semantic: SemanticFrame | None = None, now: float | None = None) -> MirrorState:
        now = monotonic() if now is None else now
        acoustic = acoustic or self.state.acoustic
        semantic = semantic or analyze_text(text or "")
        physical = acoustic_qualities(acoustic)
        semantic_mix = self.semantic_weight * semantic.confidence
        target = {key: physical[key] * (1.0 - semantic_mix) + semantic.values[key] * semantic_mix for key in QUALITIES}

        silence_presence = 1.0 - math.exp(-max(0.0, acoustic.silence_seconds) / 5.0)
        # Silence is presence with low motion/density, not a reset to black.
        target["motion"] *= 1.0 - silence_presence * .72
        target["density"] *= 1.0 - silence_presence * .78
        target["warmth"] = clamp(target["warmth"] + silence_presence * .12)
        target["shimmer"] = clamp(target["shimmer"] + silence_presence * .08)

        dt = max(0.0, now - self.state.updated_at)
        alpha = 1.0 if not self.initialized else 1.0 - math.pow(0.5, dt / self.half_life)
        for key in QUALITIES:
            delta = target[key] - self.state.values[key]
            if abs(delta) < 0.012:  # small hysteresis prevents nervous twitching
                continue
            self.state.values[key] = clamp(self.state.values[key] + delta * alpha)
        self.state.acoustic = acoustic
        self.state.semantic_confidence = semantic.confidence
        self.state.silence_presence = silence_presence
        self.state.updated_at = now
        self.initialized = True
        return self.state
