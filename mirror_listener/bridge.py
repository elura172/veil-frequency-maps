from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re

from .model import CORE_QUALITIES, ListenerFrame, clamp


RELATIONAL_MODES = (
    "silent_witness", "gentle_mirror", "shared_attention", "curious_listener",
    "poetic_companion", "analytical_ear", "memory_keeper",
)


@dataclass
class VocabularyProfile:
    id: str = "default"
    associations: dict[str, str] = field(default_factory=dict)
    notes: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "VocabularyProfile":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        associations = data.get("associations", {})
        if not isinstance(associations, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in associations.items()):
            raise ValueError("profile associations must map strings to strings")
        return cls(str(data.get("id", "personal")), associations, list(data.get("notes", [])))

    def apply(self, text: str) -> str:
        for source, replacement in sorted(self.associations.items(), key=lambda item: -len(item[0])):
            text = re.sub(rf"\b{re.escape(source)}\b", lambda _: replacement, text, flags=re.IGNORECASE)
        return text

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ModePolicy:
    minimum_novelty: float
    cooldown: float
    invitation: bool = False


POLICIES = {
    "silent_witness": ModePolicy(1.0, 1e9),
    "gentle_mirror": ModePolicy(.55, 18.0),
    "shared_attention": ModePolicy(.48, 14.0, True),
    "curious_listener": ModePolicy(.45, 12.0, True),
    "poetic_companion": ModePolicy(.50, 16.0),
    "analytical_ear": ModePolicy(.35, 7.0),
    "memory_keeper": ModePolicy(.70, 10.0),
}


class CompanionBridge:
    """Sparse, deterministic context adapter that never impersonates a companion."""

    def __init__(self, mode: str = "silent_witness", profile: VocabularyProfile | None = None):
        if mode not in RELATIONAL_MODES:
            raise ValueError(f"unknown relational mode: {mode}")
        self.mode = mode
        self.profile = profile or VocabularyProfile()
        self.last_reflection = -1e9

    def _observation(self, frame: ListenerFrame, recurrence: dict | None) -> tuple[str, str]:
        if recurrence:
            return (f"A passage resembling {recurrence['passage_id']} is returning.", "memory")
        strongest = max(CORE_QUALITIES, key=lambda name: abs(frame.state[name].trend))
        quality = frame.state[strongest]
        direction = "gathering" if quality.trend >= 0 else "receding"
        if self.mode == "poetic_companion":
            return (frame.numeric_image.descriptor.capitalize() + ".", "metaphor")
        if self.mode == "analytical_ear":
            return (f"{strongest.capitalize()} is {direction} at {quality.value:.2f} with confidence {quality.confidence:.2f}.", "inference")
        color = frame.synesthesia.get("color", {}).get("primary")
        suffix = f" The field suggests {color}." if color else ""
        return (f"{strongest.capitalize()} is {direction}.{suffix}", "inference")

    def reflect(self, frame: ListenerFrame, invited: bool = False) -> dict:
        policy = POLICIES[self.mode]
        base = {"mode": self.mode, "action": "silence", "profile": self.profile.id}
        if self.mode == "silent_witness":
            return {**base, "reason": "mode_prefers_silence"}
        if frame.time - self.last_reflection < policy.cooldown:
            return {**base, "reason": "cooldown"}

        recurrence = frame.memory.get("recurrence")
        novelty = frame.state.get("novelty")
        novelty_value = novelty.value if novelty else 0.0
        confidence = sum(item.confidence for item in frame.state.values()) / max(len(frame.state), 1)
        event_strength = max((event.get("strength", 0.0) for event in frame.events), default=0.0)
        meaningful = bool(recurrence) or novelty_value >= policy.minimum_novelty or event_strength >= policy.minimum_novelty
        if not (invited or meaningful):
            return {**base, "reason": "no_meaningful_change"}
        if confidence < .25 and not invited:
            return {**base, "reason": "low_confidence"}
        if self.mode == "memory_keeper" and not recurrence:
            return {**base, "reason": "no_recurrence"}

        observation, register = self._observation(frame, recurrence)
        observation = self.profile.apply(observation)
        invitation = None
        if policy.invitation:
            invitation = "What do you notice there?" if self.mode == "curious_listener" else "Does that resemble what you are hearing?"
        self.last_reflection = frame.time
        return {
            **base,
            "action": "offer_context",
            "observation": observation,
            "invitation": invitation,
            "register": register,
            "uncertainty": clamp(1.0 - confidence),
            "evidence": {
                "novelty": novelty_value,
                "event_strength": event_strength,
                "recurrence": recurrence,
            },
            "preserve_companion_voice": True,
        }
