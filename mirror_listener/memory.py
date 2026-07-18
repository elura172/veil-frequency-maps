from __future__ import annotations

from collections import deque
import math

from .model import CORE_QUALITIES, clamp


def _mean(states: list[dict[str, float]]) -> dict[str, float]:
    if not states:
        return {name: 0.0 for name in CORE_QUALITIES}
    return {name: sum(state[name] for state in states) / len(states) for name in CORE_QUALITIES}


def _similarity(left: dict[str, float], right: dict[str, float]) -> float:
    distance = math.sqrt(sum((left[name] - right[name]) ** 2 for name in CORE_QUALITIES) / len(CORE_QUALITIES))
    return clamp(1.0 - distance * 1.6)


class TemporalMemory:
    """Bounded moment/gesture/passage memory with deterministic recurrence."""

    def __init__(self, passage_seconds: float = 12.0, retention_seconds: float = 90.0):
        self.passage_seconds = max(2.0, passage_seconds)
        self.retention_seconds = max(self.passage_seconds, retention_seconds)
        self.frames: deque[tuple[float, dict[str, float], float]] = deque()
        self.passages: list[dict] = []
        self.segment: list[tuple[float, dict[str, float], float]] = []
        self.segment_started: float | None = None
        self.extrema = {name: {"min": 1.0, "max": 0.0} for name in CORE_QUALITIES}

    def _window(self, now: float, seconds: float) -> list[dict[str, float]]:
        return [state for at, state, _ in self.frames if at >= now - seconds]

    def _summary(self, now: float, seconds: float) -> dict:
        states = self._window(now, seconds)
        values = _mean(states)
        return {
            "seconds": seconds,
            "samples": len(states),
            "state": values,
            "range": {
                name: [min((state[name] for state in states), default=0.0),
                       max((state[name] for state in states), default=0.0)]
                for name in CORE_QUALITIES
            },
        }

    def _close_passage(self, ended: float) -> tuple[dict, dict | None]:
        states = [state for _, state, _ in self.segment]
        confidence = sum(item[2] for item in self.segment) / max(len(self.segment), 1)
        passage = {
            "id": f"passage-{len(self.passages) + 1:04d}",
            "start": self.segment_started,
            "end": ended,
            "state": _mean(states),
            "confidence": confidence,
        }
        best = None
        for remembered in self.passages:
            similarity = _similarity(passage["state"], remembered["state"])
            if best is None or similarity > best["similarity"]:
                best = {"passage_id": remembered["id"], "similarity": similarity,
                        "confidence": min(confidence, remembered["confidence"]) * similarity}
        self.passages.append(passage)
        return passage, best if best and best["similarity"] >= .82 else None

    def update(self, now: float, state: dict[str, float], confidence: float) -> tuple[dict, list[dict]]:
        state = dict(state)
        self.frames.append((now, state, confidence))
        while self.frames and self.frames[0][0] < now - self.retention_seconds:
            self.frames.popleft()
        for name, value in state.items():
            self.extrema[name]["min"] = min(self.extrema[name]["min"], value)
            self.extrema[name]["max"] = max(self.extrema[name]["max"], value)

        if self.segment_started is None:
            self.segment_started = now
        self.segment.append((now, state, confidence))
        events = []
        recurrence = None
        if now - self.segment_started >= self.passage_seconds:
            passage, recurrence = self._close_passage(now)
            events.append({"type": "passage", "verb": "remembering", "passage_id": passage["id"],
                           "strength": passage["confidence"], "confidence": passage["confidence"]})
            if recurrence:
                events.append({"type": "recurrence", "verb": "returning", **recurrence})
            self.segment = []
            self.segment_started = now

        current_passage = _mean([item[1] for item in self.segment])
        memory = {
            "moment": self._summary(now, 2.0),
            "gesture": self._summary(now, 12.0),
            "passage": {"start": self.segment_started, "state": current_passage,
                        "samples": len(self.segment)},
            "session": {"passages": len(self.passages), "extrema": self.extrema},
            "recurrence": recurrence,
        }
        return memory, events
