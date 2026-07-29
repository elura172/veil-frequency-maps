#!/usr/bin/env python3
"""Build the Radiant Mirror wanderer: a theremin that glides between the field.

Idempotent. Appends one track after the twelve voices, gives it the AM-radio
chain, and parks it silently on the first waypoint. Motion is a separate act —
see perform_radiant_mirror.py.
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

from projects.radiant_mirror.scripts.breath_radiant_mirror import (  # noqa: E402
    calibrate_period,
    parameter_map,
    set_parameter,
    value_string,
)
from projects.radiant_mirror.scripts.build_radiant_mirror import (  # noqa: E402
    device_names,
    displayed_time,
    query,
    set_fixed_frequency,
    tcp_call,
    track_names,
    wait_for_track_count,
)
from projects.radiant_mirror.spec import (  # noqa: E402
    AM_DEVICE,
    AM_DEVICE_URI,
    AM_MODE_TREMOLO,
    AM_TIME_MODE_FREE,
    AM_WAVEFORM_SINE,
    LENGTH_BEATS,
    THEREMIN_AM_DEPTH,
    THEREMIN_AM_PERIOD_SECONDS,
    THEREMIN_ATTACK_SECONDS,
    THEREMIN_BASE_VOLUME,
    THEREMIN_CHAIN,
    THEREMIN_EROSION_AMOUNT,
    THEREMIN_EROSION_FREQ_HZ,
    THEREMIN_EROSION_URI,
    THEREMIN_EROSION_FILTER_WIDTH,
    THEREMIN_FILTER_BANDPASS,
    THEREMIN_FORMANT_HZ,
    THEREMIN_MEMORY_SEND,
    THEREMIN_NAME,
    THEREMIN_PAN,
    THEREMIN_PATH,
    THEREMIN_RELEASE_SECONDS,
    THEREMIN_RESONANCE,
    THEREMIN_ROOM_SEND,
    THEREMIN_WAVE,
    VOICES,
    expected_names,
    theremin_levels,
)

DEVICE_URIS = {
    "Operator": "query:Synths#Operator",
    "Auto Filter": "query:AudioFx#Auto%20Filter",
    "Erosion": THEREMIN_EROSION_URI,
    AM_DEVICE: AM_DEVICE_URI,
    "Utility": "query:AudioFx#Utility",
}


def ensure_track(client):
    names = track_names(client)
    if names[:len(VOICES)] != expected_names():
        raise RuntimeError("Radiant Mirror's voice field is not intact")
    if THEREMIN_NAME in names:
        return names.index(THEREMIN_NAME), "unchanged"
    client.send_message("/live/song/create_midi_track", [-1])
    wait_for_track_count(client, len(names) + 1)
    index = len(names)
    client.send_message("/live/track/set/name", [index, THEREMIN_NAME])
    time.sleep(0.2)
    if track_names(client)[index] != THEREMIN_NAME:
        raise RuntimeError("Could not name the wanderer track")
    return index, "created"


def ensure_chain(client, track):
    """Load the AM-radio chain in order, silencing each modulator as it lands."""
    for position, device_name in enumerate(THEREMIN_CHAIN):
        devices = device_names(client, track)
        if len(devices) > position and devices[position] == device_name:
            continue
        if device_name in devices:
            raise RuntimeError(
                "%s is already on the wanderer out of order: %s" % (device_name, devices)
            )
        tcp_call("load_browser_item", {"track_index": track, "item_uri": DEVICE_URIS[device_name]})
        time.sleep(0.45)
        devices = device_names(client, track)
        if len(devices) <= position or devices[position] != device_name:
            raise RuntimeError("%s did not land at position %d: %s" % (device_name, position, devices))
        if device_name == AM_DEVICE:
            params = parameter_map(client, track, position)
            set_parameter(client, track, position, params["Amount"], 0.0)
    devices = device_names(client, track)
    if devices[:len(THEREMIN_CHAIN)] != THEREMIN_CHAIN:
        raise RuntimeError("Unexpected wanderer chain: %s" % devices)
    return devices[:len(THEREMIN_CHAIN)]


def configure_operator(client, track):
    params = parameter_map(client, track, 0)
    required = ["A Fix On ", "A Fix Freq", "A Fix Freq Mul", "Osc-A Level", "Osc-A Wave",
                "Osc-B On", "Osc-C On", "Osc-D On", "Ae Attack", "Ae Release"]
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError("Operator parameter map changed; missing %s" % missing)
    set_parameter(client, track, 0, params["A Fix On "], 1)
    set_parameter(client, track, 0, params["A Fix Freq Mul"], 4)
    set_parameter(client, track, 0, params["Osc-A Level"], 1)
    set_parameter(client, track, 0, params["Osc-A Wave"], THEREMIN_WAVE)
    for oscillator in ("Osc-B On", "Osc-C On", "Osc-D On"):
        set_parameter(client, track, 0, params[oscillator], 0)

    start_hz = VOICES[THEREMIN_PATH[0]][0]
    tuning = set_fixed_frequency(client, track, params["A Fix Freq"], start_hz)

    attack_value, attack_display = calibrate_time_parameter_on(
        client, track, params["Ae Attack"], THEREMIN_ATTACK_SECONDS)
    release_value, release_display = calibrate_time_parameter_on(
        client, track, params["Ae Release"], THEREMIN_RELEASE_SECONDS)
    set_parameter(client, track, 0, params["Ae Attack"], attack_value)
    set_parameter(client, track, 0, params["Ae Release"], release_value)
    return {
        "start_hz": tuning["display_hz"],
        "wave_index": THEREMIN_WAVE,
        "attack_seconds": attack_display,
        "release_seconds": release_display,
        "fix_freq_parameter": params["A Fix Freq"],
    }


def calibrate_time_parameter_on(client, track, parameter_index, target_seconds):
    """build_radiant_mirror's envelope calibrator, but on an arbitrary track."""
    low, high, best = 0.0, 1.0, None
    for _ in range(22):
        value = (low + high) / 2.0
        set_parameter(client, track, 0, parameter_index, value)
        actual = displayed_time(client, track, parameter_index)
        if best is None or abs(actual - target_seconds) < abs(best[1] - target_seconds):
            best = (value, actual)
        if actual < target_seconds:
            low = value
        elif actual > target_seconds:
            high = value
        else:
            break
    return best


def configure_filter(client, track):
    device = THEREMIN_CHAIN.index("Auto Filter")
    params = parameter_map(client, track, device)
    for required in ("Filter Type", "Frequency", "Resonance"):
        if required not in params:
            raise RuntimeError("Auto Filter parameter map changed; missing %r" % required)
    set_parameter(client, track, device, params["Filter Type"], THEREMIN_FILTER_BANDPASS)
    set_parameter(client, track, device, params["Resonance"], THEREMIN_RESONANCE)
    control, displayed = calibrate_filter_frequency(
        client, track, device, params["Frequency"], THEREMIN_FORMANT_HZ)
    set_parameter(client, track, device, params["Frequency"], control)
    return {"formant_hz": displayed, "resonance": THEREMIN_RESONANCE}


def calibrate_filter_frequency(client, track, device, parameter, target):
    low, high, best = 0.0, 1.0, None
    for _ in range(22):
        control = (low + high) / 2.0
        set_parameter(client, track, device, parameter, control)
        text = str(query(client, "/live/device/get/parameter/value_string",
                         [track, device, parameter])[-1]).replace(",", "")
        match = re.search(r"([0-9.]+)\s*(k?Hz)", text, re.IGNORECASE)
        if not match:
            raise RuntimeError("Cannot parse Auto Filter frequency: %s" % text)
        actual = float(match.group(1))
        if match.group(2).lower() == "khz":
            actual *= 1000.0
        if best is None or abs(actual - target) < abs(best[1] - target):
            best = (control, actual)
        if actual < target:
            low = control
        elif actual > target:
            high = control
        else:
            break
    return best


def configure_erosion(client, track):
    """The static between stations."""
    device = THEREMIN_CHAIN.index("Erosion")
    params = parameter_map(client, track, device)
    required = ["Frequency", "Filter Width", "Amount"]
    missing = [name for name in required if name not in params]
    if missing:
        raise RuntimeError("Erosion parameter map changed; missing %s" % missing)
    set_parameter(client, track, device, params["Filter Width"], THEREMIN_EROSION_FILTER_WIDTH)
    set_parameter(client, track, device, params["Amount"], THEREMIN_EROSION_AMOUNT)
    control, displayed = calibrate_filter_frequency(
        client, track, device, params["Frequency"], THEREMIN_EROSION_FREQ_HZ)
    set_parameter(client, track, device, params["Frequency"], control)
    if abs(displayed - THEREMIN_EROSION_FREQ_HZ) > THEREMIN_EROSION_FREQ_HZ * 0.05:
        raise RuntimeError(
            "Erosion settled at %g Hz, expected %g Hz" % (displayed, THEREMIN_EROSION_FREQ_HZ)
        )
    return {
        "frequency_hz": displayed,
        "filter_width": value_string(client, track, device, params["Filter Width"]),
        "amount": value_string(client, track, device, params["Amount"]),
    }


def configure_tremolo(client, track):
    device = THEREMIN_CHAIN.index(AM_DEVICE)
    params = parameter_map(client, track, device)
    set_parameter(client, track, device, params["Amount"], 0.0)
    set_parameter(client, track, device, params["Mode"], AM_MODE_TREMOLO)
    set_parameter(client, track, device, params["Time Mode"], AM_TIME_MODE_FREE)
    set_parameter(client, track, device, params["Waveform"], AM_WAVEFORM_SINE)
    set_parameter(client, track, device, params["Phase"], 0.0)
    set_parameter(client, track, device, params["Stereo Mode"], 0)
    control, displayed = calibrate_period(
        client, track, device, params["Time"], THEREMIN_AM_PERIOD_SECONDS)
    set_parameter(client, track, device, params["Time"], control)
    set_parameter(client, track, device, params["Amount"], THEREMIN_AM_DEPTH)
    return {"period_seconds": displayed, "depth": THEREMIN_AM_DEPTH}


def configure_mix(client, track):
    levels = theremin_levels()
    client.send_message("/live/track/set/volume", [track, levels[0]])
    client.send_message("/live/track/set/panning", [track, THEREMIN_PAN])
    client.send_message("/live/track/set/send", [track, 0, THEREMIN_ROOM_SEND])
    client.send_message("/live/track/set/send", [track, 1, THEREMIN_MEMORY_SEND])
    time.sleep(0.1)
    has_clip = bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1])
    if not has_clip:
        client.send_message("/live/clip_slot/create_clip", [track, 0, LENGTH_BEATS])
        time.sleep(0.15)
        client.send_message("/live/clip/add/notes",
                            [track, 0, 60, 0.0, LENGTH_BEATS - 1.0, 90, False])
        client.send_message("/live/clip/set/name", [track, 0, THEREMIN_NAME])
        time.sleep(0.15)
    return {"volume": levels[0], "pan": THEREMIN_PAN,
            "room_send": THEREMIN_ROOM_SEND, "memory_send": THEREMIN_MEMORY_SEND,
            "clip": True}


def main():
    client = AbletonOSCClient()
    try:
        track, track_status = ensure_track(client)
        chain = ensure_chain(client, track)
        result = {
            "status": "ready",
            "track": track,
            "track_status": track_status,
            "name": THEREMIN_NAME,
            "chain": chain,
            "operator": configure_operator(client, track),
            "filter": configure_filter(client, track),
            "erosion": configure_erosion(client, track),
            "tremolo": configure_tremolo(client, track),
            "mix": configure_mix(client, track),
            "base_volume": THEREMIN_BASE_VOLUME,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
