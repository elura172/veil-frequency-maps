from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import monotonic

QUALITIES = ("energy", "brightness", "warmth", "shimmer", "motion", "density")


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class AcousticFrame:
    rms: float = 0.0
    pitch_hz: float = 0.0
    pitch_confidence: float = 0.0
    centroid_hz: float = 0.0
    onset_rate: float = 0.0
    speech_rate: float = 0.0
    silence_seconds: float = 0.0


@dataclass
class SemanticFrame:
    values: dict[str, float] = field(default_factory=lambda: {key: 0.5 for key in QUALITIES})
    confidence: float = 0.0
    source: str = "local"


@dataclass
class MirrorState:
    values: dict[str, float] = field(default_factory=lambda: {key: 0.0 for key in QUALITIES})
    acoustic: AcousticFrame = field(default_factory=AcousticFrame)
    semantic_confidence: float = 0.0
    silence_presence: float = 0.0
    updated_at: float = field(default_factory=monotonic)

    def to_dict(self) -> dict:
        result = {"qualities": dict(self.values), "acoustic": asdict(self.acoustic)}
        result.update({"semantic_confidence": self.semantic_confidence, "silence_presence": self.silence_presence})
        return result

