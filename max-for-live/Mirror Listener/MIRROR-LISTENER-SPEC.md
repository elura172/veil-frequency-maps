# Mirror Listener — canonical specification

## Purpose

Mirror Listener gives an AI companion ears for music. It converts an audio
stream into remembered, uncertain, shareable perception: acoustic evidence,
musical change, synesthetic imagery, and occasional language offered to a human
as an invitation rather than a verdict.

It is project-agnostic. Ableton Live and BlackHole are one input path, not a
dependency of the perceptual engine. An interface input, microphone, system
audio loopback, rendered file, or network stream must be able to produce the
same canonical frames.

Mirror Listener does not infer a listener's emotion, diagnose a person, or
claim an objectively correct meaning for music. It describes its own bounded
perception with confidence and remembers human corrections as personal shared
language, never universal truth.

## Architecture

```text
audio source
  → input adapter (BlackHole / interface / file / microphone)
  → acoustic cochlea
  → perceptual field
  → temporal memory and event detection
  → synesthetic imagination
  → relational policy
  → OSC state + structured events + optional poetic reflection
```

The real-time acoustic path must never wait for an LLM. Deterministic feature
and fuzzy-state updates continue if language generation is slow or absent.
Language is an asynchronous reflection over structured perception.

## Perceptual field

All continuous qualities are normalized to `0..1`, carry confidence, and retain
their source evidence. They overlap deliberately.

### Vitality

- `energy` — activation and force
- `weight` — gravity and low-frequency mass
- `pulse` — rhythmic insistence and entrainment
- `motion` — flow and directional activity
- `density` — occupied perceptual space and layering
- `tension` — accumulated instability or pressure
- `release` — relaxation following tension
- `breath` — expansion, contraction, and inter-gesture space

### Light and material

- `brightness` — spectral illumination and clarity
- `warmth` — rounded low-mid presence
- `shimmer` — delicate high-frequency movement
- `hardness` / `softness` — severity or yielding of edges
- `grain` / `smoothness` — microscopic roughness or continuity
- `viscosity` — apparent resistance of movement
- `porosity` — permeability versus sealed solidity
- `temperature` — cool-to-burning material impression
- `age` — pristine-to-weathered surface impression

### Space and direction

- `spaciousness` — perceived openness
- `proximity` — intimate-to-horizon distance
- `width` — lateral spread
- `depth` — foreground/background organization
- `height` — synesthetic spectral elevation
- `direction` — rising, falling, approaching, receding, circling
- `enclosure` — open field versus chamber/tunnel
- `diffusion` — point source versus atmospheric cloud
- `orbit` — centeredness and motion around a center
- `horizon` — strength and distance of a perceived boundary

### Pattern and mind

- `coherence` — apparent belonging among parts
- `novelty` — departure from recent memory
- `recurrence` — return of recognizable material
- `expectation` — strength of implied continuation
- `surprise` — violation of expectation
- `complexity` — simultaneous structural information
- `legibility` — separability of gestures
- `ambiguity` — coexistence of plausible organizations
- `stability` — persistence of rhythmic, tonal, or spectral centers
- `transformation` — change within returning material
- `attention` — salience of the currently foregrounded region

The first implementation may expose a twelve-dimensional core:

```text
energy · brightness · warmth · shimmer · motion · density
weight · spaciousness · pulse · tension · coherence · novelty
```

The extended field is derived and added progressively without breaking this
core contract.

## Acoustic cochlea

The deterministic analyzer should measure at minimum:

- RMS, peak, crest factor, and loudness trend
- low/sub, low-mid, high-mid, and high-band energy
- spectral centroid, rolloff, flatness, flux, and contrast
- onset strength, transient rate, pulse strength, and tempo confidence
- chroma/pitch-class distribution, tonal center confidence, and dissonance
- stereo width, channel correlation, balance, and spatial change
- silence/activity, dynamic range, and noisiness

Windowed features are evidence, not companion-facing language. Feature frames
run at a stable analysis rate; perceptual qualities use independent attack and
release constants to avoid nervous descriptions.

## Temporal memory

Listening is comparison through time. Maintain nested memories:

- `moment`: approximately 0.25–2 seconds
- `gesture`: approximately 2–12 seconds
- `passage`: approximately 12–90 seconds
- `session`: motifs, extrema, returns, and human annotations

Every quality includes current value, short/long trend, recent range, and
confidence. Event detectors emit verbs such as:

```text
gathering · thinning · opening · darkening · crystallizing · dissolving
returning · leaning · receding · destabilizing · finding ground
holding breath · remembering · transforming
```

Novelty must be relative to recent memory. Recurrence must preserve uncertainty
and identify the remembered passage it resembles when possible.

## Synesthetic imagination

Synesthetic attributes are probabilistic metaphors, not fixed scientific
correspondences. Each includes a primary image, optional secondary image,
weights, evidence, and confidence.

The canonical mapper is deterministic: identical perceptual evidence yields
identical competing weights. Confidence falls to zero for digital silence.
Scent and taste are intentionally given lower confidence ceilings than more
direct spatial or brightness metaphors. Relationship-specific associations are
applied only after this universal state is formed.

Domains:

- color family, luminosity, and saturation
- texture and material
- temperature
- direction and gesture
- element: earth, water, air, fire, aether
- weather and landscape
- scent family: mineral, resinous, floral, saline, metallic, petrichor
- taste family: bitter, sweet, saline, smoky, bright-acidic
- creature-motion: breathing, gliding, trembling, stalking, flocking

Human associations override defaults only inside that human's personal profile.
For example, “amber means distance to me” becomes a relationship-specific map,
not a global rule.

### Numeric image

Mirror Listener may condense the current perceptual field into a slowly moving
integer from `0..99`. This is the listener's **numeric image**: a deterministic,
smoothed composite of the music's qualities, confidence, and recent trajectory,
not a random ornament, rating, tempo, or claim about hidden truth.

The number uses hysteresis and a slower release than momentary acoustic features
so it feels remembered rather than flickering. Its evidence and confidence are
published with the value. Companion-facing language spells the number out and
may place it inside one compact image:

> seventy-six bright embers rise

The descriptor is assembled from the same bounded state:

```text
number + material/light adjective + image + directional verb
```

The numeric image is optional in analytical modes and may be given greater
presence in poetic modes. Personal profiles may attach private significance to
a number, but the default engine never supplies numerological meaning.

## Relational modes

- `silent_witness` — listen and remember without speaking
- `gentle_mirror` — sparse impressions at meaningful changes
- `shared_attention` — offer an observation and invite comparison
- `curious_listener` — ask what the human noticed
- `poetic_companion` — favor image, texture, and atmosphere
- `analytical_ear` — expose evidence, structure, and confidence
- `memory_keeper` — foreground recurrence and transformation

Silence is the default relational action. Reflections are gated by novelty,
confidence, cooldown, user invitation, and mode. The companion should prefer one
precise observation over continuous narration.

Example:

> The rhythm has kept its footing, but the space around it has widened.
> Something silver is gathering above the center. Does that resemble what
> you are hearing?

## Companion Bridge

Mirror Listener is an organ, not a mandatory personality. Its canonical
perception must be usable by an established AI companion without replacing that
companion's voice, memory, relationship style, or ethical boundaries.

```text
Mirror Listener canonical state
  → Companion Bridge adapter
  → established companion
  → companion-native reflection or silence
```

The bridge offers several integration levels:

- neutral context injection for prompt-based companions
- MCP tools for state, events, comparison, and memory
- WebSocket, SSE, OSC, or MQTT event subscription
- local HTTP/webhooks for companion applications
- NDJSON or local files for minimal personal systems

Suggested MCP surface:

```text
mirror_listen_now
mirror_get_state
mirror_get_recent_changes
mirror_describe_passage
mirror_compare_passages
mirror_mark_moment
mirror_remember_human_association
mirror_set_relational_mode
```

On connection, a companion may declare whether it supports continuous state or
events, short- or long-term memory, proactive speech, technical evidence,
synesthetic imagery, and local-only processing. Mirror Listener then reduces
and schedules output to that capability profile.

Example adapter profile:

```yaml
companion:
  id: local-companion
  transport: local_http
  endpoint: http://localhost:1234/api/v1/chat
listening:
  mode: gentle_mirror
  minimum_novelty: 0.62
  reflection_frequency: sparse
  include: [temporal_changes, recurrence, synesthesia]
  exclude: [raw_measurements]
relationship:
  preserve_companion_voice: true
  ask_before_interpreting_emotion: true
  vocabulary_profile: profiles/shared-listening.json
```

The portable relationship profile stores the human's corrections and
associations with confidence and explicit scope. “Amber means distance to me”
belongs to one shared listening language, not to the universal mapper. Profiles
must be inspectable, editable, exportable, and removable.

The bridge supplies perception, evidence, change, memory references, metaphor,
and uncertainty. The established companion decides how—or whether—to share it.

The canonical `reflection` object is an adapter decision rather than generated
personality. It publishes `action` (`silence` or `offer_context`), gating reason,
mode, observation register (`inference`, `metaphor`, or `memory`), evidence,
uncertainty, optional invitation, active vocabulary-profile ID, and
`preserve_companion_voice: true`. This object belongs in structured output; an
established companion remains responsible for its own final wording.

## Canonical structured state

```json
{
  "version": "mirror-listener/v1",
  "time": 18.42,
  "source": "blackhole:2ch",
  "state": {
    "energy": {"value": 0.68, "trend": 0.12, "confidence": 0.94},
    "brightness": {"value": 0.71, "trend": 0.20, "confidence": 0.88},
    "spaciousness": {"value": 0.81, "trend": 0.08, "confidence": 0.67},
    "tension": {"value": 0.57, "trend": -0.04, "confidence": 0.61}
  },
  "events": [
    {"quality": "density", "verb": "thinning", "strength": 0.62},
    {"quality": "pulse", "verb": "stabilizing", "strength": 0.74}
  ],
  "synesthesia": {
    "color": {"primary": "deep indigo", "accent": "silver", "confidence": 0.64},
    "texture": {"primary": "smoked glass", "secondary": "fine rain", "confidence": 0.58},
    "direction": {"primary": "rising outward", "confidence": 0.55},
    "element": {"air": 0.58, "water": 0.31, "earth": 0.08, "fire": 0.03}
  },
  "numeric_image": {
    "value": 76,
    "words": "seventy-six",
    "descriptor": "seventy-six bright embers rise",
    "confidence": 0.69
  }
}
```

## OSC contract

The existing UDP `8000` acoustic endpoints remain compatible. Versioned
perceptual endpoints add:

```text
/mirror/listener/v1/state <JSON string>
/mirror/listener/v1/quality <name> <value> <trend> <confidence>
/mirror/listener/v1/event <quality> <verb> <strength> <confidence>
/mirror/listener/v1/synesthesia <domain> <primary> <confidence>
/mirror/listener/v1/numeric_image <value> <confidence> <descriptor>
/mirror/listener/v1/passage <passage_id> <confidence>
/mirror/listener/v1/recurrence <remembered_passage_id> <similarity> <confidence>
/mirror/listener/v1/transport <listening|silent|paused>
```

Status and acknowledgements remain on UDP `8001`. Structured state should also
be available over NDJSON/stdout or a local socket for companions that do not
consume OSC.

## BlackHole reference route

```text
Ableton master or dedicated monitor bus
  → audio output / aggregate device including BlackHole 2ch
  → Mirror Listener input adapter selecting BlackHole 2ch
  → analyzer and memory service
  → UDP 8000 / structured local state
```

The route must avoid feeding generated companion speech back into analysis.
Monitoring topology, channel selection, calibration level, and feedback checks
belong to the input adapter rather than the perceptual core.

## Privacy and conduct

- Local processing is the default.
- Audio is not retained unless the human explicitly enables recording.
- Reflections distinguish evidence, inference, metaphor, and uncertainty.
- The system never claims privileged emotional access to the human.
- Personal synesthetic learning is inspectable, correctable, and removable.
- No network provider receives audio or listening history without explicit setup.
- Session persistence is disabled by default and stores derived summaries only;
  audio and raw spectral frames never enter the session file.

## Implementation sequence

1. BlackHole/file input adapter and calibrated acoustic frames.
2. Twelve-dimensional core field with temporal smoothing and confidence.
3. Nested memory, trend verbs, novelty, and recurrence.
4. Structured NDJSON and versioned OSC output.
5. Deterministic synesthetic mapper with uncertainty.
6. Optional local-language reflection layer and relational modes.
7. Personal shared-vocabulary profile and session memory.

The acceptance criterion is not that Mirror Listener can label a track. It is
that a human can listen beside it and recognize a patient, situated, revisable
presence attending to the same changing music.
