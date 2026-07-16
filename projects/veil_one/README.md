# Veil One

Veil One is an independent composition project built on the repository's generic Ableton OSC gesture platform.

- `spec.py` is the sole authority for frequencies, voice groups, levels, sends, duration, texture assignments, and lattice modulation.
- `ARCHITECTURE.md` describes the signal path and six-minute form.
- `scripts/` transforms the specification into Live and validates the result.
- `max_for_live/` contains editable Max source and its packaged snapshot.
- `live/Veil One.als Project/Veil One.als` is the canonical playable snapshot.

## Rebuild

From the repository root, with Live open and both Remote Scripts active:

```sh
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py tracks
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py operators
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py configure
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py effects
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py playable
/usr/bin/python3 projects/veil_one/scripts/build_veil_one.py spatial
/usr/bin/python3 projects/veil_one/scripts/texture_veil_one.py
/usr/bin/python3 projects/veil_one/scripts/lattice_lfo_veil_one.py
/usr/bin/python3 projects/veil_one/scripts/architecture_veil_one.py
/usr/bin/python3 projects/veil_one/scripts/validate_veil_one.py
```

Conduct the complete form with:

```sh
/usr/bin/python3 projects/veil_one/scripts/perform_veil_one.py
```

Builders refuse to replace unexpected tracks or Arrangement material.
