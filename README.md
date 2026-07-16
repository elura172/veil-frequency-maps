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

- `ableton_ramp`: one track fader, pan, send, device parameter, or the master crossfader
- `ableton_batch_ramp`: coordinated multi-parameter movement
- `ableton_golden_crossfade`: complementary golden-ratio track fades
- `ableton_get_crossfader` / `ableton_set_crossfader`: Live's actual master A/B crossfader
- `ableton_get_crossfade_assignment` / `ableton_assign_crossfade`: read or assign a track to A, neither side, or B
- `ableton_inspect_wavetable`: discover the loaded Wavetable's live parameter surface
- `ableton_set_wavetable_parameter`: resolve and set a parameter by display name
- `ableton_morph_wavetable`: animate a named, multi-parameter Wavetable state as one gesture
- `ableton_inspect_operator`: discover the loaded Operator parameter surface
- `ableton_set_operator_parameter`: resolve and set an Operator parameter by display name
- `ableton_morph_operator`: animate a named, multi-parameter Operator state as one gesture
- `ableton_get_gestures`: inspect scheduled and running gestures
- `ableton_cancel_gesture` / `ableton_cancel_all_gestures`

Durations may be expressed in seconds or beats and starts may be quantized to the next beat or bar. Curves include linear, eased, sine, exponential, logarithmic, Fibonacci steps, and metallic-mean families: `golden`, `golden_in/out`, `silver_in/out`, and `bronze_in/out`. Update rates are capped at 30 Hz so Live handles audio and timing while the MCP layer describes the gesture.

The metallic arrivals use normalized power curves: golden `t^φ`, silver `t^(1+√2)`, and bronze `t^((3+√13)/2)`. Their complementary `*_out` forms reverse the velocity while preserving exact endpoints.

The `master_crossfader` gesture target controls Live's actual crossfader over `-1..1`; it works with single and batch ramps using every supported curve. Unlike the legacy `ableton_golden_crossfade` helper, it does not rewrite track volumes.

Wavetable tools never assume fixed parameter indices. They verify the target device, inventory its names, ranges, and quantization through AbletonOSC, and resolve each requested name at call time. Ambiguous partial names are rejected with their candidate matches. This keeps saved intentions portable across Live updates while still allowing the raw device and OSC tools as escape hatches.

Operator uses the same dynamic contract. This covers its oscillator levels, coarse/fine or fixed-frequency controls, waveforms, envelopes, FM algorithm, feedback, filter, LFO, pitch envelope, spread, transpose, glide, and global controls whenever Live publishes them as `DeviceParameter` objects.

Interpolation domains may be `linear`, `log` (useful for positive frequency/time values), or `db`. In `db` mode the endpoints are specified in decibels and converted to linear amplitude before being sent to Live.

## Composition projects

- [Veil One](projects/veil_one/README.md) — sixteen-voice fixed-frequency field and six-minute golden-ratio form.

See [`projects/README.md`](projects/README.md) for the project contract and how to add a future work without coupling it to Veil One.
