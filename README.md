# Ableton OSC Gesture MCP

This repository contains a project-agnostic local Ableton MCP/OSC control platform plus isolated composition projects. Start with [SOURCE-OF-TRUTH.md](SOURCE-OF-TRUTH.md).

Generic infrastructure lives in `osc_mcp/`; no composition is allowed to become a dependency of that package. Individual works live under [`projects/`](projects/README.md), each with its own specification, builders, tests, Max assets, and optional Live snapshot.

This project uses two Ableton Live Remote Scripts:

- **AbletonOSC** is the preferred, broad Live Object Model interface over UDP `11000/11001`.
- **AbletonMCP** remains available over TCP `9877` and is used as a fallback for core operations.

The local MCP adapter is launched with:

```sh
cd "/Users/mirrr/Desktop/veil frequency maps"
/usr/bin/python3 -m osc_mcp
```

## Activate in Ableton Live

After saving the current Set, restart Live. In **Settings → Link, Tempo & MIDI**, add or select both control surfaces:

1. `AbletonOSC` with Input and Output set to `None`.
2. `AbletonMCP` with Input and Output set to `None`.

On success, AbletonOSC displays that it is listening on port `11000`; AbletonMCP listens on `9877`.

## Environment overrides

- `ABLETON_OSC_INSTALL`
- `ABLETON_OSC_HOST`, `ABLETON_OSC_PORT`, `ABLETON_OSC_REPLY_PORT`

All defaults target the local installation. The existing TCP bridge stays bound to localhost.

## Local gesture engine

The adapter can schedule smooth OSC gestures without requiring the model to make repeated calls:

- `ableton_ramp`: one track fader, pan, send, or device parameter
- `ableton_batch_ramp`: coordinated multi-parameter movement
- `ableton_golden_crossfade`: complementary golden-ratio track fades
- `ableton_get_gestures`: inspect scheduled and running gestures
- `ableton_cancel_gesture` / `ableton_cancel_all_gestures`

Durations may be expressed in seconds or beats and starts may be quantized to the next beat or bar. Curves include linear, eased, sine, exponential, logarithmic, Fibonacci steps, and `golden`, `golden_in`, and `golden_out`. Update rates are capped at 30 Hz so Live handles audio and timing while the MCP layer describes the gesture.

Interpolation domains may be `linear`, `log` (useful for positive frequency/time values), or `db`. In `db` mode the endpoints are specified in decibels and converted to linear amplitude before being sent to Live.

## Composition projects

- [Veil One](projects/veil_one/README.md) — sixteen-voice fixed-frequency field and six-minute golden-ratio form.

See [`projects/README.md`](projects/README.md) for the project contract and how to add a future work without coupling it to Veil One.
