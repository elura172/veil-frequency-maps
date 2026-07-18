# Repository source of truth

This repository is a project-agnostic Ableton control platform and a collection of independent, reproducible works.

## Authority order

1. `osc_mcp/` — generic Live connectivity, MCP tools, gesture scheduling, curves, and safety limits.
2. `mirror_listener/` — project-agnostic stereo music perception, twelve-quality state, temporal events, and structured output.
3. `mirror_voice/` — human-voice acoustic/semantic fusion and the canonical six-quality modulation field.
4. `tests/` — generic infrastructure tests.
5. `max-for-live/` — generic Max devices and versioned OSC protocols.
6. `projects/<project_id>/spec.py` — canonical musical declaration for one independent work.
7. `projects/<project_id>/scripts/` — deterministic transformations of that specification into Live.
8. `projects/<project_id>/max_for_live/` — editable Max source; packaged `.amxd` files are snapshots.
9. `projects/<project_id>/live/` — optional playable Live snapshots, derived from project source rather than treated as the only definition.
10. Project documentation and shared reference material — human-readable intent.

Backups, caches, Ableton Project Info, collected samples, `.als.als` accidents, and Python bytecode are not source and are ignored.

Generic infrastructure must never import from `projects`. A project may import `osc_mcp` and its own package, but not another work unless an explicit shared library is extracted first.

## Project rebuilds

Each project documents its own rebuild and validation sequence in its README. Builders should be idempotent where Live permits it and refuse destructive replacement of unexpected material.

## Change protocol

1. Change a project's `spec.py` when altering its compositional constants.
2. Change a project transformation only when altering how its concepts are realized in Live.
3. Change `osc_mcp` only for reusable Ableton control or gesture behavior.
4. Rebuild the affected project layer and run both generic and project tests.
5. Save a canonical Live Set only after project validation.
6. Commit source, documentation, Max assets, and intentional snapshots together.

## Tests

```sh
/usr/bin/python3 -m pytest -q
/usr/bin/python3 -m unittest discover -s projects -p 'test_*.py' -v
/usr/bin/python3 -m compileall -q osc_mcp mirror_listener mirror_voice projects
git diff --check
```
