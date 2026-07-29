#!/usr/bin/env python3
"""Shape the room: Radiant Mirror's reverb on return A.

Requires the return-track endpoints added by
integrations/abletonosc/return-tracks.patch. Idempotent, and verifies every
calibrated value against Live's own display before reporting success.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402

from projects.radiant_mirror.spec import (  # noqa: E402
    ROOM_CHORUS_ON,
    ROOM_DECAY_SECONDS,
    ROOM_DEVICE,
    ROOM_DIFFUSION_PERCENT,
    ROOM_DRY_WET,
    ROOM_FREEZE_ON,
    ROOM_HIGH_SHELF_GAIN,
    ROOM_HIGH_SHELF_HZ,
    ROOM_INPUT_FREQ_HZ,
    ROOM_PREDELAY_MS,
    ROOM_RETURN_INDEX,
    ROOM_RETURN_NAME,
    ROOM_SCALE_PERCENT,
    ROOM_SIZE,
    ROOM_STEREO_IMAGE,
    ROOM_TOLERANCE,
)

RETURN = ROOM_RETURN_INDEX
DEVICE = 0

UNITS = {"ms": 0.001, "s": 1.0, "hz": 1.0, "khz": 1000.0, "%": 1.0, "": 1.0}


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=3.0))


def require_endpoints(client):
    try:
        query(client, "/live/song/get/num_return_tracks")
    except RuntimeError:
        raise SystemExit(
            "AbletonOSC has no return-track endpoints. Apply "
            "integrations/abletonosc/return-tracks.patch and send /live/api/reload."
        )


def parameter_map(client):
    names = query(client, "/live/return/get/device/parameters/name", [RETURN, DEVICE])[2:]
    return {str(name): index for index, name in enumerate(names)}


def value_string(client, parameter):
    return str(query(
        client, "/live/return/get/device/parameter/value_string",
        [RETURN, DEVICE, parameter],
    )[-1])


def set_parameter(client, parameter, value):
    client.send_message(
        "/live/return/set/device/parameter/value",
        [RETURN, DEVICE, parameter, float(value)],
    )
    time.sleep(0.04)


def displayed_number(client, parameter, unit):
    """Read Live's display back in the requested unit."""
    text = value_string(client, parameter).strip().replace(",", "")
    match = re.search(r"(-?[0-9.]+)\s*(ms|s|kHz|Hz|%)?", text, re.IGNORECASE)
    if not match:
        raise RuntimeError("Cannot parse reverb display: %r" % text)
    value = float(match.group(1))
    seen = (match.group(2) or "").lower()
    return value * UNITS.get(seen, 1.0) / UNITS[unit.lower()]


def calibrate(client, parameter, target, unit):
    low, high, best = 0.0, 1.0, None
    for _ in range(24):
        control = (low + high) / 2.0
        set_parameter(client, parameter, control)
        actual = displayed_number(client, parameter, unit)
        if best is None or abs(actual - target) < abs(best[1] - target):
            best = (control, actual)
        if actual < target:
            low = control
        elif actual > target:
            high = control
        else:
            break
    set_parameter(client, parameter, best[0])
    return best[1]


def shape(client):
    params = parameter_map(client)
    required = ["Predelay", "Decay Time", "Diffusion", "Scale", "Input Freq",
                "Diff. Hi Freq", "HiShelf Gain", "Stereo Image", "Chorus On",
                "Freeze On", "Dry/Wet", "Density", "Room Size"]
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError("%s parameter map changed; missing %s" % (ROOM_DEVICE, missing))

    # Switched settings first, so the calibrations below are measured in the
    # room the field will actually hear.
    set_parameter(client, params["Chorus On"], ROOM_CHORUS_ON)
    set_parameter(client, params["Freeze On"], ROOM_FREEZE_ON)
    set_parameter(client, params["Dry/Wet"], ROOM_DRY_WET)
    set_parameter(client, params["Stereo Image"], ROOM_STEREO_IMAGE)
    set_parameter(client, params["HiShelf Gain"], ROOM_HIGH_SHELF_GAIN)
    set_parameter(client, params["Room Size"], ROOM_SIZE)

    calibrated = [
        ("predelay_ms", params["Predelay"], ROOM_PREDELAY_MS, "ms"),
        ("decay_seconds", params["Decay Time"], ROOM_DECAY_SECONDS, "s"),
        ("diffusion_percent", params["Diffusion"], ROOM_DIFFUSION_PERCENT, "%"),
        ("scale_percent", params["Scale"], ROOM_SCALE_PERCENT, "%"),
        ("input_freq_hz", params["Input Freq"], ROOM_INPUT_FREQ_HZ, "Hz"),
        ("high_shelf_hz", params["Diff. Hi Freq"], ROOM_HIGH_SHELF_HZ, "Hz"),
    ]
    result = {}
    failures = []
    for key, parameter, target, unit in calibrated:
        actual = calibrate(client, parameter, target, unit)
        result[key] = actual
        if abs(actual - target) > max(1e-6, abs(target) * ROOM_TOLERANCE):
            failures.append("%s is %g %s, expected %g %s" % (key, actual, unit, target, unit))

    result["chorus"] = value_string(client, params["Chorus On"])
    result["dry_wet"] = value_string(client, params["Dry/Wet"])
    result["stereo_image"] = value_string(client, params["Stereo Image"])
    result["room_size"] = value_string(client, params["Room Size"])
    result["density"] = value_string(client, params["Density"])
    if failures:
        raise RuntimeError("Room did not settle: %s" % "; ".join(failures))
    return result


def main():
    client = AbletonOSCClient()
    try:
        require_endpoints(client)
        names = [str(v) for v in query(client, "/live/song/get/return_track_names")]
        if not names:
            raise SystemExit("This Set has no return tracks")
        if names[RETURN] != ROOM_RETURN_NAME:
            raise SystemExit("Return %d is %r, expected %r" % (RETURN, names[RETURN], ROOM_RETURN_NAME))
        devices = [str(v) for v in query(client, "/live/return/get/devices/name", [RETURN])[1:]]
        if not devices or devices[0] != ROOM_DEVICE:
            raise SystemExit("Return %d carries %s, expected %s first" % (RETURN, devices, ROOM_DEVICE))
        print(json.dumps({
            "status": "shaped",
            "return": RETURN,
            "return_name": names[RETURN],
            "device": devices[0],
            "room": shape(client),
        }, indent=2, ensure_ascii=False))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
