# Mirror Listener engine

Deterministic, project-agnostic musical perception for AI companions. It accepts
stereo audio from BlackHole/an interface or a PCM WAV file and emits the twelve
canonical qualities, evidence, trends, confidence, events, synesthetic state,
and the slow numeric image. Phase 2 adds bounded temporal memory: two-second
moments, twelve-second gestures, passage summaries, session extrema, and
uncertain recurrence against stable passage IDs. Each quality retains the v1
`trend` and also publishes `short_trend`, `long_trend`, `recent_min`, and
`recent_max`.

The deterministic synesthetic mapper reflects ten explicitly metaphorical
domains: color (with luminosity and saturation), texture, temperature,
direction, element, weather, landscape, scent, taste, and creature-motion.
Every domain publishes a primary and secondary image, normalized competing
weights, acoustic/perceptual evidence labels, and confidence. Silence produces
zero metaphor confidence; personal vocabulary is applied later by the bridge.

BlackHole or interface input:

```sh
python3 -m mirror_listener --device "BlackHole 2ch"
```

Deterministic offline inspection:

```sh
python3 -m mirror_listener --file music.wav --no-osc
```

NDJSON is written to stdout. Compact OSC is sent to UDP `8000`; complete JSON is
not placed in one UDP packet. Passage and return events use
`/mirror/listener/v1/passage` and `/mirror/listener/v1/recurrence`. No LLM is
used by the real-time perception path.

## Companion Bridge

The bridge supplies structured context without replacing an established
companion's personality. Silence remains the default:

```sh
python3 -m mirror_listener --device "BlackHole 2ch" --mode gentle_mirror
```

Modes are `silent_witness`, `gentle_mirror`, `shared_attention`,
`curious_listener`, `poetic_companion`, `analytical_ear`, and `memory_keeper`.
Confidence, novelty, meaningful events, recurrence, and a per-mode cooldown gate
all unsolicited reflections. `--invited` records that the human has invited
reflection for this run.

An optional, inspectable JSON profile can adapt vocabulary without changing the
canonical perceptual mapping:

```json
{
  "id": "shared-listening",
  "associations": {"amber": "distance"},
  "notes": [{"association": "amber means distance", "scope": "this relationship"}]
}
```

Copy [`profiles/shared-listening.example.json`](profiles/shared-listening.example.json)
and pass the edited file with `--profile`. Profiles are plain
files: editable, exportable, and removable. They never trigger network access.

## Optional session memory

Persistence is off by default. To let passage memories and human annotations
survive restarts, explicitly provide a local file:

```sh
python3 -m mirror_listener --device "BlackHole 2ch" \
  --mode memory_keeper --session-file ~/.mirror-listener/our-session.json
```

Writes are atomic. The versioned file contains only derived passage-quality
summaries, extrema, and deliberately added annotations—never audio, FFT data,
or raw acoustic frames. Delete the file to remove the memory. Integrations can
call `ear.memory.mark_moment(time, label, note)` before saving to attach a
human-named moment to the current derived state.
