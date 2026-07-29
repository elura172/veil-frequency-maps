# Mirror Voice canonical seed

Mirror Voice is a voice-mediated semantic instrument. It does not classify a speaker into one emotion and it does not merely turn pitch into notes. Acoustic listening and linguistic listening overlap as six continuous qualities:

```text
energy · brightness · warmth · shimmer · motion · density
```

The Python engine fuses voice measurements, words, cadence, and silence into normalized fuzzy weights. It sends them to UDP `9000`:

```text
/mirror/voice/energy <0..1>
/mirror/voice/brightness <0..1>
/mirror/voice/warmth <0..1>
/mirror/voice/shimmer <0..1>
/mirror/voice/motion <0..1>
/mirror/voice/density <0..1>
/mirror/voice/state <six values in canonical order>
/mirror/voice/silence <0..1>
```

Max is the nervous system and hands. It adds smoothing, inertia, mapping, range shaping, and `live.remote~` ownership. Ableton is the reflected body. Silence lowers motion and density while retaining warmth and shimmer; it is never treated as missing data.

The local lexicon is deterministic and overlapping. `mirror-voice --ollama-model <name>` enables a local Ollama semantic ear; malformed output, timeout, or model absence falls back to the local lexicon and reports a warning without stopping the instrument.
