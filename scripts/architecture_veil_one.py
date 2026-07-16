#!/usr/bin/env python3
"""Build Veil One's complete six-minute Arrangement and safe opening state."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))

from client.client import AbletonOSCClient  # noqa: E402
from scripts.build_veil_one import tcp_call  # noqa: E402
from scripts.veil_one import (  # noqa: E402
    FLOOR,
    FOUNDATION,
    LENGTH_BEATS,
    LENGTH_SECONDS,
    M4L_HOST,
    MEMORY_SENDS,
    ROOM_SENDS,
    TEMPO,
    VOLUMES,
    expected_names,
)


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=2.0))


def arrangement_clip_count(track):
    return int(tcp_call("get_arrangement_clips", {"track_index": track})["clip_count"])


def build_arrangement():
    results = []
    for track in range(16):
        count = arrangement_clip_count(track)
        if count == 0:
            result = tcp_call("duplicate_session_clip_to_arrangement", {
                "track_index": track,
                "clip_index": 0,
                "destination_time": 0.0,
            })
            time.sleep(0.08)
            count = arrangement_clip_count(track)
            if count != 1:
                raise RuntimeError(f"Arrangement clip failed on track {track + 1}")
            results.append({"track": track, "status": "created", "result": result})
        elif count == 1:
            clip = tcp_call("get_arrangement_clips", {"track_index": track})["clips"][0]
            if abs(float(clip["start_time"])) > 0.001 or abs(float(clip["length"]) - LENGTH_BEATS) > 0.01:
                raise RuntimeError(f"Unexpected Arrangement clip on track {track + 1}: {clip}")
            results.append({"track": track, "status": "unchanged"})
        else:
            raise RuntimeError(f"Refusing to alter {count} Arrangement clips on track {track + 1}")
    return results


def set_opening_state(client):
    client.send_message("/live/song/stop_all_clips", [])
    client.send_message("/live/song/stop_playing", [])
    client.send_message("/live/song/set/tempo", [TEMPO])
    client.send_message("/live/song/set/signature_numerator", [4])
    client.send_message("/live/song/set/signature_denominator", [4])
    client.send_message("/live/song/set/loop", [0])
    client.send_message("/live/song/set/current_song_time", [0.0])
    for track in range(16):
        client.send_message("/live/track/set/volume", [track, VOLUMES[track] if track in set(FOUNDATION) else FLOOR])
        client.send_message("/live/track/set/send", [track, 0, ROOM_SENDS[track]])
        client.send_message("/live/track/set/send", [track, 1, 0.0])
        time.sleep(0.025)

    # Return buses have generous headroom; B begins silent until the memory section.
    tcp_call("set_return_track_volume", {"return_index": 0, "value": 0.26})
    tcp_call("set_return_track_volume", {"return_index": 1, "value": 0.20})

    names = [str(v) for v in query(client, "/live/song/get/track_names")]
    if M4L_HOST in names:
        tcp_call("set_track_mute", {"track_index": names.index(M4L_HOST), "mute": True})


def main():
    client = AbletonOSCClient()
    try:
        names = [str(v) for v in query(client, "/live/song/get/track_names")]
        if names[:16] != expected_names():
            raise RuntimeError("Veil One's voice field is not intact")
        if any(not bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]) for track in range(16)):
            raise RuntimeError("One or more 720-beat source clips are missing")
        arrangement = build_arrangement()
        set_opening_state(client)
        print(json.dumps({
            "status": "complete",
            "tempo": TEMPO,
            "length_beats": LENGTH_BEATS,
            "length_seconds": LENGTH_SECONDS,
            "voice_count": 16,
            "arrangement": arrangement,
            "opening_voices": [1, 3, 5],
        }, indent=2))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
