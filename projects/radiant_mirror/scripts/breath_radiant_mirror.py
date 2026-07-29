#!/usr/bin/env python3
"""Give Radiant Mirror its breath: paired, phase-opposed amplitude modulation.

Each voice gets one Auto Pan-Tremolo in tremolo mode. The two leaves of a pair
share a period and sit half a cycle apart, so the pair see-saws about the pivot.
Idempotent: re-running reconfigures the existing devices rather than stacking.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402

from projects.radiant_mirror.scripts.build_radiant_mirror import (  # noqa: E402
    device_names,
    query,
    tcp_call,
)
from projects.radiant_mirror.spec import (  # noqa: E402
    AM_DEPTHS,
    AM_DEVICE,
    AM_DEVICE_URI,
    AM_MODE_TREMOLO,
    AM_OFFSETS,
    AM_PERIOD_TOLERANCE,
    AM_PERIODS,
    AM_TIME_MODE_FREE,
    AM_WAVEFORM_SINE,
    LOWER_LEAF,
    UPPER_LEAF,
    VOICES,
    expected_names,
)

TIME_MODE_PARAM = "Time Mode"
PERIOD_PARAM = "Time"
AMOUNT_PARAM = "Amount"


def parameter_map(client, track, device):
    names = query(client, "/live/device/get/parameters/name", [track, device])[2:]
    return {str(name): index for index, name in enumerate(names)}


def set_parameter(client, track, device, parameter, value):
    client.send_message(
        "/live/device/set/parameter/value",
        [track, device, parameter, float(value)],
    )
    time.sleep(0.03)


def value_string(client, track, device, parameter):
    return str(query(
        client, "/live/device/get/parameter/value_string",
        [track, device, parameter],
    )[-1])


def displayed_period(client, track, device, parameter):
    """Read Live's free-mode period display back as seconds."""
    text = value_string(client, track, device, parameter).strip().lower()
    match = re.search(r"([0-9.]+)\s*(ms|s)\b", text)
    if not match:
        raise RuntimeError("Cannot parse Auto Pan-Tremolo period: %s" % text)
    value = float(match.group(1))
    return value / 1000.0 if match.group(2) == "ms" else value


def calibrate_period(client, track, device, parameter, target):
    """Binary-search the normalised control for a displayed period in seconds."""
    low, high, best = 0.0, 1.0, None
    for _ in range(22):
        control = (low + high) / 2.0
        set_parameter(client, track, device, parameter, control)
        actual = displayed_period(client, track, device, parameter)
        if best is None or abs(actual - target) < abs(best[1] - target):
            best = (control, actual)
        if actual < target:
            low = control
        elif actual > target:
            high = control
        else:
            break
    return best


def ensure_device(client, track):
    """Return the index of this track's single Auto Pan-Tremolo, loading it silent."""
    names = device_names(client, track)
    count = names.count(AM_DEVICE)
    if count > 1:
        raise RuntimeError("Track %d already carries %d %s devices" % (track, count, AM_DEVICE))
    if count == 0:
        tcp_call("load_browser_item", {"track_index": track, "item_uri": AM_DEVICE_URI})
        time.sleep(0.4)
        names = device_names(client, track)
        if names.count(AM_DEVICE) != 1:
            raise RuntimeError("%s did not load on track %d" % (AM_DEVICE, track))
        # Live loads it at full depth and 1 Hz. Silence the modulation before
        # anything else so a sounding field is not jolted mid-build.
        index = names.index(AM_DEVICE)
        params = parameter_map(client, track, index)
        set_parameter(client, track, index, params[AMOUNT_PARAM], 0.0)
    return names.index(AM_DEVICE)


def breathe(client, track, pair):
    device = ensure_device(client, track)
    params = parameter_map(client, track, device)
    required = ["Mode", "Amount", "Waveform", "Invert", TIME_MODE_PARAM,
                PERIOD_PARAM, "Phase", "Offset", "Stereo Mode", "Harmonic", "Vintage"]
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError("%s parameter map changed; missing %s" % (AM_DEVICE, missing))

    set_parameter(client, track, device, params[AMOUNT_PARAM], 0.0)
    set_parameter(client, track, device, params["Mode"], AM_MODE_TREMOLO)
    set_parameter(client, track, device, params[TIME_MODE_PARAM], AM_TIME_MODE_FREE)
    set_parameter(client, track, device, params["Waveform"], AM_WAVEFORM_SINE)
    set_parameter(client, track, device, params["Invert"], 0)
    # Tremolo phase is the offset between channels. Zero keeps both moving
    # together, so this is amplitude modulation and not a stereo wobble.
    set_parameter(client, track, device, params["Phase"], 0.0)
    set_parameter(client, track, device, params["Stereo Mode"], 0)
    set_parameter(client, track, device, params["Harmonic"], 0)
    set_parameter(client, track, device, params["Vintage"], 0)

    control, displayed = calibrate_period(
        client, track, device, params[PERIOD_PARAM], AM_PERIODS[pair]
    )
    set_parameter(client, track, device, params[PERIOD_PARAM], control)
    set_parameter(client, track, device, params["Offset"], AM_OFFSETS[track])
    set_parameter(client, track, device, params[AMOUNT_PARAM], AM_DEPTHS[track])

    target = AM_PERIODS[pair]
    if abs(displayed - target) > max(0.05, target * AM_PERIOD_TOLERANCE):
        raise RuntimeError(
            "Track %d period is %.3f s, expected %.3f s" % (track, displayed, target)
        )
    return {
        "track": track,
        "device_index": device,
        "period_seconds": displayed,
        "depth": AM_DEPTHS[track],
        "offset_degrees": AM_OFFSETS[track] * 360.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="first one-based voice")
    parser.add_argument("--end", type=int, default=len(VOICES), help="last one-based voice")
    args = parser.parse_args()
    if not 1 <= args.start <= args.end <= len(VOICES):
        raise SystemExit("voice range must satisfy 1 <= start <= end <= %d" % len(VOICES))

    pair_of = {}
    for pair, (lower, upper) in enumerate(zip(LOWER_LEAF, UPPER_LEAF)):
        pair_of[lower] = pair
        pair_of[upper] = pair

    client = AbletonOSCClient()
    try:
        if [str(v) for v in query(client, "/live/song/get/track_names")][:len(VOICES)] != expected_names():
            raise RuntimeError("Radiant Mirror's voice field is not intact")
        for track in range(args.start - 1, args.end):
            result = breathe(client, track, pair_of[track])
            frequency, role = VOICES[track]
            print(
                "R%02d %7gHz %-14s breath %6.2f s · depth %4.1f%% · offset %3.0f°"
                % (track + 1, frequency, role, result["period_seconds"],
                   result["depth"] * 100.0, result["offset_degrees"])
            )
    finally:
        client.stop()


if __name__ == "__main__":
    main()
