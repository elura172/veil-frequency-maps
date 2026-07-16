# Veil Modulator — proof-of-concept

This draft is a transparent Max Audio Effect for Ableton Live 12's bundled Max runtime. It exposes four automatable semantic controls:

- **Presence** — intended to control overall voice density and foreground energy.
- **Distance** — intended to coordinate filtering, width, predelay, and room send.
- **Memory** — intended to coordinate the 9/8 voices and filtered echo return.
- **Shimmer** — intended to control upper partials and high-register diffusion.

`Drift Active` adds extremely slow phase-offset movement. `Drift Amount` limits its depth. The engine ticks locally at 20 Hz and applies φ-based smoothing before publishing each value.

## Outputs

Values are available inside Max through:

```text
receive veil.presence
receive veil.distance
receive veil.memory
receive veil.shimmer
```

They are also emitted as OSC messages to `127.0.0.1:12000`:

```text
/veil/presence <0..1>
/veil/distance <0..1>
/veil/memory <0..1>
/veil/shimmer <0..1>
```

## Open and package

1. In Live, add a blank Max Audio Effect.
2. Open it for editing.
3. Open `Veil Modulator.maxpat` in the bundled Max editor.
4. Confirm `veil_modulator.js` resolves from the same folder.
5. Save the device into the User Library as `Veil Modulator.amxd`.

## Next iteration

The proof-of-concept intentionally does not control Live parameters yet. After validation, add four mapping slots based on `live.path`, `live.object`, and `live.remote~`, plus parameter-range scaling and mapping persistence. The MCP adapter can then expose the four semantic controls while Max owns continuous modulation.
