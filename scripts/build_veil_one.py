#!/usr/bin/env python3
"""Idempotent staged builder for Veil One in the current Ableton Live Set."""

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
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ABLETON_OSC))
from client.client import AbletonOSCClient  # noqa: E402

from scripts.veil_one import (  # noqa: E402
    MEMORY_SENDS,
    PANS,
    ROOM_SENDS,
    VOICES,
    VOLUMES,
    expected_names,
)

DEFAULT_TRACKS = ["1-MIDI", "2-MIDI", "3-Audio", "4-Audio"]


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


def build_tracks(client):
    current = [str(value) for value in query(client, "/live/song/get/track_names")]
    wanted = expected_names()
    if current == wanted:
        return {"status": "unchanged", "track_count": len(current)}
    if current not in (DEFAULT_TRACKS, [DEFAULT_TRACKS[0]]):
        raise RuntimeError(
            "Refusing to replace non-default tracks. Current names: %s" % current
        )
    # Live always retains at least one track. Delete defaults down to one,
    # then reuse that remaining MIDI track as voice 1.
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
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
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


def load_operators(client):
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    if names != expected_names():
        raise RuntimeError("Veil One tracks are not ready")
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
            device_names = query(client, "/live/track/get/devices/name", [index])
            if "Operator" not in [str(v) for v in device_names]:
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
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    if names != expected_names():
        raise RuntimeError("Veil One tracks are not ready")
    params = parameter_map(client)
    required = ["A Fix On ", "A Fix Freq", "A Fix Freq Mul", "Osc-A Level", "Osc-B On", "Osc-C On", "Osc-D On"]
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
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    if names != expected_names():
        raise RuntimeError("Veil One tracks are not ready")
    wanted = [
        ("Auto Filter", "query:AudioFx#Auto%20Filter"),
        ("Utility", "query:AudioFx#Utility"),
    ]
    results = []
    for track, track_name in enumerate(names):
        device_names = [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]
        if not device_names or device_names[0] != "Operator":
            raise RuntimeError("Operator is missing from %s" % track_name)
        for device_name, uri in wanted:
            if device_name not in device_names:
                tcp_call("load_browser_item", {"track_index": track, "item_uri": uri})
                time.sleep(0.25)
                device_names = [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]
                if device_name not in device_names:
                    raise RuntimeError("%s did not load on %s" % (device_name, track_name))
        if device_names[:3] != ["Operator", "Auto Filter", "Utility"]:
            raise RuntimeError("Unexpected device order on %s: %s" % (track_name, device_names))
        results.append({"track": track, "devices": device_names[:3]})
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
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    if names != expected_names():
        raise RuntimeError("Veil One tracks are not ready")
    params = parameter_map(client)
    attack_value, attack_display = calibrate_time_parameter(client, params["Ae Attack"], 8.0)
    release_value, release_display = calibrate_time_parameter(client, params["Ae Release"], 12.0)
    results = []
    for track, (frequency, role) in enumerate(VOICES):
        client.send_message("/live/track/set/volume", [track, VOLUMES[track]])
        client.send_message("/live/track/set/panning", [track, PANS[track]])
        set_parameter(client, track, params["Ae Attack"], attack_value)
        set_parameter(client, track, params["Ae Release"], release_value)
        has_clip = bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1])
        if not has_clip:
            client.send_message("/live/clip_slot/create_clip", [track, 0, 720.0])
            time.sleep(0.12)
            client.send_message("/live/clip/add/notes", [track, 0, 60, 0.0, 719.0, 80, False])
            client.send_message("/live/clip/set/name", [track, 0, "V%02d %gHz — %s" % (track + 1, frequency, role)])
            time.sleep(0.12)
        results.append({
            "track": track, "frequency_hz": frequency,
            "volume": VOLUMES[track], "pan": PANS[track], "clip": True,
        })
    return {
        "status": "playable",
        "attack_seconds": attack_display,
        "release_seconds": release_display,
        "clip_length_beats": 720.0,
        "voices": results,
    }


def configure_spatial_sends(client):
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    if names != expected_names():
        raise RuntimeError("Veil One tracks are not ready")
    results = []
    for track in range(len(VOICES)):
        client.send_message("/live/track/set/send", [track, 0, ROOM_SENDS[track]])
        client.send_message("/live/track/set/send", [track, 1, MEMORY_SENDS[track]])
        time.sleep(0.06)
        room = float(query(client, "/live/track/get/send", [track, 0])[-1])
        memory = float(query(client, "/live/track/get/send", [track, 1])[-1])
        results.append({"track": track, "room_send": room, "memory_send": memory})
    return {"status": "configured", "sends": results}


def audition_foundation(client):
    client.send_message("/live/song/stop_all_clips", [])
    time.sleep(0.15)
    tracks = [0, 2, 4]
    for track in tracks:
        if not bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]):
            raise RuntimeError("Audition clip missing on track %d" % track)
        client.send_message("/live/clip_slot/fire", [track, 0])
        time.sleep(0.08)
    return {
        "status": "playing",
        "tracks": tracks,
        "frequencies_hz": [VOICES[index][0] for index in tracks],
    }


def audition_fifths(client):
    tracks = [1, 3, 6]
    launched = []
    for position, track in enumerate(tracks):
        if not bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]):
            raise RuntimeError("Audition clip missing on track %d" % track)
        client.send_message("/live/clip_slot/fire", [track, 0])
        launched.append({"track": track, "frequency_hz": VOICES[track][0]})
        if position < len(tracks) - 1:
            time.sleep(10.0)
    return {"status": "playing", "launched": launched}


def audition_full_field(client):
    tracks = [7, 9, 10, 5, 8, 11, 12, 13, 14, 15]
    launched = []
    for position, track in enumerate(tracks):
        if not bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]):
            raise RuntimeError("Audition clip missing on track %d" % track)
        client.send_message("/live/clip_slot/fire", [track, 0])
        launched.append({"track": track, "frequency_hz": VOICES[track][0]})
        if position < len(tracks) - 1:
            time.sleep(5.0)
    return {"status": "playing", "launched": launched}


def stop_audition(client):
    client.send_message("/live/song/stop_all_clips", [])
    client.send_message("/live/song/stop_playing", [])
    return {"status": "stopped"}


def create_m4l_host(client):
    names = [str(value) for value in query(client, "/live/song/get/track_names")]
    host_name = "M4L — Veil Modulator DEV"
    if host_name in names:
        track = names.index(host_name)
    else:
        client.send_message("/live/song/create_audio_track", [-1])
        wait_for_track_count(client, len(names) + 1)
        track = len(names)
        client.send_message("/live/track/set/name", [track, host_name])
        time.sleep(0.15)
    devices = [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]
    if "Max Audio Effect" not in devices:
        browser = tcp_call("get_browser_items_at_path", {"path": "audio_effects"})
        matches = [item for item in browser.get("items", []) if item.get("name") == "Max Audio Effect"]
        if not matches:
            raise RuntimeError("Max Audio Effect is not present in Live's Audio Effects browser")
        tcp_call("load_browser_item", {
            "track_index": track,
            "item_uri": matches[0]["uri"],
        })
        time.sleep(0.5)
        devices = [str(v) for v in query(client, "/live/track/get/devices/name", [track])[1:]]
    if "Max Audio Effect" not in devices:
        raise RuntimeError("Blank Max Audio Effect did not load")
    return {"status": "ready", "track": track, "name": host_name, "devices": devices}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["tracks", "operators", "configure", "effects", "playable", "spatial", "audition", "fifths", "full", "stop", "m4l-host"])
    args = parser.parse_args()
    client = AbletonOSCClient()
    try:
        if args.phase == "tracks":
            result = build_tracks(client)
        elif args.phase == "operators":
            result = load_operators(client)
        elif args.phase == "configure":
            result = configure_operators(client)
        elif args.phase == "effects":
            result = load_voice_effects(client)
        elif args.phase == "playable":
            result = make_playable_stack(client)
        elif args.phase == "spatial":
            result = configure_spatial_sends(client)
        elif args.phase == "audition":
            result = audition_foundation(client)
        elif args.phase == "fifths":
            result = audition_fifths(client)
        elif args.phase == "full":
            result = audition_full_field(client)
        elif args.phase == "stop":
            result = stop_audition(client)
        else:
            result = create_m4l_host(client)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
