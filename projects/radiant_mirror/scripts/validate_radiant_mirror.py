#!/usr/bin/env python3
"""Validate the Radiant Mirror field currently loaded in Ableton Live.

Reads Live back and compares it against the specification. Changes nothing.
Exits non-zero and prints every failure when Live and the spec disagree.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"))
from client.client import AbletonOSCClient  # noqa: E402

from projects.radiant_mirror.scripts.breath_radiant_mirror import (  # noqa: E402
    displayed_period,
)
from projects.radiant_mirror.scripts.breath_radiant_mirror import (  # noqa: E402
    parameter_map as device_parameter_map,
)
from projects.radiant_mirror.scripts.build_radiant_mirror import (  # noqa: E402
    device_names,
    displayed_frequency,
    displayed_time,
    parameter_map,
    query,
    track_names,
)
from projects.radiant_mirror.spec import (  # noqa: E402
    AM_DEPTHS,
    AM_DEVICE,
    AM_MODE_TREMOLO,
    AM_OFFSETS,
    AM_PERIODS,
    AM_PERIOD_TOLERANCE,
    AM_TIME_MODE_FREE,
    AM_WAVEFORM_SINE,
    ATTACK_SECONDS,
    LENGTH_BEATS,
    LOWER_LEAF,
    MEMORY_SENDS,
    PANS,
    RELEASE_SECONDS,
    ROOM_DECAY_SECONDS,
    ROOM_DEVICE,
    ROOM_DIFFUSION_PERCENT,
    ROOM_INPUT_FREQ_HZ,
    ROOM_PREDELAY_MS,
    ROOM_RETURN_INDEX,
    ROOM_RETURN_NAME,
    ROOM_SCALE_PERCENT,
    ROOM_SENDS,
    ROOM_TOLERANCE,
    THEREMIN_AM_DEPTH,
    THEREMIN_AM_PERIOD_SECONDS,
    THEREMIN_CHAIN,
    THEREMIN_MEMORY_SEND,
    THEREMIN_NAME,
    THEREMIN_PATH,
    THEREMIN_ROOM_SEND,
    THEREMIN_WAVE,
    UPPER_LEAF,
    VOICES,
    VOICE_CHAIN,
    VOLUMES,
    expected_names,
)

CHAIN = VOICE_CHAIN
MIX_TOLERANCE = 0.005


def frequency_tolerance(target):
    # Live displays kilohertz in 10 Hz steps, so verification above 1 kHz
    # cannot be finer than half a displayed step.
    return 5.1 if target >= 1000 else max(0.02, target * 0.0005)


def check(failures, condition, message):
    if not condition:
        failures.append(message)


def validate(client):
    failures = []

    names = track_names(client)
    check(failures, names[:len(VOICES)] == expected_names(),
          "Voice track names do not match the specification: %s" % names[:len(VOICES)])
    if failures:
        return failures

    params = parameter_map(client)
    for required in ("A Fix On ", "A Fix Freq", "Ae Attack", "Ae Release"):
        check(failures, required in params,
              "Operator parameter %r is missing from Live" % required)
    if failures:
        return failures

    reference_attack = None
    reference_release = None

    for track, (frequency, _role) in enumerate(VOICES):
        devices = device_names(client, track)
        check(failures, devices[:len(CHAIN)] == CHAIN,
              "Track %d device chain is %s, expected %s" % (track, devices[:len(CHAIN)], CHAIN))

        fixed_on = float(query(client, "/live/device/get/parameter/value",
                               [track, 0, params["A Fix On "]])[-1])
        check(failures, fixed_on == 1.0,
              "Track %d is not in Operator fixed-frequency mode" % track)

        displayed = displayed_frequency(client, track, params["A Fix Freq"])
        check(failures, abs(displayed - frequency) <= frequency_tolerance(frequency),
              "Track %d is tuned to %g Hz, expected %g Hz" % (track, displayed, frequency))

        volume = float(query(client, "/live/track/get/volume", [track])[-1])
        check(failures, abs(volume - VOLUMES[track]) <= MIX_TOLERANCE,
              "Track %d volume is %.4f, expected %.4f" % (track, volume, VOLUMES[track]))

        panning = float(query(client, "/live/track/get/panning", [track])[-1])
        check(failures, abs(panning - PANS[track]) <= MIX_TOLERANCE,
              "Track %d pan is %.4f, expected %.4f" % (track, panning, PANS[track]))

        room = float(query(client, "/live/track/get/send", [track, 0])[-1])
        check(failures, abs(room - ROOM_SENDS[track]) <= MIX_TOLERANCE,
              "Track %d room send is %.4f, expected %.4f" % (track, room, ROOM_SENDS[track]))

        memory = float(query(client, "/live/track/get/send", [track, 1])[-1])
        check(failures, abs(memory - MEMORY_SENDS[track]) <= MIX_TOLERANCE,
              "Track %d memory send is %.4f, expected %.4f" % (track, memory, MEMORY_SENDS[track]))

        has_clip = bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1])
        check(failures, has_clip, "Track %d has no clip in slot 0" % track)
        if has_clip:
            length = float(query(client, "/live/clip/get/length", [track, 0])[-1])
            check(failures, abs(length - LENGTH_BEATS) <= 0.01,
                  "Track %d clip is %g beats, expected %g" % (track, length, LENGTH_BEATS))

        attack = displayed_time(client, track, params["Ae Attack"])
        release = displayed_time(client, track, params["Ae Release"])
        if track == 0:
            reference_attack, reference_release = attack, release
            check(failures, abs(attack - ATTACK_SECONDS) <= ATTACK_SECONDS * 0.05,
                  "Attack is %.2f s, expected %.2f s" % (attack, ATTACK_SECONDS))
            check(failures, abs(release - RELEASE_SECONDS) <= RELEASE_SECONDS * 0.05,
                  "Release is %.2f s, expected %.2f s" % (release, RELEASE_SECONDS))
        else:
            check(failures, abs(attack - reference_attack) <= 0.05,
                  "Track %d attack is %.2f s, expected %.2f s" % (track, attack, reference_attack))
            check(failures, abs(release - reference_release) <= 0.05,
                  "Track %d release is %.2f s, expected %.2f s" % (track, release, reference_release))

    validate_breath(client, failures)
    validate_room(client, failures)
    validate_wanderer(client, failures)
    return failures


def validate_breath(client, failures):
    """Every pair shares one period and sits half a cycle apart."""
    pair_of = {}
    for pair, (lower, upper) in enumerate(zip(LOWER_LEAF, UPPER_LEAF)):
        pair_of[lower] = pair
        pair_of[upper] = pair

    device = CHAIN.index(AM_DEVICE)
    for track in range(len(VOICES)):
        params = device_parameter_map(client, track, device)
        for required in ("Mode", "Amount", "Waveform", "Time Mode", "Time", "Offset"):
            if required not in params:
                failures.append("Track %d %s is missing %r" % (track, AM_DEVICE, required))
                return

        mode = float(query(client, "/live/device/get/parameter/value",
                           [track, device, params["Mode"]])[-1])
        check(failures, mode == AM_MODE_TREMOLO,
              "Track %d %s is not in tremolo mode" % (track, AM_DEVICE))

        time_mode = float(query(client, "/live/device/get/parameter/value",
                                [track, device, params["Time Mode"]])[-1])
        check(failures, time_mode == AM_TIME_MODE_FREE,
              "Track %d %s is not in free time mode" % (track, AM_DEVICE))

        waveform = float(query(client, "/live/device/get/parameter/value",
                               [track, device, params["Waveform"]])[-1])
        check(failures, waveform == AM_WAVEFORM_SINE,
              "Track %d breath waveform is %g, expected sine" % (track, waveform))

        target = AM_PERIODS[pair_of[track]]
        period = displayed_period(client, track, device, params["Time"])
        check(failures, abs(period - target) <= max(0.05, target * AM_PERIOD_TOLERANCE),
              "Track %d breathes every %.3f s, expected %.3f s" % (track, period, target))

        depth = float(query(client, "/live/device/get/parameter/value",
                            [track, device, params["Amount"]])[-1])
        check(failures, abs(depth - AM_DEPTHS[track]) <= MIX_TOLERANCE,
              "Track %d breath depth is %.4f, expected %.4f" % (track, depth, AM_DEPTHS[track]))

        offset = float(query(client, "/live/device/get/parameter/value",
                             [track, device, params["Offset"]])[-1])
        check(failures, abs(offset - AM_OFFSETS[track]) <= MIX_TOLERANCE,
              "Track %d breath offset is %.4f, expected %.4f" % (track, offset, AM_OFFSETS[track]))


def validate_room(client, failures):
    """The reverb on return A, read through the return-track endpoints."""
    try:
        names = [str(v) for v in query(client, "/live/song/get/return_track_names")]
    except RuntimeError:
        failures.append(
            "AbletonOSC has no return-track endpoints; apply "
            "integrations/abletonosc/return-tracks.patch and reload"
        )
        return

    if ROOM_RETURN_INDEX >= len(names) or names[ROOM_RETURN_INDEX] != ROOM_RETURN_NAME:
        failures.append("Return %d is not %r" % (ROOM_RETURN_INDEX, ROOM_RETURN_NAME))
        return

    devices = [str(v) for v in query(
        client, "/live/return/get/devices/name", [ROOM_RETURN_INDEX])[1:]]
    if not devices or devices[0] != ROOM_DEVICE:
        failures.append("Return %d carries %s, expected %s first" % (ROOM_RETURN_INDEX, devices, ROOM_DEVICE))
        return

    parameter_names = query(
        client, "/live/return/get/device/parameters/name", [ROOM_RETURN_INDEX, 0])[2:]
    params = {str(name): index for index, name in enumerate(parameter_names)}

    def room_display(name):
        return str(query(client, "/live/return/get/device/parameter/value_string",
                         [ROOM_RETURN_INDEX, 0, params[name]])[-1])

    def room_number(name, unit):
        text = room_display(name).strip().replace(",", "")
        match = re.search(r"(-?[0-9.]+)\s*(ms|s|kHz|Hz|%)?", text, re.IGNORECASE)
        if not match:
            raise RuntimeError("Cannot parse reverb display for %s: %r" % (name, text))
        value = float(match.group(1))
        seen = (match.group(2) or "").lower()
        scale = {"ms": 0.001, "s": 1.0, "hz": 1.0, "khz": 1000.0}
        return value * scale.get(seen, 1.0) / scale.get(unit, 1.0)

    for name, target, unit in (
        ("Predelay", ROOM_PREDELAY_MS, "ms"),
        ("Decay Time", ROOM_DECAY_SECONDS, "s"),
        ("Diffusion", ROOM_DIFFUSION_PERCENT, "%"),
        ("Scale", ROOM_SCALE_PERCENT, "%"),
        ("Input Freq", ROOM_INPUT_FREQ_HZ, "hz"),
    ):
        if name not in params:
            failures.append("Reverb is missing %r" % name)
            continue
        actual = room_number(name, unit)
        check(failures, abs(actual - target) <= max(1e-6, abs(target) * ROOM_TOLERANCE),
              "Room %s is %g, expected %g" % (name, actual, target))

    check(failures, room_display("Dry/Wet").startswith("100"),
          "Room Dry/Wet is %s on a return, expected 100 %%" % room_display("Dry/Wet"))
    check(failures, room_display("Chorus On") == "Off",
          "Room chorus is %s; the field's ratios must not be detuned" % room_display("Chorus On"))


def validate_wanderer(client, failures):
    """The theremin track, parked or gliding."""
    names = track_names(client)
    if THEREMIN_NAME not in names:
        failures.append("The wanderer %r is missing" % THEREMIN_NAME)
        return
    track = names.index(THEREMIN_NAME)

    devices = device_names(client, track)
    check(failures, devices[:len(THEREMIN_CHAIN)] == THEREMIN_CHAIN,
          "Wanderer chain is %s, expected %s" % (devices[:len(THEREMIN_CHAIN)], THEREMIN_CHAIN))
    if devices[:1] != ["Operator"]:
        return

    params = parameter_map(client, track)
    fixed_on = float(query(client, "/live/device/get/parameter/value",
                           [track, 0, params["A Fix On "]])[-1])
    check(failures, fixed_on == 1.0, "The wanderer is not in fixed-frequency mode")

    wave = float(query(client, "/live/device/get/parameter/value",
                       [track, 0, params["Osc-A Wave"]])[-1])
    check(failures, wave == THEREMIN_WAVE,
          "Wanderer waveform is %g, expected %g" % (wave, THEREMIN_WAVE))

    # Its pitch is a moving target by design, so only the reachable span is
    # checked, not a fixed value.
    hertz = displayed_frequency(client, track, params["A Fix Freq"])
    span = [VOICES[voice][0] for voice in THEREMIN_PATH]
    check(failures, min(span) * 0.9 <= hertz <= max(span) * 1.1,
          "The wanderer is at %g Hz, outside the field it wanders" % hertz)

    tremolo = THEREMIN_CHAIN.index(AM_DEVICE)
    am = device_parameter_map(client, track, tremolo)
    period = displayed_period(client, track, tremolo, am["Time"])
    check(failures, abs(period - THEREMIN_AM_PERIOD_SECONDS) <= 0.02,
          "Wanderer tremolo is %.3f s, expected %.3f s" % (period, THEREMIN_AM_PERIOD_SECONDS))
    depth = float(query(client, "/live/device/get/parameter/value",
                        [track, tremolo, am["Amount"]])[-1])
    check(failures, abs(depth - THEREMIN_AM_DEPTH) <= MIX_TOLERANCE,
          "Wanderer tremolo depth is %.4f, expected %.4f" % (depth, THEREMIN_AM_DEPTH))

    room = float(query(client, "/live/track/get/send", [track, 0])[-1])
    memory = float(query(client, "/live/track/get/send", [track, 1])[-1])
    check(failures, abs(room - THEREMIN_ROOM_SEND) <= MIX_TOLERANCE,
          "Wanderer room send is %.4f, expected %.4f" % (room, THEREMIN_ROOM_SEND))
    check(failures, abs(memory - THEREMIN_MEMORY_SEND) <= MIX_TOLERANCE,
          "Wanderer memory send is %.4f, expected %.4f" % (memory, THEREMIN_MEMORY_SEND))

    check(failures, bool(query(client, "/live/clip_slot/get/has_clip", [track, 0])[-1]),
          "The wanderer has no clip in slot 0")


def main():
    client = AbletonOSCClient()
    try:
        failures = validate(client)
    finally:
        client.stop()
    if failures:
        print(json.dumps({"status": "invalid", "failures": failures}, indent=2, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps({
        "status": "valid",
        "voices": len(VOICES),
        "chain": CHAIN,
        "length_beats": LENGTH_BEATS,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
