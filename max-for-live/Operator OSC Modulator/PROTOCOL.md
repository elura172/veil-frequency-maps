# Operator OSC Modulator protocol

Status: implemented by [`../Instrument OSC Modulator`](../Instrument%20OSC%20Modulator/README.md).

This is the Operator counterpart to the generic Wavetable modulator. It receives on UDP `11012`, reports on `11013`, and uses `/operator-mod/v1`. Separate ports allow both devices to coexist without address collisions.

## Ownership

- MCP/AbletonOSC resolves Operator parameters by current Live display name and performs durable changes.
- Max maps the resolved parameter with `live.path`/`live.object` and drives it continuously through `live.remote~`.
- A slot releases its target with `id 0` before MCP commits a final value.
- No composition-specific frequencies, algorithms, or envelopes are embedded here.

## Four modulation slots

```text
/operator-mod/v1/slot/map       slot track device parameter
/operator-mod/v1/slot/unmap     slot
/operator-mod/v1/slot/start     slot
/operator-mod/v1/slot/stop      slot
/operator-mod/v1/slot/set       slot field value
/operator-mod/v1/slot/status    slot
/operator-mod/v1/all/stop
/operator-mod/v1/status
```

`slot/set` fields are `shape`, `rate_hz`, `sync_beats`, `depth`, `offset`, `phase`, `smoothing_ms`, and `polarity`. Shapes are `sine`, `triangle`, `saw_up`, `saw_down`, `square`, `sample_hold`, `golden`, `silver`, and `bronze`.

Track, device, and parameter indices are zero-based. Max scales normalized signals into the inspected parameter range and treats quantized parameters as control-rate destinations rather than audio-rate signals.

## Replies and safety

```text
/operator-mod/v1/ready          protocol_version slot_count
/operator-mod/v1/slot/state     slot mapped running target_id phase value
/operator-mod/v1/error          request_address message
```

Clamp output, smooth remapping, release missing targets, avoid modulation-rate undo events, and send `id 0` to all `live.remote~` objects when the device is deleted.

The eventual MCP tools will only be exposed after the packaged `.amxd` acknowledges this protocol.
