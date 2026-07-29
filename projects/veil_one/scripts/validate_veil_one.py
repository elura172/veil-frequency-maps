#!/usr/bin/env python3
"""Read-only structural validator for the finished Veil One Live Set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402
from projects.veil_one.scripts.build_veil_one import tcp_call  # noqa: E402
from projects.veil_one.spec import (  # noqa: E402
    CHORUSED_VOICES,
    LENGTH_BEATS,
    LENGTH_SECONDS,
    SATURATED_VOICES,
    TEMPO,
    TRIANGLE_VOICES,
    VOICES,
    expected_names,
)


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=2.0))


def display(client, track, device, parameter):
    return str(query(client, "/live/device/get/parameter/value_string", [track, device, parameter])[-1])


def main():
    errors = []
    client = AbletonOSCClient()
    try:
        session = tcp_call("get_session_info")
        if session["is_playing"]:
            errors.append("transport is playing")
        if abs(float(session["current_song_time"])) > 0.01:
            errors.append("playhead is not at beat zero")
        if abs(float(session["tempo"]) - TEMPO) > 0.001:
            errors.append(f"tempo is not {TEMPO:g} BPM")
        if int(session["return_track_count"]) != 2:
            errors.append("expected exactly two return buses")

        names = [str(v) for v in query(client, "/live/song/get/track_names")]
        if names[:16] != expected_names():
            errors.append("voice names/order changed")

        for track, (frequency, _role) in enumerate(VOICES):
            chain = [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]
            expected = ["Operator", "Auto Filter", "Utility"]
            if track in SATURATED_VOICES:
                expected.append("Saturator")
            if track in CHORUSED_VOICES:
                expected.append("Chorus-Ensemble")
            expected.extend(["Auto Pan-Tremolo", "Auto Pan-Tremolo"])
            if chain != expected:
                errors.append(f"track {track + 1} chain is {chain}, expected {expected}")

            wave = display(client, track, 0, 25)
            wanted_wave = "Triangle" if track in TRIANGLE_VOICES else "Sine"
            if wave != wanted_wave:
                errors.append(f"track {track + 1} waveform is {wave}, expected {wanted_wave}")

            pan_device, trem_device = len(chain) - 2, len(chain) - 1
            if display(client, track, pan_device, 1) != "Panning":
                errors.append(f"track {track + 1} lattice pan device is not in Panning mode")
            if display(client, track, trem_device, 1) != "Tremolo":
                errors.append(f"track {track + 1} lattice amplitude device is not in Tremolo mode")
            if display(client, track, pan_device, 3) != "Triangle" or display(client, track, trem_device, 3) != "Triangle":
                errors.append(f"track {track + 1} lattice LFO waveform is not Triangle")

            arrangement = tcp_call("get_arrangement_clips", {"track_index": track})
            if arrangement["clip_count"] != 1:
                errors.append(f"track {track + 1} does not have one Arrangement clip")
            else:
                clip = arrangement["clips"][0]
                if abs(float(clip["start_time"])) > 0.001 or abs(float(clip["length"]) - LENGTH_BEATS) > 0.01:
                    errors.append(f"track {track + 1} Arrangement span is invalid")

            # Operator's display intentionally rounds kHz voices to two decimals.
            fixed = display(client, track, 0, 18)
            if not fixed:
                errors.append(f"track {track + 1} has no fixed-frequency display for {frequency} Hz")

        host = PROJECT_ROOT / "max_for_live" / "Veil Modulator" / "Veil Modulator.amxd"
        if not host.is_file() or host.read_bytes()[:4] != b"ampf":
            errors.append("Veil Modulator.amxd is missing or invalid")

        result = {
            "status": "healthy" if not errors else "invalid",
            "voice_count": 16,
            "arrangement_beats": LENGTH_BEATS,
            "duration_seconds": LENGTH_SECONDS,
            "return_buses": 2,
            "errors": errors,
        }
        print(json.dumps(result, indent=2))
        if errors:
            raise SystemExit(1)
    finally:
        client.stop()


if __name__ == "__main__":
    main()
