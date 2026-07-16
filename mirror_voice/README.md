# Mirror Voice Engine

Local-first voice/language fusion for the six Mirror qualities. Input is newline-delimited JSON so any microphone analyzer, transcription system, or live performance process can feed it without coupling the engine to one vendor.

```sh
python3 -m mirror_voice
```

Example event:

```json
{"text":"a warm silver shimmer, gently flowing","acoustic":{"rms":0.32,"pitch_hz":196,"pitch_confidence":0.8,"centroid_hz":1800,"onset_rate":0.2,"speech_rate":0.35,"silence_seconds":0}}
```

The engine prints its fused state and sends individual qualities plus a complete state frame to `127.0.0.1:9000`. Values are normalized, smoothed, and hysteretic.

Use `--no-osc` to inspect or calibrate state output without opening a UDP socket.

For a local LM Studio-compatible `/api/v1/chat` server:

```sh
python3 -m mirror_voice --local-model google/gemma-4-e2b
```

The default endpoint is `http://127.0.0.1:1234/api/v1/chat`; override it with
`--local-url`. Only the final `message` block is parsed, so private reasoning
blocks never enter the musical state.

Optional local semantic enrichment:

```sh
python3 -m mirror_voice --ollama-model gemma3:4b
```

If Ollama is unavailable or returns invalid data, the deterministic fuzzy lexicon remains active and a warning appears in output. No recording or transcript is sent anywhere unless an explicitly configured model provider is added later.

The acoustic inputs are already normalized features. A dedicated microphone/transcription front end is intentionally separate: it may be replaced without changing the musical state model or Max protocol.

An optional live microphone front end is included:

```sh
pip install -e '.[voice]'
python3 -m mirror_voice.capture
```

It measures RMS, pitch/confidence, spectral centroid, onset, activity, and accumulating silence locally, then streams fused states to Mirror Hands. Transcribed text can simultaneously enter through the NDJSON engine; a future frontend may combine the two processes around a chosen local speech-to-text model.
