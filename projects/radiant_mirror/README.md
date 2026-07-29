# Radiant Mirror

Radiant Mirror is an independent ambient field built on the repository's generic
Ableton OSC gesture platform. Twelve fixed-frequency voices form six pairs
reflected about a pivot at 288 Hz that never sounds.

- `spec.py` is the sole authority for the pivot, ratios, frequencies, voice
  groups, levels, pans, sends, envelope, and form length.
- `ARCHITECTURE.md` describes the signal path and the shape of the reflection.
- `scripts/` transforms the specification into Live and validates the result.

## Rebuild

From the repository root, with Live open and both Remote Scripts active:

```sh
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py tracks
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py operators
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py configure
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py effects
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py playable
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py spatial
/usr/bin/python3 projects/radiant_mirror/scripts/breath_radiant_mirror.py
/usr/bin/python3 projects/radiant_mirror/scripts/room_radiant_mirror.py
/usr/bin/python3 projects/radiant_mirror/scripts/theremin_radiant_mirror.py
/usr/bin/python3 projects/radiant_mirror/scripts/validate_radiant_mirror.py
```

Every phase is idempotent and refuses to replace unexpected tracks or devices.
`validate_radiant_mirror.py` reads Live back and changes nothing.

`room_radiant_mirror.py` requires `integrations/abletonosc/return-tracks.patch`;
without it, stock AbletonOSC cannot address a return track at all. It fails with
that instruction rather than guessing.

## Audition

The field opens from its narrowest pair outward:

```sh
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py core
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py golden
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py full
/usr/bin/python3 projects/radiant_mirror/scripts/build_radiant_mirror.py stop
```

`core` stops all clips first. `golden` and `full` layer onto whatever is already
sounding. Attack is 13 seconds, so each phase takes time to arrive.

## Conduct the wanderer

The theremin does not move on its own. One pass is one form — 377 seconds:

```sh
/usr/bin/python3 projects/radiant_mirror/scripts/perform_radiant_mirror.py --fire
```

`--passes N` repeats the circuit, `--stop-when-done` silences the wanderer at the
end and leaves the field sounding. Interrupting it cancels every gesture and
leaves the theremin wherever its glide had reached.

AbletonOSC's reply port is exclusive, so **no other script here can run while the
conductor is conducting** — builders, the validator, and the conductor each hold
that port for their lifetime. Let a pass finish, or stop it, before running
anything else.

## Tests

```sh
/usr/bin/python3 -m unittest discover -s projects/radiant_mirror -t . -p 'test_*.py' -v
```

## Not yet built

The timbral-texture layer that Veil One carries in `texture_*` has no Radiant
Mirror equivalent yet. `Auto Filter` and `Utility` are loaded on every voice at
Live's defaults, reserved for it. Return B's Delay is used as the memory bus but
is left at its own settings — only the room on return A is shaped.

Nothing in `spec.py` describes modulation that Live is not actually performing.
