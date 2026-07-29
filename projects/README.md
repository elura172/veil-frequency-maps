# Ableton projects

Each directory below is an independent composition or Live system. Generic MCP, OSC, and gesture infrastructure must remain outside this directory.

A project should normally contain:

```text
projects/<project_id>/
├── README.md
├── spec.py                 # canonical declarative musical specification
├── ARCHITECTURE.md         # human-readable signal/form description
├── scripts/                # project-specific Live transformations
├── tests/                  # specification and transformation invariants
├── max_for_live/           # editable Max source and packaged snapshots
└── live/                   # optional canonical .als snapshot
```

Project code may import the generic `osc_mcp` package. Generic infrastructure must not import a project package.

To start a new work, copy the shape—not the musical constants—of an existing project. Give it its own `spec.py`, validator, and rebuild sequence.
