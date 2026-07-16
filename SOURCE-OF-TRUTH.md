# Repository source of truth

This repository is the canonical, reproducible definition of the Veil works and their local Ableton control system.

## Authority order

1. `scripts/veil_one.py` — musical constants: frequencies, roles, groups, levels, sends, duration, texture assignments, and lattice-LFO design.
2. Composition scripts — deterministic transformations of that specification into Live:
   - `build_veil_one.py`: instruments, exact tuning, envelopes, clips, core effects, mix, and sends.
   - `texture_veil_one.py`: triangle voices, filter drift, saturation, and chorus.
   - `lattice_lfo_veil_one.py`: paired pan/tremolo modulation derived from the frequency lattice.
   - `architecture_veil_one.py`: Arrangement spine and canonical opening state.
   - `perform_veil_one.py`: six-minute golden-ratio conductor.
   - `validate_veil_one.py`: read-only conformance check against the specification.
3. `max-for-live/Veil Modulator/Veil Modulator.maxpat` and `veil_modulator.js` — editable Max source. The `.amxd` is its packaged snapshot.
4. `Veil One.als Project/Veil One.als` — convenient canonical Live snapshot. It is versioned, but derived from the source above rather than used as the only definition.
5. `VEIL-ONE-ARCHITECTURE.md` and `veil-frequency-maps.md` — human-readable intent and reference material.

Backups, caches, Ableton Project Info, collected samples, `.als.als` accidents, and Python bytecode are not source and are ignored.

## Canonical rebuild sequence

With Live open and both Remote Scripts active:

```sh
/usr/bin/python3 scripts/build_veil_one.py tracks
/usr/bin/python3 scripts/build_veil_one.py operators
/usr/bin/python3 scripts/build_veil_one.py configure
/usr/bin/python3 scripts/build_veil_one.py effects
/usr/bin/python3 scripts/build_veil_one.py playable
/usr/bin/python3 scripts/build_veil_one.py spatial
/usr/bin/python3 scripts/texture_veil_one.py
/usr/bin/python3 scripts/lattice_lfo_veil_one.py
/usr/bin/python3 scripts/architecture_veil_one.py
/usr/bin/python3 scripts/validate_veil_one.py
```

The early build phases intentionally refuse to replace non-default or unexpected tracks. The architecture phase intentionally refuses to overwrite unexpected Arrangement material.

## Change protocol

1. Change `scripts/veil_one.py` when altering compositional constants.
2. Change a transformation script only when altering how a concept is realized in Live.
3. Rebuild the affected layer.
4. Run `scripts/validate_veil_one.py` and the unit tests.
5. Save the canonical Live Set only after validation.
6. Commit source, documentation, Max assets, and the single canonical `.als` together.

## Tests

```sh
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m py_compile osc_mcp/*.py scripts/*.py
git diff --check
```
