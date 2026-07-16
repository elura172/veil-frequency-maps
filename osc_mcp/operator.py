"""Dynamic, version-tolerant access to Ableton Operator parameters."""

from __future__ import annotations

from .wavetable import normalize_parameter_name


def parameter_inventory(bridge, track_index: int, device_index: int) -> dict:
    prefix = [track_index, device_index]
    class_reply = bridge.query("/live/device/get/class_name", prefix)
    class_name = str(class_reply[-1])
    if normalize_parameter_name(class_name).replace(" ", "") != "operator":
        raise ValueError(
            "Device %d on track %d is %r, not Operator"
            % (device_index, track_index, class_name)
        )

    def payload(path):
        return list(bridge.query(path, prefix)[2:])

    names = payload("/live/device/get/parameters/name")
    values = payload("/live/device/get/parameters/value")
    minimums = payload("/live/device/get/parameters/min")
    maximums = payload("/live/device/get/parameters/max")
    quantized = payload("/live/device/get/parameters/is_quantized")
    return {
        "track_index": track_index,
        "device_index": device_index,
        "class_name": class_name,
        "parameters": [
            {
                "index": index,
                "name": str(name),
                "key": normalize_parameter_name(str(name)),
                "value": values[index],
                "min": minimums[index],
                "max": maximums[index],
                "is_quantized": bool(quantized[index]),
            }
            for index, name in enumerate(names)
        ],
    }
