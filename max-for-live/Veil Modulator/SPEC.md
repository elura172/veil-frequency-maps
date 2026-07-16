# Veil Modulator specification

## Design boundary

The LLM chooses intent and large-scale form. The OSC scheduler handles seconds-to-minutes transitions. Veil Modulator owns continuous modulation inside Live.

## Version 0.1 acceptance criteria

- Transparent stereo audio path.
- Four Live-automatable semantic controls.
- Deterministic phase-offset drift at 20 Hz.
- Golden-shaped smoothing with no discontinuities.
- Drift bypass and bounded depth.
- Named Max sends for local patch integration.
- Localhost OSC output for diagnostics and MCP state mirroring.
- No external network traffic or telemetry.

## Planned mapping semantics

| Control | Primary destinations |
|---|---|
| Presence | voice gains, filter openness, harmonic density |
| Distance | low-pass cutoff, stereo width, room send, predelay |
| Memory | 9/8 voice gains, echo feedback, echo filtering |
| Shimmer | upper partial levels, diffusion, high-frequency return |

All destination mappings require explicit min/max bounds, smoothing, and a per-mapping polarity control. Feedback, resonance, master gain, and return feedback must have hard safety ceilings.
