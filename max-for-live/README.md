# Generic Max for Live integrations

This directory contains project-agnostic Max devices and protocols. Composition-specific patches belong under `projects/<project_id>/max_for_live/`.

## Wavetable OSC Modulator

The planned runtime boundary is documented in [`Wavetable OSC Modulator/PROTOCOL.md`](Wavetable%20OSC%20Modulator/PROTOCOL.md). MCP owns discovery, durable state changes, and musical intentions; Max owns continuous signals and `live.remote~` mappings. No project frequencies or forms belong in this device.
