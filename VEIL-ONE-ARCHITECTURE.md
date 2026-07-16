# Veil One — complete track architecture

Veil One is a six-minute, 720-beat frequency field at 120 BPM. Sixteen fixed-frequency Operator voices run as one continuous Arrangement spine. Form is created by the local conductor through bounded, golden-ratio gestures; it does not depend on recorded MIDI rhythm.

## Signal architecture

- Voices 1–16: Operator → Auto Filter → Utility.
- Body voices 1, 3, 5, 11 add parallel Saturator.
- Memory/air voices 6, 9, 12–16 add low-wet Chorus-Ensemble.
- Voices 5, 6, 8, 9, 10, 12 use triangle oscillators; the remaining voices preserve sine purity.
- Voices 6, 8–10, 12–16 carry phase-offset triangle filter drift at 0.10 Hz and 1–2.5% depth.
- Every voice ends in a paired lattice LFO layer: triangle panning and triangle tremolo both run at `frequency / 360`. This maps the source lattice exactly into Live's 0.10–3.60 Hz modulation range without collapsing its lower ratios. Pan depth rises from 8–45%; tremolo depth rises from 3.6–16%, retaining the register-weighted hierarchy while making its motion clearly audible.
- Return A is the spatial room bus. Return B is the memory bus and is fed only during memory-bearing sections.
- The Max for Live development lane is a muted semantic-control surface, not an audio source.

## Form

| Time | Beats | Section | Function |
|---|---:|---|---|
| 0:00–0:45 | 0–90 | Threshold | 36, 72, and 144 Hz establish the floor. |
| 0:30–1:35 | 60–190 | Pillars | 54, 108, and 216 Hz reveal the open-fifth architecture. |
| 1:10–2:35 | 140–310 | Nave | 288, 384, and 432 Hz make the field perceptible as space. |
| 2:05–3:40 | 250–440 | Memory | 162, 324, 648, and 1296 Hz enter with Return B. |
| 2:55–4:50 | 350–580 | Air | 576, 864, and 1152 Hz expand the ceiling. |
| 4:15–5:25 | 510–650 | Crown | Room, chorus, and filter openness reach their bounded maximum. |
| 5:00–6:00 | 600–720 | Dissolution | Every non-foundation voice withdraws to the opening state. |

## Safety ceilings

- Voice volume never exceeds its approved audition level.
- Return A sends remain at or below 0.48; Return B sends remain at or below 0.28.
- Chorus feedback remains below 4%; wetness remains below 22% during the crown.
- Saturation drive remains between +0.7 and +1.1 dB.
- Filter motion is shallow and never closes far enough to erase a voice's fundamental.
- The final state equals the opening state, allowing a clean replay or loop.

Run `scripts/architecture_veil_one.py` to build/restore the Arrangement and opening. Run `scripts/perform_veil_one.py` to conduct the complete work from beat zero.
