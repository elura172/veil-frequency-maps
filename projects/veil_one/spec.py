"""Canonical declarative specification for Veil One.

All builders, conductors, texture passes, and validators import musical constants
from this module. Change the composition here first, then rebuild and validate Live.
"""

TEMPO = 120.0
LENGTH_BEATS = 720.0
LENGTH_SECONDS = 360.0
FLOOR = 0.01
M4L_HOST = "M4L — Veil Modulator DEV"

VOICES = [
    (36.00, "Sub-foundation"), (54.00, "Open fifth"),
    (72.00, "Foundation"), (108.00, "Fifth anchor"),
    (144.00, "Body"), (162.00, "Gentle second"),
    (216.00, "Fifth shimmer"), (288.00, "Presence"),
    (324.00, "Floating second"), (384.00, "Fourth distance"),
    (432.00, "Anchor tone"), (576.00, "Air"),
    (648.00, "High whisper"), (864.00, "Overtone haze"),
    (1152.00, "Ceiling shimmer"), (1296.00, "Distant bell"),
]

PANS = [0.0, -0.05, 0.06, -0.14, 0.11, -0.22, 0.24, -0.34,
        0.17, 0.38, -0.28, 0.43, -0.49, 0.55, -0.61, 0.47]
VOLUMES = [0.38, 0.32, 0.36, 0.30, 0.32, 0.26, 0.27, 0.25,
           0.22, 0.22, 0.20, 0.18, 0.16, 0.14, 0.12, 0.10]
ROOM_SENDS = [0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.13, 0.15,
              0.17, 0.18, 0.20, 0.23, 0.26, 0.29, 0.32, 0.35]
MEMORY_SENDS = [0.0, 0.0, 0.0, 0.0, 0.0, 0.14, 0.0, 0.0,
                0.18, 0.0, 0.0, 0.0, 0.23, 0.0, 0.0, 0.28]

FOUNDATION = [0, 2, 4]
FIFTHS = [1, 3, 6]
PRESENCE = [7, 9, 10]
MEMORY = [5, 8, 12, 15]
AIR = [11, 13, 14]

TRIANGLE_VOICES = [4, 5, 7, 8, 9, 11]
SATURATED_VOICES = [0, 2, 4, 10]
CHORUSED_VOICES = [5, 8, 11, 12, 13, 14, 15]
DRIFT_VOICES = [5, 7, 8, 9, 11, 12, 13, 14, 15]

LFO_DIVISOR = 360.0
PAN_DEPTH = [0.08, 0.10, 0.11, 0.13, 0.15, 0.17, 0.19, 0.22,
             0.24, 0.27, 0.30, 0.33, 0.36, 0.39, 0.42, 0.45]
TREM_DEPTH = [0.036, 0.040, 0.044, 0.050, 0.056, 0.064, 0.072, 0.080,
              0.088, 0.096, 0.104, 0.114, 0.124, 0.136, 0.148, 0.160]


def expected_names():
    return [
        "V%02d %gHz — %s" % (index, frequency, role)
        for index, (frequency, role) in enumerate(VOICES, 1)
    ]
