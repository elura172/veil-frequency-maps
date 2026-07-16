#!/usr/bin/env python3
"""Apply Veil One's restrained timbral-motion layer idempotently."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402
from scripts.build_veil_one import tcp_call  # noqa: E402
from scripts.veil_one import (  # noqa: E402
    CHORUSED_VOICES,
    DRIFT_VOICES,
    SATURATED_VOICES,
    TRIANGLE_VOICES,
    expected_names,
)


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=2.0))


def devices(client, track):
    return [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]


def parameter_map(client, track, device):
    names = query(client, "/live/device/get/parameters/name", [track, device])[2:]
    return {str(name): index for index, name in enumerate(names)}


def set_parameter(client, track, device, parameter, value):
    client.send_message(
        "/live/device/set/parameter/value",
        [track, device, parameter, float(value)],
    )
    time.sleep(0.025)


def value_string(client, track, device, parameter):
    return str(query(
        client,
        "/live/device/get/parameter/value_string",
        [track, device, parameter],
    )[-1])


def calibrate_display(client, track, device, parameter, target, pattern):
    """Find a normalized control value whose displayed number is near target."""
    low, high, best = 0.0, 1.0, None
    for _ in range(18):
        control = (low + high) / 2.0
        set_parameter(client, track, device, parameter, control)
        match = re.search(pattern, value_string(client, track, device, parameter))
        if not match:
            raise RuntimeError("Cannot parse parameter display")
        actual = float(match.group(1))
        if best is None or abs(actual - target) < abs(best[1] - target):
            best = (control, actual)
        if actual < target:
            low = control
        elif actual > target:
            high = control
        else:
            break
    return best


def ensure_effect(client, track, name, uri):
    current = devices(client, track)
    if name not in current:
        tcp_call("load_browser_item", {"track_index": track, "item_uri": uri})
        time.sleep(0.35)
        current = devices(client, track)
    if name not in current:
        raise RuntimeError(f"{name} failed to load on track {track + 1}")
    return current.index(name)


def main():
    client = AbletonOSCClient()
    try:
        names = [str(v) for v in query(client, "/live/song/get/track_names")]
        if names[:16] != expected_names():
            raise RuntimeError("Veil One's 16 voice tracks are not intact")

        # Triangle is reserved for the body/memory threshold; foundations remain sine.
        op = parameter_map(client, 0, 0)
        for track in TRIANGLE_VOICES:
            set_parameter(client, track, 0, op["Osc-A Wave"], 19)

        # Auto Filter's triangle LFO creates extremely shallow, unsynchronised breathing.
        af = parameter_map(client, 0, 1)
        drift_rates = [0.031, 0.037, 0.043, 0.053, 0.061, 0.071, 0.079, 0.089, 0.097]
        drift_depths = [1.0, 1.15, 1.3, 1.45, 1.6, 1.8, 2.0, 2.2, 2.5]
        rate_controls = {}
        for target in drift_rates:
            rate_controls[target] = calibrate_display(
                client, 0, 1, af["LFO Freq"], target, r"([0-9.]+)\s*Hz"
            )[0]
        set_parameter(client, 0, 1, af["LFO Amount"], 0)
        for track, rate, depth in zip(DRIFT_VOICES, drift_rates, drift_depths):
            set_parameter(client, track, 1, af["LFO Wave"], 1)
            set_parameter(client, track, 1, af["LFO Freq"], rate_controls[rate])
            depth_control = calibrate_display(
                client, track, 1, af["LFO Amount"], depth, r"(-?[0-9.]+)\s*%"
            )[0]
            set_parameter(client, track, 1, af["LFO Amount"], depth_control)
            set_parameter(client, track, 1, af["LFO Phase"], (track * 0.137) % 1.0)
            set_parameter(client, track, 1, af["LFO Smoothing"], 0.32)

        # Body-only saturation: low drive, parallel blend, no hard clipping.
        for position, track in enumerate(SATURATED_VOICES):
            device = ensure_effect(client, track, "Saturator", "query:AudioFx#Saturator")
            params = parameter_map(client, track, device)
            drive = calibrate_display(
                client, track, device, params["Drive"], 0.7 + 0.15 * position, r"(-?[0-9.]+)\s*dB"
            )[0]
            set_parameter(client, track, device, params["Drive"], drive)
            set_parameter(client, track, device, params["Color On"], 0)
            set_parameter(client, track, device, params["Post Clip Mode"], 0)
            set_parameter(client, track, device, params["Dry/Wet"], 0.20 + 0.025 * position)

        # Air and memory receive phase-offset chorus; feedback stays almost absent.
        chorus_rates = [0.047, 0.059, 0.067, 0.073, 0.083, 0.091, 0.103]
        for position, (track, target_rate) in enumerate(zip(CHORUSED_VOICES, chorus_rates)):
            device = ensure_effect(client, track, "Chorus-Ensemble", "query:AudioFx#Chorus-Ensemble")
            params = parameter_map(client, track, device)
            rate = calibrate_display(
                client, track, device, params["Rate"], target_rate, r"([0-9.]+)\s*Hz"
            )[0]
            set_parameter(client, track, device, params["Mode"], 0)
            set_parameter(client, track, device, params["Shape"], 0.22 + position * 0.09)
            set_parameter(client, track, device, params["Rate"], rate)
            set_parameter(client, track, device, params["Amount"], 0.16 + position * 0.012)
            set_parameter(client, track, device, params["Feedback"], 0.015 + position * 0.004)
            set_parameter(client, track, device, params["Width"], 0.55 + position * 0.035)
            set_parameter(client, track, device, params["Warmth"], 0.12)
            set_parameter(client, track, device, params["Dry/Wet"], 0.10 + position * 0.012)

        print("Veil One texture layer applied and bounded.")
        for track in range(16):
            print(f"{track + 1:02d}: {' -> '.join(devices(client, track))}")
    finally:
        client.stop()


if __name__ == "__main__":
    main()
