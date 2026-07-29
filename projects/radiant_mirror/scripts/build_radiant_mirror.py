#!/usr/bin/env python3
"""Idempotent staged builder for Radiant Mirror in the current Ableton Live Set."""

from __future__ import annotations

import argparse
import json
import math
import re
import socket
import sys
import time
from pathlib import Path

ABLETON_OSC = Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ABLETON_OSC))
from client.client import AbletonOSCClient  # noqa: E402

from projects.radiant_mirror.spec import (  # noqa: E402
    ATTACK_SECONDS,
    LENGTH_BEATS,
    MEMORY_SENDS,
    PANS,
    RELEASE_SECONDS,
    ROOM_SENDS,
    VOICES,
    VOICE_BASE_CHAIN,
    VOLUMES,
    expected_names,
)

DEFAULT_TRACKS = ["1-MIDI", "2-MIDI", "3-Audio", "4-Audio"]
CHAIN = VOICE_BASE_CHAIN


def query(client, address, params=()):
    return list(client.query(address, tuple(params), timeout=1.5))


def wait_for_track_count(client, expected, timeout=8.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        count = int(query(client, "/live/song/get/num_tracks")[0])
        if count == expected:
            return
        time.sleep(0.15)
    raise RuntimeError("Timed out waiting for %d tracks" % expected)


def track_names(client):
    return [str(value) for value in query(client, "/live/song/get/track_names")]


def require_field(client):
    """Confirm the twelve voices, and return only those.

    Later layers append tracks after the field — the wanderer, and whatever
    comes next — so every phase must work on the voices alone.
    """
    names = track_names(client)[:len(VOICES)]
    if names != expected_names():
        raise RuntimeError("Radiant Mirror tracks are not ready")
    return names


def build_tracks(client):
    current = track_names(client)
    wanted = expected_names()
    if current[:len(wanted)] == wanted:
        return {"status": "unchanged", "track_count": len(wanted),
                "tracks_after_field": current[len(wanted):]}
    if current not in (DEFAULT_TRACKS, [DEFAULT_TRACKS[0]]):
        raise RuntimeError(
            "Refusing to replace non-default tracks. Current names: %s" % current
        )
    # Live always retains at least one track. Delete defaults down to one,
    # then reuse that remaining MIDI track as the first reflection.
    for index in reversed(range(1, len(current))):
        client.send_message("/live/song/delete_track", [index])
        time.sleep(0.12)
    wait_for_track_count(client, 1)
    client.send_message("/live/track/set/name", [0, wanted[0]])
    time.sleep(0.12)
    for index, name in enumerate(wanted[1:], 1):
        client.send_message("/live/song/create_midi_track", [-1])
        wait_for_track_count(client, index + 1)
        client.send_message("/live/track/set/name", [index, name])
        time.sleep(0.12)
    names = track_names(client)
    if names != wanted:
        raise RuntimeError("Track-name verification failed: %s" % names)
    return {"status": "created", "track_count": len(names), "tracks": names}


def tcp_call(command, params=None, timeout=15.0):
    payload = json.dumps({"type": command, "params": params or {}}).encode("utf-8")
    with socket.create_connection(("127.0.0.1", 9877), timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(payload)
        data = bytearray()
        while True:
            data.extend(sock.recv(65536))
            try:
                response = json.loads(data)
                break
            except json.JSONDecodeError:
                continue
    if response.get("status") != "success":
        raise RuntimeError(response.get("message", "AbletonMCP command failed"))
    return response.get("result")


def device_names(client, track):
    return [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]


def load_operators(client):
    names = require_field(client)
    results = []
    for index, name in enumerate(names):
        count = int(query(client, "/live/track/get/num_devices", [index])[-1])
        if count == 0:
            result = tcp_call("load_browser_item", {
                "track_index": index,
                "item_uri": "query:Synths#Operator",
            })
            time.sleep(0.25)
            count = int(query(client, "/live/track/get/num_devices", [index])[-1])
            if count != 1:
                raise RuntimeError("Operator did not load on %s" % name)
            results.append({"track": index, "status": "loaded", "result": result})
        else:
            if "Operator" not in device_names(client, index):
                raise RuntimeError("Unexpected device already present on %s" % name)
            results.append({"track": index, "status": "unchanged"})
    return {"status": "ready", "operators": results}


def parameter_map(client, track=0, device=0):
    values = query(client, "/live/device/get/parameters/name", [track, device])
    return {str(name): index for index, name in enumerate(values[2:])}


def displayed_frequency(client, track, parameter_index):
    text = str(query(
        client, "/live/device/get/parameter/value_string",
        [track, 0, parameter_index],
    )[-1]).replace(",", "")
    match = re.search(r"([0-9.]+)\s*(k?Hz)", text, re.IGNORECASE)
    if not match:
        raise RuntimeError("Could not parse Operator frequency: %s" % text)
    value = float(match.group(1))
    return value * 1000.0 if match.group(2).lower() == "khz" else value


def set_parameter(client, track, parameter_index, value):
    client.send_message(
        "/live/device/set/parameter/value",
        [track, 0, parameter_index, float(value)],
    )
    time.sleep(0.06)


def set_fixed_frequency(client, track, parameter_index, target):
    if target < 10.0 or target > 2000.0:
        raise ValueError("Operator fixed-frequency base must be 10–2000 Hz")
    # Operator's Fixed Frequency control is logarithmic over 10–2000 Hz.
    # This is equivalent to selecting Fixed and typing the frequency in Live.
    parameter_value = math.log(target / 10.0) / math.log(200.0)
    set_parameter(client, track, parameter_index, parameter_value)
    actual = displayed_frequency(client, track, parameter_index)
    # Live displays high frequencies in kHz with two decimals (10 Hz steps),
    # so verification cannot be more precise than half a displayed step there.
    tolerance = 5.1 if target >= 1000 else max(0.02, target * 0.0005)
    if abs(actual - target) > tolerance:
        raise RuntimeError("Could not tune track %d to %g Hz; got %g Hz" % (track, target, actual))
    return {"target_hz": target, "display_hz": actual, "parameter_value": parameter_value}


def configure_operators(client):
    require_field(client)
    params = parameter_map(client)
    required = ["A Fix On ", "A Fix Freq", "A Fix Freq Mul", "Osc-A Level",
                "Osc-B On", "Osc-C On", "Osc-D On"]
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError("Operator parameter map changed; missing %s" % missing)
    tuned = []
    for track, (frequency, _role) in enumerate(VOICES):
        set_parameter(client, track, params["A Fix On "], 1)
        # Enum index 4 is the x1 multiplier. Index 0 shifts the oscillator
        # below the intended range and is effectively inaudible here.
        set_parameter(client, track, params["A Fix Freq Mul"], 4)
        set_parameter(client, track, params["Osc-A Level"], 1)
        for oscillator in ("Osc-B On", "Osc-C On", "Osc-D On"):
            set_parameter(client, track, params[oscillator], 0)
        result = set_fixed_frequency(client, track, params["A Fix Freq"], frequency)
        result["track"] = track
        tuned.append(result)
    return {"status": "configured", "voices": tuned}


def load_voice_effects(client):
    names = require_field(client)
    wanted = [
        ("Auto Filter", "query:AudioFx#Auto%20Filter"),
        ("Utility", "query:AudioFx#Utility"),
    ]
    results = []
    for track, track_name in enumerate(names):
        devices = device_names(client, track)
        if not devices or devices[0] != "Operator":
            raise RuntimeError("Operator is missing from %s" % track_name)
        for device_name, uri in wanted:
            if device_name not in devices:
                tcp_call("load_browser_item", {"track_index": track, "item_uri": uri})
                time.sleep(0.25)
                devices = device_names(client, track)
                if device_name not in devices:
                    raise RuntimeError("%s did not load on %s" % (device_name, track_name))
        if devices[:3] != CHAIN:
            raise RuntimeError("Unexpected device order on %s: %s" % (track_name, devices))
        results.append({"track": track, "devices": devices[:3]})
    return {"status": "ready", "tracks": results}


def displayed_time(client, track, parameter_index):
    text = str(query(
        client, "/live/device/get/parameter/value_string",
        [track, 0, parameter_index],
    )[-1]).strip().lower()
    match = re.search(r"([0-9.]+)\s*(ms|s|min)", text)
    if not match:
        raise RuntimeError("Could not parse Operator time: %s" % text)
    value, unit = float(match.group(1)), match.group(2)
    if unit == "ms":
        return value / 1000.0
    if unit == "min":
        return value * 60.0
    return value


def calibrate_time_parameter(client, parameter_index, target_seconds):
    low, high, best = 0.0, 1.0, None
    for _ in range(22):
        value = (low + high) / 2.0
        set_parameter(client, 0, parameter_index, value)
        actual = displayed_time(client, 0, parameter_index)
        if best is None or abs(actual - target_seconds) < abs(best[1] - target_seconds):
            best = (value, actual)
        if actual < target_seconds:
            low = value
        elif actual > target_seconds:
            high = value
        else:
            break
    return best


def make_playable_stack(client):
    require_field(client)
    params = parameter_map(client)
    attack_value, attack_display = calibrate_time_parameter(client, params["Ae Attack"], ATTACK_SECONDS)
    release_value, release_display = calibrate_time_parameter(client, params["Ae Release"], RELEASE_SECONDS)
    results = []
    for track, (frequency, role) in enumerate(VOICES):
        client.send_message("/live/track/set/volume", [track, VOLUMES[track]])
        client.send_message("/live/track/set/panning", [track, PANS[track]])
        set_parameter(client, track, params["Ae Attack"], attack_value)
        set_parameter(client, track, params["Ae Release"], release_value)
        has_clip = bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1])
        if not has_clip:
            client.send_message("/live/clip_slot/create_clip", [track, 0, LENGTH_BEATS])
            time.sleep(0.12)
            client.send_message(
                "/live/clip/add/notes",
                [track, 0, 60, 0.0, LENGTH_BEATS - 1.0, 80, False],
            )
            client.send_message(
                "/live/clip/set/name",
                [track, 0, "R%02d %gHz — %s" % (track + 1, frequency, role)],
            )
            time.sleep(0.12)
        results.append({
            "track": track, "frequency_hz": frequency,
            "volume": VOLUMES[track], "pan": PANS[track], "clip": True,
        })
    return {
        "status": "playable",
        "attack_seconds": attack_display,
        "release_seconds": release_display,
        "clip_length_beats": LENGTH_BEATS,
        "voices": results,
    }


def configure_spatial_sends(client):
    require_field(client)
    results = []
    for track in range(len(VOICES)):
        client.send_message("/live/track/set/send", [track, 0, ROOM_SENDS[track]])
        client.send_message("/live/track/set/send", [track, 1, MEMORY_SENDS[track]])
        time.sleep(0.06)
        room = float(query(client, "/live/track/get/send", [track, 0])[-1])
        memory = float(query(client, "/live/track/get/send", [track, 1])[-1])
        results.append({"track": track, "room_send": room, "memory_send": memory})
    return {"status": "configured", "sends": results}


def _fire(client, tracks, spacing):
    launched = []
    for position, track in enumerate(tracks):
        if not bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]):
            raise RuntimeError("Audition clip missing on track %d" % track)
        client.send_message("/live/clip_slot/fire", [track, 0])
        launched.append({"track": track, "frequency_hz": VOICES[track][0]})
        if spacing and position < len(tracks) - 1:
            time.sleep(spacing)
    return launched


def audition_core(client):
    """The innermost two pairs: the mirror at its narrowest."""
    require_field(client)
    client.send_message("/live/song/stop_all_clips", [])
    time.sleep(0.15)
    return {"status": "playing", "launched": _fire(client, [0, 1, 2, 3], 0.08)}


def audition_golden(client):
    """Open the golden pairs outward from the core."""
    require_field(client)
    return {"status": "playing", "launched": _fire(client, [4, 5, 6, 7], 8.0)}


def audition_full_field(client):
    """Depths and corona last: the field at full width."""
    require_field(client)
    return {"status": "playing", "launched": _fire(client, [8, 9, 10, 11], 6.0)}


def stop_audition(client):
    client.send_message("/live/song/stop_all_clips", [])
    client.send_message("/live/song/stop_playing", [])
    return {"status": "stopped"}


PHASES = {
    "tracks": build_tracks,
    "operators": load_operators,
    "configure": configure_operators,
    "effects": load_voice_effects,
    "playable": make_playable_stack,
    "spatial": configure_spatial_sends,
    "core": audition_core,
    "golden": audition_golden,
    "full": audition_full_field,
    "stop": stop_audition,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=sorted(PHASES))
    args = parser.parse_args()
    client = AbletonOSCClient()
    try:
        result = PHASES[args.phase](client)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
