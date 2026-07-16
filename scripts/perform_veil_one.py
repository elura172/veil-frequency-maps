#!/usr/bin/env python3
"""Perform the six-minute Veil One evolution over AbletonOSC."""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402
from osc_mcp.gestures import GestureScheduler  # noqa: E402
from scripts.architecture_veil_one import set_opening_state  # noqa: E402
from scripts.build_veil_one import tcp_call  # noqa: E402
from scripts.veil_one import (  # noqa: E402
    AIR,
    CHORUSED_VOICES,
    FIFTHS,
    FLOOR,
    FOUNDATION,
    MEMORY,
    MEMORY_SENDS,
    PRESENCE,
    ROOM_SENDS,
    VOLUMES,
)


class Performance:
    def __init__(self):
        self.client = AbletonOSCClient()
        self.scheduler = GestureScheduler(self.emit)
        self.cancelled = False

    def emit(self, target, value):
        kind = target["type"]
        track = target.get("track_index")
        if kind == "track_volume":
            self.client.send_message("/live/track/set/volume", [track, max(0.0, min(1.0, value))])
        elif kind == "track_send":
            self.client.send_message("/live/track/set/send", [track, target["send_index"], max(0.0, min(1.0, value))])
        elif kind == "device_parameter":
            self.client.send_message(
                "/live/device/set/parameter/value",
                [track, target["device_index"], target["parameter_index"], value],
            )
        elif kind == "return_volume":
            tcp_call("set_return_track_volume", {
                "return_index": target["return_index"],
                "value": max(0.0, min(1.0, value)),
            })

    def ramp_group(self, tracks, start_values, end_values, start, duration, curve="golden"):
        ramps = []
        for position, track in enumerate(tracks):
            ramps.append({
                "target": {"type": "track_volume", "track_index": track},
                "from_value": start_values[position],
                "to_value": end_values[position],
                "curve": curve,
            })
        self.scheduler.schedule(ramps, duration, curve, 20, start, "veil_section")

    def send_group(self, tracks, send_index, start_values, end_values, start, duration, curve="golden"):
        ramps = []
        for position, track in enumerate(tracks):
            ramps.append({
                "target": {"type": "track_send", "track_index": track, "send_index": send_index},
                "from_value": start_values[position],
                "to_value": end_values[position],
                "curve": curve,
            })
        self.scheduler.schedule(ramps, duration, curve, 12, start, "veil_send")

    def parameter_group(self, tracks, device, parameter, start_values, end_values, start, duration, curve="golden"):
        ramps = []
        for position, track in enumerate(tracks):
            ramps.append({
                "target": {
                    "type": "device_parameter",
                    "track_index": track,
                    "device_index": device,
                    "parameter_index": parameter,
                },
                "from_value": start_values[position],
                "to_value": end_values[position],
                "curve": curve,
            })
        self.scheduler.schedule(ramps, duration, curve, 12, start, "veil_timbre")

    def build_score(self):
        # Threshold → Pillars: an open fifth grows out of the three-tone floor.
        self.ramp_group(FIFTHS, [FLOOR] * 3, [VOLUMES[t] for t in FIFTHS], 30, 65, "golden_in")

        # Pillars → Nave: perceptual midrange arrives; filters open with the gain.
        self.ramp_group(PRESENCE, [FLOOR] * 3, [VOLUMES[t] for t in PRESENCE], 70, 85, "golden")
        self.parameter_group(PRESENCE, 1, 1, [0.82] * 3, [0.91, 0.92, 0.93], 75, 80, "golden_in")

        # Nave → Memory: 9/8-related voices emerge, then acquire delayed memory.
        self.ramp_group(MEMORY, [FLOOR] * 4, [VOLUMES[t] for t in MEMORY], 125, 95, "golden_in")
        self.send_group(MEMORY, 1, [0.0] * 4, [MEMORY_SENDS[t] for t in MEMORY], 145, 75, "golden_out")

        # Memory → Air: the ceiling appears as the foundation yields a little energy.
        self.ramp_group(AIR, [FLOOR] * 3, [VOLUMES[t] for t in AIR], 175, 115, "golden")
        self.ramp_group(FOUNDATION, [VOLUMES[t] for t in FOUNDATION], [VOLUMES[t] * 0.76 for t in FOUNDATION], 210, 65, "golden_out")

        # Crown: room, filter openness, and chorus wetness rise within hard ceilings.
        upper = PRESENCE + MEMORY + AIR
        self.send_group(upper, 0, [ROOM_SENDS[t] for t in upper], [min(0.48, ROOM_SENDS[t] * 1.35) for t in upper], 255, 70, "golden_in")
        chorus_baseline = [0.10 + CHORUSED_VOICES.index(t) * 0.012 for t in CHORUSED_VOICES]
        chorus_crown = [min(0.22, value + 0.045) for value in chorus_baseline]
        self.parameter_group(CHORUSED_VOICES, 3, 15, chorus_baseline, chorus_crown, 260, 60, "golden_in")

        # Dissolution: all non-foundation material withdraws; every moving parameter returns.
        departing = FIFTHS + PRESENCE + MEMORY + AIR
        self.ramp_group(departing, [VOLUMES[t] for t in departing], [FLOOR] * len(departing), 300, 60, "golden_out")
        self.ramp_group(FOUNDATION, [VOLUMES[t] * 0.76 for t in FOUNDATION], [VOLUMES[t] for t in FOUNDATION], 315, 45, "golden_in")
        self.send_group(MEMORY, 1, [MEMORY_SENDS[t] for t in MEMORY], [0.0] * 4, 305, 55, "golden_out")
        self.send_group(upper, 0, [min(0.48, ROOM_SENDS[t] * 1.35) for t in upper], [ROOM_SENDS[t] for t in upper], 315, 45, "golden_out")
        self.parameter_group(CHORUSED_VOICES, 3, 15, chorus_crown, chorus_baseline, 315, 45, "golden_out")

    def run(self):
        set_opening_state(self.client)
        self.build_score()
        tcp_call("set_current_song_time", {"time": 0.0})
        tcp_call("start_playback")
        started = time.monotonic()
        try:
            while not self.cancelled:
                elapsed = time.monotonic() - started
                if elapsed >= 362:
                    break
                print(json.dumps({"elapsed_seconds": round(elapsed, 1), "active_gestures": len(self.scheduler.list())}), flush=True)
                time.sleep(15)
        finally:
            self.scheduler.cancel_all()
            tcp_call("stop_playback")
            set_opening_state(self.client)
            self.client.stop()


def main():
    performance = Performance()

    def stop(_signum, _frame):
        performance.cancelled = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    performance.run()


if __name__ == "__main__":
    main()
