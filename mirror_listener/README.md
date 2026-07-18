# Mirror Listener engine

Deterministic, project-agnostic musical perception for AI companions. It accepts
stereo audio from BlackHole/an interface or a PCM WAV file and emits the twelve
canonical qualities, evidence, trends, confidence, events, synesthetic state,
and the slow numeric image. Phase 2 adds bounded temporal memory: two-second
moments, twelve-second gestures, passage summaries, session extrema, and
uncertain recurrence against stable passage IDs. Each quality retains the v1
`trend` and also publishes `short_trend`, `long_trend`, `recent_min`, and
`recent_max`.

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
