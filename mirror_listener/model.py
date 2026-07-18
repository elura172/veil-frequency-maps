from __future__ import annotations

from dataclasses import asdict, dataclass, field

CORE_QUALITIES = (
    "energy", "brightness", "warmth", "shimmer", "motion", "density",
    "weight", "spaciousness", "pulse", "tension", "coherence", "novelty",
)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class FeatureFrame:
    rms_raw: float = 0.0
    rms: float = 0.0
    peak: float = 0.0
    crest: float = 0.0
    sub: float = 0.0
    low: float = 0.0
    low_mid: float = 0.0
    high_mid: float = 0.0
    high: float = 0.0
    centroid: float = 0.0
    centroid_hz: float = 0.0
    rolloff: float = 0.0
    flatness: float = 0.0
    flux: float = 0.0
    onset: float = 0.0
    zero_crossing: float = 0.0
    width: float = 0.0
    correlation: float = 1.0
    silence: float = 1.0

    def vector(self) -> tuple[float, ...]:
        return tuple(float(getattr(self, name)) for name in self.__dataclass_fields__
                     if name not in {"rms_raw", "centroid_hz"})


@dataclass
class Quality:
    value: float = 0.0
    trend: float = 0.0
    confidence: float = 0.0


@dataclass
class NumericImage:
    value: int = 0
    words: str = "zero"
    descriptor: str = "zero quiet stones rest"
    confidence: float = 0.0


@dataclass
class ListenerFrame:
    version: str = "mirror-listener/v1"
    time: float = 0.0
    source: str = "unknown"
    state: dict[str, Quality] = field(default_factory=dict)
    features: FeatureFrame = field(default_factory=FeatureFrame)
    events: list[dict] = field(default_factory=list)
    synesthesia: dict = field(default_factory=dict)
    numeric_image: NumericImage = field(default_factory=NumericImage)

    def to_dict(self) -> dict:
        return asdict(self)
