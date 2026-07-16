# Wavetable OSC Modulator protocol

Status: implemented by [`../Instrument OSC Modulator`](../Instrument%20OSC%20Modulator/README.md).

The device receives semantic modulation instructions on UDP `11010` and reports state on UDP `11011`. These ports are intentionally separate from AbletonOSC (`11000/11001`). All addresses are namespaced under `/wavetable-mod/v1`.

## Ownership

- MCP/AbletonOSC discovers Wavetable parameters and performs durable value changes.
- The Max device resolves mappings with `live.path`/`live.object` and drives continuous signals with `live.remote~`.
- A slot must release its target with `id 0` before MCP writes a durable final value.
- The Max device never embeds composition-specific constants.

## Four modulation slots

Each slot is numbered `0..3` and stores a target parameter ID plus its signal generator state.

```text
/wavetable-mod/v1/slot/map       slot track device parameter
/wavetable-mod/v1/slot/unmap     slot
/wavetable-mod/v1/slot/start     slot
/wavetable-mod/v1/slot/stop      slot
/wavetable-mod/v1/slot/set       slot field value
/wavetable-mod/v1/slot/status    slot
/wavetable-mod/v1/all/stop
/wavetable-mod/v1/status
```

Fields for `slot/set`:

- `shape`: `sine`, `triangle`, `saw_up`, `saw_down`, `square`, `sample_hold`, `golden`, `silver`, or `bronze`
- `rate_hz`: positive frequency in Hz
- `sync_beats`: positive beat period; setting it replaces `rate_hz`
- `depth`: normalized bipolar depth `0..1`
- `offset`: normalized center `0..1`
- `phase`: normalized phase `0..1`
- `smoothing_ms`: non-negative transition smoothing
- `polarity`: `bipolar` or `unipolar`

Track, device, and parameter are zero-based Live indices. Before mapping, MCP must resolve the Wavetable parameter by name and confirm its range. Max scales the normalized signal to that range locally.

## Replies

```text
/wavetable-mod/v1/ready          protocol_version slot_count
/wavetable-mod/v1/slot/state     slot mapped running target_id phase value
/wavetable-mod/v1/error          request_address message
```

## Safety

- Clamp normalized output before range scaling.
- Apply at least one signal vector of smoothing after mapping or range changes.
- Stop and unmap a slot when its target disappears.
- Never create Live undo steps at modulation rate.
- On device deletion, release all `live.remote~` targets with `id 0`.

## Intended MCP tools

The packaged device will be paired with `ableton_map_wavetable_modulator`, `ableton_set_wavetable_modulator`, `ableton_get_wavetable_modulators`, and `ableton_release_wavetable_modulator`. These tools should only ship once the `.amxd` acknowledges the protocol, so the MCP does not advertise controls that have no receiver.
