from __future__ import annotations

import math
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SILVER_RATIO = 1.0 + math.sqrt(2.0)
BRONZE_RATIO = (3.0 + math.sqrt(13.0)) / 2.0
GOLDEN_MINOR = 1.0 / (PHI * PHI)  # 0.381966...
GOLDEN_MAJOR = 1.0 / PHI          # 0.618034...


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def smoothstep(x: float) -> float:
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


def curve_value(name: str, x: float) -> float:
    """Return a normalized curve value for normalized time x."""
    x = clamp(x)
    curves = {
        "linear": lambda t: t,
        "ease_in": lambda t: t * t,
        "ease_out": lambda t: 1.0 - (1.0 - t) ** 2,
        "ease_in_out": smoothstep,
        "exponential": lambda t: 0.0 if t == 0.0 else (math.exp(4.0 * t) - 1.0) / (math.exp(4.0) - 1.0),
        "logarithmic": lambda t: math.log1p(20.0 * t) / math.log(21.0),
        "sine": lambda t: 0.5 - 0.5 * math.cos(math.pi * t),
        "golden_in": lambda t: t ** PHI,
        "golden_out": lambda t: 1.0 - (1.0 - t) ** PHI,
        "silver_in": lambda t: t ** SILVER_RATIO,
        "silver_out": lambda t: 1.0 - (1.0 - t) ** SILVER_RATIO,
        "bronze_in": lambda t: t ** BRONZE_RATIO,
        "bronze_out": lambda t: 1.0 - (1.0 - t) ** BRONZE_RATIO,
        # A monotonic two-stage curve whose structural hinge is phi^-1.
        "golden": lambda t: (
            GOLDEN_MINOR * smoothstep(t / GOLDEN_MAJOR)
            if t <= GOLDEN_MAJOR
            else GOLDEN_MINOR + GOLDEN_MAJOR * smoothstep((t - GOLDEN_MAJOR) / GOLDEN_MINOR)
        ),
        "fibonacci_steps": lambda t: max(v for v in (0.0, 0.125, 0.2, 0.333333, 0.5, GOLDEN_MAJOR, 0.8, 1.0) if v <= t),
    }
    if name not in curves:
        raise ValueError("Unknown curve: %s" % name)
    return clamp(curves[name](x))


def shaped_value(start: float, end: float, progress: float, curve: str, domain: str) -> float:
    amount = curve_value(curve, progress)
    if domain == "linear" or start == end:
        return start + (end - start) * amount
    if domain == "log":
        if start <= 0 or end <= 0:
            raise ValueError("Log interpolation requires positive endpoints")
        return math.exp(math.log(start) + (math.log(end) - math.log(start)) * amount)
    if domain == "db":
        # Endpoints are dB. Return linear amplitude for Live's normalized controls.
        db_value = start + (end - start) * amount
        return 10.0 ** (db_value / 20.0)
    raise ValueError("Unknown interpolation domain: %s" % domain)


def arch_value(progress: float, peak_at: float = GOLDEN_MAJOR, inverse: bool = False) -> float:
    progress, peak_at = clamp(progress), clamp(peak_at, 0.001, 0.999)
    if progress <= peak_at:
        value = smoothstep(progress / peak_at)
    else:
        value = 1.0 - smoothstep((progress - peak_at) / (1.0 - peak_at))
    return 1.0 - value if inverse else value


@dataclass
class Gesture:
    id: str
    kind: str
    state: str = "scheduled"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def public(self) -> dict[str, Any]:
        return {key: value for key, value in {
            "id": self.id, "kind": self.kind, "state": self.state,
            "created_at": self.created_at, "started_at": self.started_at,
            "finished_at": self.finished_at, "error": self.error,
        }.items() if value is not None}


class GestureScheduler:
    def __init__(self, emit: Callable[[dict[str, Any], float], None]):
        self.emit = emit
        self._gestures: dict[str, Gesture] = {}
        self._lock = threading.RLock()

    def schedule(self, ramps: list[dict[str, Any]], duration: float, curve: str = "linear",
                 rate_hz: float = 20.0, delay: float = 0.0, kind: str = "batch_ramp") -> dict[str, Any]:
        if not ramps:
            raise ValueError("At least one ramp is required")
        if duration <= 0:
            raise ValueError("Duration must be positive")
        rate_hz = clamp(float(rate_hz), 1.0, 30.0)
        # Validate before the worker is launched.
        curve_value(curve, 0.5)
        for ramp in ramps:
            shaped_value(float(ramp["from_value"]), float(ramp["to_value"]), 0.5,
                         ramp.get("curve", curve), ramp.get("domain", "linear"))
        gesture = Gesture(str(uuid.uuid4()), kind)
        with self._lock:
            self._gestures[gesture.id] = gesture
        thread = threading.Thread(
            target=self._run, args=(gesture, ramps, float(duration), curve, rate_hz, max(0.0, float(delay))),
            name="ableton-gesture-" + gesture.id[:8], daemon=True,
        )
        thread.start()
        return gesture.public()

    def _run(self, gesture: Gesture, ramps: list[dict[str, Any]], duration: float,
             default_curve: str, rate_hz: float, delay: float) -> None:
        try:
            if gesture.cancel_event.wait(delay):
                gesture.state = "cancelled"
                return
            gesture.state, gesture.started_at = "running", time.time()
            interval, started = 1.0 / rate_hz, time.monotonic()
            while True:
                progress = clamp((time.monotonic() - started) / duration)
                for ramp in ramps:
                    value = shaped_value(
                        float(ramp["from_value"]), float(ramp["to_value"]), progress,
                        ramp.get("curve", default_curve), ramp.get("domain", "linear"),
                    )
                    self.emit(ramp["target"], value)
                if progress >= 1.0:
                    gesture.state = "completed"
                    return
                if gesture.cancel_event.wait(interval):
                    gesture.state = "cancelled"
                    return
        except Exception as exc:
            gesture.state, gesture.error = "failed", str(exc)
        finally:
            gesture.finished_at = time.time()

    def cancel(self, gesture_id: str) -> dict[str, Any]:
        with self._lock:
            gesture = self._gestures.get(gesture_id)
        if gesture is None:
            raise ValueError("Unknown gesture: %s" % gesture_id)
        gesture.cancel_event.set()
        return gesture.public()

    def cancel_all(self) -> list[dict[str, Any]]:
        with self._lock:
            active = [g for g in self._gestures.values() if g.state in ("scheduled", "running")]
        for gesture in active:
            gesture.cancel_event.set()
        return [g.public() for g in active]

    def list(self, include_finished: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            gestures = list(self._gestures.values())
        if not include_finished:
            gestures = [g for g in gestures if g.state in ("scheduled", "running")]
        return [g.public() for g in gestures]
