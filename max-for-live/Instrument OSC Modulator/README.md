# Instrument OSC Modulator

A project-agnostic Max Audio Effect providing four normalized `live.remote~` modulation slots for Wavetable and Operator. The audio path is transparent.

Files:

- `Instrument OSC Modulator.maxpat` — editable source of truth
- `instrument_osc_modulator.js` — OSC, LiveAPI, shape, timing, and safety engine
- `Instrument OSC Modulator.amxd` — deterministically packaged Live device

The device listens for the Wavetable v1 protocol on `11010` and Operator v1 on `11012`; replies are emitted on `11011` and `11013`. It supports Hz and beat-synchronized sine, triangle, saw, square, sample-and-hold, golden, silver, and bronze movement.

Rebuild from the repository root:

```sh
python3 scripts/package_amxd.py \
  "max-for-live/Instrument OSC Modulator/Instrument OSC Modulator.maxpat" \
  "max-for-live/Instrument OSC Modulator/Instrument OSC Modulator.amxd"
```

Load the `.amxd` after the Wavetable or Operator instrument on a track. MCP resolves a named parameter into its zero-based track/device/parameter indices, maps a slot, configures it, and starts it. Stop and unmap before committing a durable parameter value through AbletonOSC.
