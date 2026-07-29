# Radiant Mirror — architecture

## The reflection

The field has a pivot at **288 Hz** and no voice tuned to it. Every voice is one
half of a pair: a ratio below the pivot and the same ratio above it. The pivot is
audible only as the symmetry the ear infers from its two leaves — a mirror whose
surface is empty.

| Pair | Ratio | Below | Above | Pan |
|---|---|---|---|---|
| I | 9:8 | 256 Hz — Breath below | 324 Hz — Breath above | ∓0.14 |
| II | 3:2 | 192 Hz — Fifth below | 432 Hz — Fifth above | ∓0.28 |
| III | φ | 178 Hz — Golden below | 466 Hz — Golden above | ∓0.42 |
| IV | φ² | 110 Hz — Deep gold | 754 Hz — Bright gold | ∓0.56 |
| V | 4:1 | 72 Hz — Floor | 1152 Hz — Radiance | −0.10 / +0.70 |
| VI | 6:1 | 48 Hz — Abyss | 1728 Hz — Corona | −0.04 / +0.84 |

Frequencies are rounded to the nearest hertz. The golden pairs are irrational and
land at 177.994 / 465.994 and 110.006 / 753.994 Hz; rounding lets Live's Operator
display verify each voice against its own readout instead of against a number
nothing can confirm. The rounding error is under 0.01 Hz, four orders of
magnitude below the slowest beat the pairs produce.

Pairs I–IV are exactly symmetric in pan. Pairs V and VI are not: below about
100 Hz the ear stops localising, so the lower leaf collapses toward centre rather
than claiming a width it cannot deliver. The mirror stays exact in frequency,
level, and gesture; only its image narrows where hearing does.

## Radiance

The upper leaf is always quieter and always wetter than its reflection. Level
falls and room send rises as the pair opens, so height in the field reads as
distance rather than loudness. Only the golden pairs and the corona are given
memory send — the irrational intervals and the two brightest voices are the parts
allowed to persist after they stop.

## Breath

Each voice carries an Auto Pan-Tremolo in tremolo mode, and **both leaves of a
pair share one period, half a cycle apart**. As one leaf swells its reflection
recedes: the mirror made temporal. The period is proportional to the pair's own
ratio — the wider the mirror opens, the slower it breathes.

| Pair | Ratio | Period | Depth below / above |
|---|---|---|---|
| I | 9:8 | 5.63 s | 10% / 12% |
| II | 3:2 | 7.50 s | 13% / 16% |
| III | φ | 8.09 s | 17% / 21% |
| IV | φ² | 13.09 s | 22% / 27% |
| V | 4:1 | 20.00 s | 28% / 34% |
| VI | 6:1 | 30.00 s | 35% / 42% |

The device is driven in free **time** mode, not rate mode, because Live's Auto
Pan bottoms out at 0.10 Hz and four of the six pairs breathe slower than that.
Free time mode spans 0.1 s to 200 s, and stating the breath as a period rather
than a rate is truer to what it is. Tremolo `Phase` is zero so both channels
move together — this is amplitude modulation, not a stereo wobble. The 180°
separation is set through `Offset`.

One honesty: these are free-running LFOs. The spec fixes their periods and their
offset; whether two leaves hold exact antiphase indefinitely depends on Live's
own free-run phase reference, which the API does not expose. The see-saw is what
is configured, not something this project can prove from outside.

## The room

Return A's Reverb is the room every voice sends to, shaped large and slow enough
that a thirty-second breath still blooms inside it: 12 s decay, 25 ms predelay,
100% scale, 80% diffusion, high density, full stereo image, 100% wet.

Its **chorus is switched off**. Live's reverb chorus detunes the tail, and this
field's entire identity is exact frequency ratios — a detuning room would smear
the very intervals the mirror exists to hold. Return B's Delay is the memory the
golden pairs and the corona echo into, left at its own settings.

## Signal path

Each of the twelve tracks carries the same chain:

```
Operator (Osc-A only, fixed frequency, sine) → Auto Filter → Utility → Auto Pan-Tremolo → track → Return A (room) / Return B (memory)
```

Operator runs a single oscillator with fixed-frequency tuning, so MIDI pitch is
irrelevant — every clip holds one note held for the length of the form purely to
gate the envelope. Oscillators B, C, and D are off. `Auto Filter` and `Utility`
sit at Live's defaults, reserved for a timbral layer that does not exist yet.

## The wanderer

A thirteenth track belongs to no pair. It is tuned by Operator's fixed frequency
like the rest of the field, but its frequency is never held — it is glided
between the twelve reflections. Operator's fixed-frequency control is
logarithmic, so interpolating it linearly is a constant-cents portamento: a
theremin's hand, not a keyboard's steps.

```
Operator (Saw 8, fixed frequency) → Auto Filter (band-pass, 700 Hz, Q 0.35) → Erosion → Auto Pan-Tremolo (145 ms, 30%) → Utility
```

The band-pass is **fixed while the pitch moves**, so the harmonics of a
band-limited saw sweep through a standing formant — voices swelling and fading
as the glide passes through the band. Erosion sits above that formant at 1.5 kHz,
35% amount, narrow filter width: the static between stations, riding with the
tone rather than hissing underneath it. That, plus a 6.9 Hz tremolo, is the AM
radio in the room.

Its path crosses the pivot at every step, alternating lower leaf and upper leaf,
visiting all twelve voices exactly once before closing back on its first:

```
256 → 466 → 192 → 754 → 178 → 324 → 110 → 1152 → 72 → 432 → 48 → 1728 → 256
```

Twelve glides, each shaped by a different metallic curve, with Fibonacci glide
and dwell times that sum to **exactly 377 seconds** — one circuit of the mirror
is one form. Its volume follows the field's own falling law: the level at each
waypoint is scaled from the level of the voice it lands on, so the wanderer is
quietest at the corona and loudest at the fifth below.

## Form

At 120 BPM the field is **754 beats — 377 seconds**. Attack is 13 seconds and
release 21 seconds, so no voice has an onset and the field takes roughly half a
minute to fully close after the last clip stops. The audition sequence opens from
the core outward: pairs I–II together, then the golden pairs at 8-second
intervals, then the depths and corona at 6.

## Invariants

`tests/test_spec.py` holds the composition to its own claims: that every voice is
a reflection of the pivot at the declared ratio, that the pivot is silent, that
the upper leaf is always brighter, quieter, and wetter, that only the golden
pairs and corona echo, that the pan mirror is exact wherever the frequency is
localisable, that each pair breathes at one period proportional to its ratio
with its leaves half a cycle apart, that every period is reachable in Live's
free time mode, that the wanderer visits every voice exactly once and crosses
the pivot at every step, that one circuit is exactly one form, and that the
form's beats and seconds agree at the declared tempo.
`scripts/validate_radiant_mirror.py` holds Live to the same spec by reading it
back — voices, breath, room, and wanderer.

## Dependency

The room layer needs `integrations/abletonosc/return-tracks.patch`. Live keeps
return tracks in a list of their own, and stock AbletonOSC's `/live/track/*`
handlers cannot address them, so nothing could read or shape a reverb sitting on
a return. The patch adds the return endpoints inside `TrackHandler.init_api()` —
a module `Manager.reload_imports()` already reloads — so `/live/api/reload`
activates them without restarting Live.
