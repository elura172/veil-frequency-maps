"""Dynamic, version-tolerant access to Ableton Wavetable parameters."""

from __future__ import annotations

import re


def normalize_parameter_name(value: str) -> str:
    """Normalize Live's display names without guessing parameter indices."""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def parameter_inventory(bridge, track_index: int, device_index: int) -> dict:
    prefix = [track_index, device_index]
    class_reply = bridge.query("/live/device/get/class_name", prefix)
    class_name = str(class_reply[-1])
    normalized_class = normalize_parameter_name(class_name).replace(" ", "")
    if normalized_class not in {"wavetable", "instrumentvector"}:
        raise ValueError(
            "Device %d on track %d is %r, not Wavetable"
            % (device_index, track_index, class_name)
        )

    def payload(path):
        reply = bridge.query(path, prefix)
        return list(reply[2:])

    names = payload("/live/device/get/parameters/name")
    values = payload("/live/device/get/parameters/value")
    minimums = payload("/live/device/get/parameters/min")
    maximums = payload("/live/device/get/parameters/max")
    quantized = payload("/live/device/get/parameters/is_quantized")
    parameters = []
    for index, name in enumerate(names):
        parameters.append({
            "index": index,
            "name": str(name),
            "key": normalize_parameter_name(str(name)),
            "value": values[index],
            "min": minimums[index],
            "max": maximums[index],
            "is_quantized": bool(quantized[index]),
        })
    return {
        "track_index": track_index,
        "device_index": device_index,
        "class_name": class_name,
        "parameters": parameters,
    }


def resolve_parameter(inventory: dict, requested_name: str) -> dict:
    key = normalize_parameter_name(requested_name)
    exact = [p for p in inventory["parameters"] if p["key"] == key]
    if len(exact) == 1:
        return exact[0]
    requested_tokens = set(key.split())
    partial = [
        p for p in inventory["parameters"]
        if requested_tokens and requested_tokens.issubset(set(p["key"].split()))
    ]
    if len(partial) == 1:
        return partial[0]
    if not exact and not partial:
        raise ValueError("No Wavetable parameter matches %r" % requested_name)
    matches = exact or partial
    raise ValueError(
        "Ambiguous Wavetable parameter %r; matches: %s"
        % (requested_name, ", ".join(p["name"] for p in matches))
    )


def checked_value(parameter: dict, value: float) -> float:
    value = float(value)
    if value < float(parameter["min"]) or value > float(parameter["max"]):
        raise ValueError(
            "%s must be between %s and %s"
            % (parameter["name"], parameter["min"], parameter["max"])
        )
    if parameter["is_quantized"]:
        value = float(round(value))
    return value
