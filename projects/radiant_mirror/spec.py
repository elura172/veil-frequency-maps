"""Canonical declarative specification for Radiant Mirror.

All builders and validators import musical constants from this module. Change the
composition here first, then rebuild and validate Live.

Radiant Mirror is a twelve-voice ambient field built as six frequency pairs
reflected about a silent pivot. The pivot itself never sounds; only its
reflections do. Each pair is a ratio and its reciprocal, rounded to the nearest
hertz so that Live's Operator can be verified against its own display.
"""

import math

TEMPO = 120.0
LENGTH_BEATS = 754.0
LENGTH_SECONDS = 377.0
FLOOR = 0.01

# The axis of reflection. No voice is tuned here.
PIVOT_HZ = 288.0

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Reflection ratios, innermost pair first. Each yields PIVOT_HZ / r and
# PIVOT_HZ * r. Just ratios carry the body; golden ratios carry the shimmer.
RATIOS = [1.125, 1.5, PHI, PHI ** 2, 4.0, 6.0]
RATIO_NAMES = ["9:8", "3:2", "phi", "phi^2", "4:1", "6:1"]

# Voices are ordered pair by pair, lower leaf then upper leaf, so that the
# mirror reads down Live's track list as adjacent reflections.
VOICES = [
    (256.00, "Breath below"), (324.00, "Breath above"),
    (192.00, "Fifth below"), (432.00, "Fifth above"),
    (178.00, "Golden below"), (466.00, "Golden above"),
    (110.00, "Deep gold"), (754.00, "Bright gold"),
    (72.00, "Floor"), (1152.00, "Radiance"),
    (48.00, "Abyss"), (1728.00, "Corona"),
]

LOWER_LEAF = [0, 2, 4, 6, 8, 10]
UPPER_LEAF = [1, 3, 5, 7, 9, 11]

JUST = [0, 1, 2, 3, 8, 9, 10, 11]
GOLDEN = [4, 5, 6, 7]

CORE = [0, 1, 2, 3]
DEPTHS = [8, 10]
CORONA = [9, 11]

# Spatial reflection. Each pair opens symmetrically about centre; the deviation
# widens as the pair moves away from the pivot.
PAIR_DEVIATIONS = [0.14, 0.28, 0.42, 0.56, 0.70, 0.84]

# Below this frequency the ear stops localising, so the lower leaf collapses
# toward centre rather than pretending to a width it cannot deliver. The mirror
# stays exact in frequency, level, and gesture; only its image narrows.
LOCALIZATION_FLOOR_HZ = 100.0

PANS = [-0.14, 0.14, -0.28, 0.28, -0.42, 0.42,
        -0.56, 0.56, -0.10, 0.70, -0.04, 0.84]

VOLUMES = [0.34, 0.33, 0.36, 0.31, 0.35, 0.29,
           0.33, 0.26, 0.30, 0.22, 0.26, 0.18]

# Return A: room. Radiance grows with height, so the upper leaf is wetter.
ROOM_SENDS = [0.10, 0.12, 0.08, 0.15, 0.09, 0.18,
              0.07, 0.24, 0.05, 0.30, 0.04, 0.36]

# Return B: memory. Only the golden pairs and the corona are allowed to echo.
MEMORY_SENDS = [0.0, 0.0, 0.0, 0.0, 0.16, 0.16,
                0.20, 0.20, 0.0, 0.24, 0.0, 0.28]

ATTACK_SECONDS = 13.0
RELEASE_SECONDS = 21.0

# --- Breath: amplitude modulation -------------------------------------------
#
# Every voice carries one Auto Pan-Tremolo in tremolo mode. Both leaves of a
# pair share a period and sit 180 degrees apart, so the pair see-saws: as one
# leaf swells its reflection recedes. The period is proportional to the pair's
# own ratio — the wider the mirror opens, the slower it breathes.
#
# Live's Auto Pan bottoms out at 0.10 Hz in rate mode, so the device runs in
# free time mode, where the period is stated in seconds over 0.1 s to 200 s.

AM_DEVICE = "Auto Pan-Tremolo"
AM_DEVICE_URI = "query:AudioFx#Auto%20Pan-Tremolo"

# What build_radiant_mirror.py guarantees, and what a fully breathing voice is.
VOICE_BASE_CHAIN = ["Operator", "Auto Filter", "Utility"]
VOICE_CHAIN = VOICE_BASE_CHAIN + [AM_DEVICE]
AM_MODE_TREMOLO = 1
AM_TIME_MODE_FREE = 1
AM_WAVEFORM_SINE = 0

AM_PERIOD_BASE_SECONDS = 5.0
AM_PERIODS = [AM_PERIOD_BASE_SECONDS * ratio for ratio in RATIOS]

# Depth grows outward, and the upper leaf always shimmers deeper than the
# reflection that carries it.
AM_DEPTHS = [0.10, 0.12, 0.13, 0.16, 0.17, 0.21,
             0.22, 0.27, 0.28, 0.34, 0.35, 0.42]

# The lower leaf starts at the top of its sine, the upper leaf half a cycle away.
AM_OFFSETS = [0.0, 0.5] * 6

# Live displays free-mode period to three significant figures, so calibration
# cannot be finer than this.
AM_PERIOD_TOLERANCE = 0.03


# --- The wanderer: a theremin between the reflections ------------------------
#
# One voice that belongs to no pair. It is tuned by Operator's fixed frequency
# like the rest of the field, but its frequency is never held — it is glided,
# continuously, between the twelve reflections. Operator's fixed-frequency
# control is logarithmic, so a linear ramp across it is a constant-cents
# portamento: a theremin's hand, not a keyboard's steps.
#
# Its band-pass is fixed while its pitch moves, so the harmonics of a band-
# limited saw sweep through a standing formant. That, plus a fast tremolo and
# Erosion's noise, is the AM-radio in the room.

THEREMIN_NAME = "R13 Theremin — wanderer"
THEREMIN_CHAIN = ["Operator", "Auto Filter", "Erosion", AM_DEVICE, "Utility"]
THEREMIN_EROSION_URI = "query:AudioFx#Erosion"

THEREMIN_WAVE = 6                 # Operator "Saw 8": band-limited, hollow
THEREMIN_FILTER_BANDPASS = 2      # Auto Filter "Band-pass"
THEREMIN_FORMANT_HZ = 700.0
THEREMIN_RESONANCE = 0.35

THEREMIN_AM_PERIOD_SECONDS = 0.145   # about 6.9 Hz — the radio's buzz
THEREMIN_AM_DEPTH = 0.30

# Erosion is the static between stations: narrow-band noise sitting just above
# the formant, so the grit tracks the tone rather than hissing underneath it.
THEREMIN_EROSION_FREQ_HZ = 1500.0
THEREMIN_EROSION_FILTER_WIDTH = 0.45   # raw
THEREMIN_EROSION_AMOUNT = 0.35         # raw; Live shows this as a percentage

THEREMIN_ATTACK_SECONDS = 3.0
THEREMIN_RELEASE_SECONDS = 8.0

THEREMIN_PAN = 0.0
THEREMIN_ROOM_SEND = 0.28
THEREMIN_MEMORY_SEND = 0.22
THEREMIN_BASE_VOLUME = 0.30

# The wander visits every voice exactly once and crosses the pivot at every
# step, alternating lower leaf and upper leaf, before closing back on its first.
THEREMIN_PATH = [0, 5, 2, 7, 4, 1, 6, 9, 8, 3, 10, 11]

# (glide seconds, dwell seconds, curve) for each transition, including the
# closing return to THEREMIN_PATH[0]. Fibonacci terms throughout; the twelve
# steps sum to exactly one form.
THEREMIN_STEPS = [
    (21.0, 8.0, "golden"),
    (13.0, 13.0, "silver_out"),
    (34.0, 5.0, "bronze_in"),
    (8.0, 13.0, "golden_out"),
    (21.0, 13.0, "sine"),
    (13.0, 8.0, "silver_in"),
    (34.0, 8.0, "bronze_out"),
    (8.0, 5.0, "golden_in"),
    (21.0, 21.0, "ease_in_out"),
    (13.0, 5.0, "silver_out"),
    (34.0, 13.0, "bronze_in"),
    (34.0, 11.0, "golden"),
]


def theremin_levels():
    """Track volume at each waypoint, obeying the field's own falling law."""
    loudest = max(VOLUMES)
    return [THEREMIN_BASE_VOLUME * VOLUMES[voice] / loudest for voice in THEREMIN_PATH]


def theremin_form_seconds():
    return sum(glide + dwell for glide, dwell, _curve in THEREMIN_STEPS)


# --- The room ----------------------------------------------------------------
#
# Return A carries the reverb every voice sends to. It is shaped to be large and
# slow enough that a thirty-second breath still blooms inside it, and its chorus
# is switched off: the field's identity is exact ratios, and a detuning room
# would smear the very intervals the mirror exists to hold.

ROOM_RETURN_INDEX = 0
ROOM_RETURN_NAME = "A-Reverb"
ROOM_DEVICE = "Reverb"

ROOM_PREDELAY_MS = 25.0
ROOM_DECAY_SECONDS = 12.0
ROOM_DIFFUSION_PERCENT = 80.0
ROOM_SCALE_PERCENT = 100.0
ROOM_INPUT_FREQ_HZ = 500.0
ROOM_HIGH_SHELF_HZ = 8000.0

# Raw parameter values, not display units.
ROOM_HIGH_SHELF_GAIN = 0.5
ROOM_SIZE = 1.0
ROOM_STEREO_IMAGE = 1.0
ROOM_DRY_WET = 1.0
ROOM_CHORUS_ON = 0.0
ROOM_FREEZE_ON = 0.0

# Live shows reverb times and percentages to three significant figures.
ROOM_TOLERANCE = 0.04

MEMORY_RETURN_INDEX = 1
MEMORY_RETURN_NAME = "B-Delay"


def pair_frequencies(ratio):
    """Return the (lower, upper) hertz pair reflected about the pivot."""
    return round(PIVOT_HZ / ratio), round(PIVOT_HZ * ratio)


def expected_names():
    return [
        "R%02d %gHz — %s" % (index, frequency, role)
        for index, (frequency, role) in enumerate(VOICES, 1)
    ]
