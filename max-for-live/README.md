# Generic Max for Live integrations

This directory contains project-agnostic Max devices and protocols. Composition-specific patches belong under `projects/<project_id>/max_for_live/`.

The shared packaged implementation is [`Instrument OSC Modulator`](Instrument%20OSC%20Modulator/README.md). Its editable `.maxpat` is authoritative and its `.amxd` is rebuilt deterministically by `scripts/package_amxd.py`.

[`Mirror Listener`](Mirror%20Listener/README.md) is the source-controlled successor to the early UDP 8000 debug listener. It consolidates Mirror and Shimmer analysis messages into smoothed, observable musical state.

## Wavetable OSC Modulator

The planned runtime boundary is documented in [`Wavetable OSC Modulator/PROTOCOL.md`](Wavetable%20OSC%20Modulator/PROTOCOL.md). MCP owns discovery, durable state changes, and musical intentions; Max owns continuous signals and `live.remote~` mappings. No project frequencies or forms belong in this device.

## Operator OSC Modulator

The parallel Operator boundary is documented in [`Operator OSC Modulator/PROTOCOL.md`](Operator%20OSC%20Modulator/PROTOCOL.md). It uses separate ports so both modulation devices can coexist.
