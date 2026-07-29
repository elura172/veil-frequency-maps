from __future__ import annotations

from collections import deque
import math

from .language import number_words, poetic_descriptor
from .memory import TemporalMemory
from .model import CORE_QUALITIES, FeatureFrame, ListenerFrame, NumericImage, Quality, clamp
from .synesthesia import SynestheticMapper


def _entropy(values: list[float]) -> float:
    total = max(sum(values), 1e-12)
    probabilities = [max(value / total, 1e-12) for value in values]
    return clamp(-sum(p * math.log(p) for p in probabilities) / math.log(len(probabilities)))


class MirrorMusicEar:
    """Stateful deterministic mapping from stereo evidence to musical perception."""

    def __init__(self, source: str = "unknown", half_life: float = 1.2, number_half_life: float = 3.5,
                 passage_seconds: float = 12.0):
        self.source = source
        self.half_life = max(.05, half_life)
        self.number_half_life = max(.2, number_half_life)
        self.values = {name: 0.0 for name in CORE_QUALITIES}
        self.previous_values = dict(self.values)
        self.feature_mean: list[float] | None = None
        self.onsets = deque(maxlen=64)
        self.last_time: float | None = None
        self.number_value = 0.0
        self.last_events = {name: -1e9 for name in CORE_QUALITIES}
        self.memory = TemporalMemory(passage_seconds=passage_seconds)
        self.synesthetic_mapper = SynestheticMapper()

    def _pulse(self) -> float:
        if len(self.onsets) < 12:
            return clamp(sum(self.onsets) / max(len(self.onsets), 1))
        import numpy as np

        signal = np.asarray(self.onsets, dtype=float)
        signal -= signal.mean()
        energy = float(np.dot(signal, signal))
        if energy < 1e-8:
            return 0.0
        scores = [float(np.dot(signal[lag:], signal[:-lag]) / energy) for lag in range(3, min(32, len(signal) // 2))]
        return clamp(max(scores, default=0.0) * 1.8)

    def _targets(self, f: FeatureFrame) -> dict[str, float]:
        if f.silence >= .999:
            self.onsets.append(0.0)
            return {name: 0.0 for name in CORE_QUALITIES}

        bands = [f.sub, f.low, f.low_mid, f.high_mid, f.high]
        density = clamp(_entropy(bands) * .65 + f.flatness * .35)
        vector = list(f.vector())
        if self.feature_mean is None:
            novelty = 0.0
            self.feature_mean = vector
        else:
            novelty = clamp(math.sqrt(sum((a - b) ** 2 for a, b in zip(vector, self.feature_mean)) / len(vector)) * 3.0)
            self.feature_mean = [old * .97 + new * .03 for old, new in zip(self.feature_mean, vector)]
        self.onsets.append(f.onset)
        pulse = self._pulse()
        return {
            "energy": clamp(f.rms * .72 + f.peak * .18 + f.onset * .10),
            "brightness": clamp(f.centroid * .55 + f.high_mid * .22 + f.high * .23),
            "warmth": clamp(f.low_mid * .52 + f.low * .25 + (1.0 - f.flatness) * .15 + (1.0 - f.centroid) * .08),
            "shimmer": clamp(f.high * .38 + f.high_mid * .18 + f.flux * .28 + f.width * .16),
            "motion": clamp(f.flux * .46 + f.onset * .34 + f.zero_crossing * .20),
            "density": density,
            "weight": clamp(f.sub * .58 + f.low * .32 + f.rms * .10),
            "spaciousness": clamp(f.width * .55 + (1.0 - f.correlation) * .30 + (1.0 - density) * .15),
            "pulse": pulse,
            "tension": clamp(f.high_mid * .22 + f.flatness * .25 + f.flux * .23 + f.crest * .18 + novelty * .12),
            "coherence": clamp((1.0 - f.flatness) * .35 + f.correlation * .25 + (1.0 - f.flux) * .25 + pulse * .15),
            "novelty": novelty,
        }

    def update(self, features: FeatureFrame, now: float) -> ListenerFrame:
        first = self.last_time is None
        dt = .25 if first else max(.001, now - self.last_time)
        self.last_time = now
        targets = self._targets(features)
        alpha = 1.0 if not any(self.values.values()) else 1.0 - math.pow(.5, dt / self.half_life)
        self.previous_values = dict(self.values)
        for name in CORE_QUALITIES:
            self.values[name] = clamp(self.values[name] + (targets[name] - self.values[name]) * alpha)

        evidence = clamp(features.rms * 3.5) * (1.0 - features.silence * .65)
        confidence = clamp(evidence * .94)
        state = {}
        events = []
        verbs = {
            "energy": ("fading", "gathering"), "brightness": ("darkening", "opening"),
            "warmth": ("cooling", "warming"), "shimmer": ("dimming", "crystallizing"),
            "motion": ("settling", "flowing"), "density": ("thinning", "thickening"),
            "weight": ("lifting", "grounding"), "spaciousness": ("closing", "widening"),
            "pulse": ("loosening", "stabilizing"), "tension": ("releasing", "tightening"),
            "coherence": ("scattering", "finding ground"), "novelty": ("returning", "transforming"),
        }
        for name in CORE_QUALITIES:
            trend = max(-1.0, min(1.0, (self.values[name] - self.previous_values[name]) / dt))
            state[name] = Quality(self.values[name], trend, confidence)
            if not first and abs(trend) >= .18 and now - self.last_events[name] >= 2.0:
                direction = 1 if trend > 0 else 0
                events.append({"quality": name, "verb": verbs[name][direction],
                               "strength": clamp(abs(trend)), "confidence": confidence})
                self.last_events[name] = now

        memory, memory_events = self.memory.update(
            now, self.values, sum(quality.confidence for quality in state.values()) / len(state)
        )
        events.extend(memory_events)
        for name, quality in state.items():
            moment = memory["moment"]
            gesture = memory["gesture"]
            quality.short_trend = max(-1.0, min(1.0, (quality.value - moment["state"][name]) / 2.0))
            quality.long_trend = max(-1.0, min(1.0, (quality.value - gesture["state"][name]) / 12.0))
            quality.recent_min, quality.recent_max = gesture["range"][name]

        composite = (
            self.values["energy"] * .14 + self.values["brightness"] * .10 + self.values["warmth"] * .08 +
            self.values["shimmer"] * .09 + self.values["motion"] * .09 + self.values["density"] * .09 +
            self.values["weight"] * .08 + self.values["spaciousness"] * .08 + self.values["pulse"] * .08 +
            self.values["tension"] * .06 + self.values["coherence"] * .06 + self.values["novelty"] * .05
        ) * 99.0
        number_alpha = 1.0 if self.number_value == 0 else 1.0 - math.pow(.5, dt / self.number_half_life)
        candidate = self.number_value + (composite - self.number_value) * number_alpha
        if abs(candidate - self.number_value) >= .35 or self.number_value == 0:
            self.number_value = candidate
        number = max(0, min(99, round(self.number_value)))

        synesthesia = self.synesthetic_mapper.map(self.values, features, confidence)
        numeric = NumericImage(number, number_words(number), poetic_descriptor(number, self.values), confidence * .78)
        return ListenerFrame(time=now, source=self.source, state=state, features=features,
                             events=events, synesthesia=synesthesia, numeric_image=numeric, memory=memory)
