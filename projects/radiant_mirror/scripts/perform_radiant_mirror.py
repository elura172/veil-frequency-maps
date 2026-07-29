#!/usr/bin/env python3
"""Conduct the wanderer: glide the theremin between the twelve reflections.

Operator's fixed-frequency control is logarithmic, so interpolating it directly
is a constant-cents portamento. Each transition is one gesture carrying both the
pitch and the volume hand, shaped by a metallic curve.

One pass is exactly one form. The field itself is left alone.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from osc_mcp.server import Server  # noqa: E402

from projects.radiant_mirror.spec import (  # noqa: E402
    THEREMIN_CHAIN,
    THEREMIN_NAME,
    THEREMIN_PATH,
    THEREMIN_STEPS,
    VOICES,
    expected_names,
    theremin_levels,
    theremin_form_seconds,
)

FIX_FREQ = "A Fix Freq"


def fixed_frequency_control(hertz):
    """Operator's Fixed Frequency control is logarithmic over 10-2000 Hz."""
    return math.log(hertz / 10.0) / math.log(200.0)


def locate(server):
    names = [str(v) for v in server.call_tool(
        "ableton_osc_query", {"address": "/live/song/get/track_names"})["values"]]
    if names[:len(VOICES)] != expected_names():
        raise RuntimeError("Radiant Mirror's voice field is not intact")
    if THEREMIN_NAME not in names:
        raise RuntimeError("The wanderer is not built; run theremin_radiant_mirror.py first")
    track = names.index(THEREMIN_NAME)
    devices = [str(v) for v in server.call_tool(
        "ableton_osc_query",
        {"address": "/live/track/get/devices/name", "params": [track]})["values"][1:]]
    if devices[:len(THEREMIN_CHAIN)] != THEREMIN_CHAIN:
        raise RuntimeError("The wanderer's chain is not intact: %s" % devices)
    inspected = server.call_tool("ableton_inspect_operator",
                                 {"track_index": track, "device_index": 0})
    parameters = {entry["name"]: entry["index"] for entry in inspected["parameters"]}
    if FIX_FREQ not in parameters:
        raise RuntimeError("Operator no longer exposes %r" % FIX_FREQ)
    return track, parameters[FIX_FREQ]


def wander(server, track, fix_freq_index, passes, settle):
    levels = theremin_levels()
    waypoints = [VOICES[voice][0] for voice in THEREMIN_PATH]
    controls = [fixed_frequency_control(hertz) for hertz in waypoints]
    count = len(THEREMIN_PATH)

    for pass_index in range(passes):
        for step, (glide, dwell, curve) in enumerate(THEREMIN_STEPS):
            here, there = step, (step + 1) % count
            server.call_tool("ableton_batch_ramp", {
                "ramps": [
                    {
                        "target": {"type": "device_parameter", "track_index": track,
                                   "device_index": 0, "parameter_index": fix_freq_index},
                        "from_value": controls[here], "to_value": controls[there],
                        "curve": curve,
                    },
                    {
                        "target": {"type": "track_volume", "track_index": track},
                        "from_value": levels[here], "to_value": levels[there],
                        "curve": curve,
                    },
                ],
                "duration": glide,
                "curve": curve,
                "rate_hz": 30,
            })
            print(
                "pass %d/%d  step %2d/%d  %7gHz -> %7gHz  glide %4.0fs %-12s dwell %2.0fs"
                % (pass_index + 1, passes, step + 1, count,
                   waypoints[here], waypoints[there], glide, curve, dwell),
                flush=True,
            )
            time.sleep(glide + dwell)
    if settle:
        time.sleep(settle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--passes", type=int, default=1, help="complete circuits of the mirror")
    parser.add_argument("--fire", action="store_true",
                        help="launch the wanderer's clip before conducting")
    parser.add_argument("--stop-when-done", action="store_true",
                        help="stop the wanderer's clip at the end, leaving the field sounding")
    args = parser.parse_args()
    if args.passes < 1:
        raise SystemExit("passes must be at least 1")

    server = Server()
    track, fix_freq_index = locate(server)
    print("wanderer on track %d, %r at parameter %d; one pass is %.0f s"
          % (track, FIX_FREQ, fix_freq_index, theremin_form_seconds()), flush=True)
    try:
        if args.fire:
            server.call_tool("ableton_osc_send",
                             {"address": "/live/clip_slot/fire", "params": [track, 0]})
            time.sleep(0.2)
        wander(server, track, fix_freq_index, args.passes, settle=0.0)
    except KeyboardInterrupt:
        print("interrupted; cancelling gestures", flush=True)
    finally:
        server.call_tool("ableton_cancel_all_gestures", {})
        if args.stop_when_done:
            server.call_tool("ableton_osc_send",
                             {"address": "/live/clip_slot/stop", "params": [track, 0]})


if __name__ == "__main__":
    main()
