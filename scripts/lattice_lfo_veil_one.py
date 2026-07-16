#!/usr/bin/env python3
"""Add frequency-lattice-derived panning and amplitude modulation to Veil One."""

from __future__ import annotations

import re
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402
from scripts.build_veil_one import tcp_call  # noqa: E402
from scripts.veil_one import (  # noqa: E402
    LFO_DIVISOR,
    PAN_DEPTH,
    TREM_DEPTH,
    VOICES,
    expected_names,
)

DEVICE_NAME = "Auto Pan-Tremolo"
DEVICE_URI = "query:AudioFx#Auto%20Pan-Tremolo"


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=2.0))


def device_names(client, track):
    return [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]


def parameter_map(client, track, device):
    values = query(client, "/live/device/get/parameters/name", [track, device])[2:]
    return {str(name): index for index, name in enumerate(values)}


def set_parameter(client, track, device, parameter, value):
    client.send_message(
        "/live/device/set/parameter/value",
        [track, device, parameter, float(value)],
    )
    time.sleep(0.02)


def display(client, track, device, parameter):
    return str(query(
        client,
        "/live/device/get/parameter/value_string",
        [track, device, parameter],
    )[-1])


def calibrate_frequency(client, track, device, parameter, target):
    low, high, best = 0.0, 1.0, None
    for _ in range(19):
        control = (low + high) / 2.0
        set_parameter(client, track, device, parameter, control)
        match = re.search(r"([0-9.]+)\s*Hz", display(client, track, device, parameter))
        if not match:
            raise RuntimeError("Cannot parse Auto Pan-Tremolo frequency display")
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


def ensure_pair(client, track):
    names = device_names(client, track)
    while names.count(DEVICE_NAME) < 2:
        tcp_call("load_browser_item", {"track_index": track, "item_uri": DEVICE_URI})
        time.sleep(0.35)
        names = device_names(client, track)
    if names.count(DEVICE_NAME) != 2:
        raise RuntimeError(f"Track {track + 1} has an unexpected Auto Pan-Tremolo count")
    indices = [index for index, name in enumerate(names) if name == DEVICE_NAME]
    return indices[0], indices[1]


def configure(client, track, device, mode, rate, amount, offset):
    params = parameter_map(client, track, device)
    rate_control, displayed_rate = calibrate_frequency(
        client, track, device, params["Frequency"], rate
    )
    set_parameter(client, track, device, params["Mode"], mode)
    set_parameter(client, track, device, params["Amount"], amount)
    set_parameter(client, track, device, params["Waveform"], 1)  # Triangle
    set_parameter(client, track, device, params["Time Mode"], 0)  # Free-running Hz
    set_parameter(client, track, device, params["Frequency"], rate_control)
    set_parameter(client, track, device, params["Phase"], 0.5 if mode == 0 else 0.0)
    set_parameter(client, track, device, params["Offset"], offset)
    set_parameter(client, track, device, params["Stereo Mode"], 0)
    set_parameter(client, track, device, params["Harmonic"], 0)
    set_parameter(client, track, device, params["Vintage"], 0)
    return displayed_rate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="first one-based voice")
    parser.add_argument("--end", type=int, default=16, help="last one-based voice")
    args = parser.parse_args()
    if not 1 <= args.start <= args.end <= 16:
        raise SystemExit("voice range must satisfy 1 <= start <= end <= 16")
    client = AbletonOSCClient()
    try:
        names = [str(v) for v in query(client, "/live/song/get/track_names")]
        if names[:16] != expected_names():
            raise RuntimeError("Veil One's voice field is not intact")

        for track in range(args.start - 1, args.end):
            frequency, _role = VOICES[track]
            pan_device, trem_device = ensure_pair(client, track)
            # Offsets are lattice-derived too: one 30-degree step per 36 Hz unit.
            offset = (((frequency / 36.0) * 30.0) % 360.0) / 360.0
            pan_rate = frequency / LFO_DIVISOR
            trem_rate = frequency / LFO_DIVISOR
            pan_display = configure(
                client, track, pan_device, 0, pan_rate, PAN_DEPTH[track], offset
            )
            trem_display = configure(
                client, track, trem_device, 1, trem_rate, TREM_DEPTH[track], offset
            )
            print(
                f"V{track + 1:02d} {frequency:g}Hz: "
                f"pan {pan_display:.3f}Hz/{PAN_DEPTH[track] * 100:.1f}% · "
                f"trem {trem_display:.3f}Hz/{TREM_DEPTH[track] * 100:.1f}%"
            )
    finally:
        client.stop()


if __name__ == "__main__":
    main()
