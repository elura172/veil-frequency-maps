import unittest

from scripts.veil_one import (
    AIR,
    CHORUSED_VOICES,
    FIFTHS,
    FOUNDATION,
    LENGTH_BEATS,
    LENGTH_SECONDS,
    LFO_DIVISOR,
    MEMORY,
    MEMORY_SENDS,
    PANS,
    PAN_DEPTH,
    PRESENCE,
    ROOM_SENDS,
    SATURATED_VOICES,
    TEMPO,
    TREM_DEPTH,
    TRIANGLE_VOICES,
    VOICES,
    VOLUMES,
    expected_names,
)


class VeilOneSpecTests(unittest.TestCase):
    def test_parallel_voice_arrays_are_complete(self):
        self.assertEqual(len(VOICES), 16)
        for values in (PANS, VOLUMES, ROOM_SENDS, MEMORY_SENDS, PAN_DEPTH, TREM_DEPTH):
            self.assertEqual(len(values), len(VOICES))
        self.assertEqual(len(expected_names()), len(set(expected_names())))

    def test_form_duration_matches_tempo(self):
        self.assertAlmostEqual(LENGTH_BEATS * 60.0 / TEMPO, LENGTH_SECONDS)

    def test_voice_groups_are_in_range_and_foundation_is_disjoint(self):
        groups = (FOUNDATION, FIFTHS, PRESENCE, MEMORY, AIR, TRIANGLE_VOICES,
                  SATURATED_VOICES, CHORUSED_VOICES)
        for group in groups:
            self.assertEqual(len(group), len(set(group)))
            self.assertTrue(all(0 <= track < len(VOICES) for track in group))
        self.assertTrue(set(FOUNDATION).isdisjoint(FIFTHS))

    def test_lattice_lfo_is_exact_and_bounded(self):
        rates = [frequency / LFO_DIVISOR for frequency, _role in VOICES]
        self.assertEqual(rates[0], 0.1)
        self.assertEqual(rates[-1], 3.6)
        self.assertTrue(all(0.0 <= depth <= 0.45 for depth in PAN_DEPTH))
        self.assertTrue(all(0.0 <= depth <= 0.16 for depth in TREM_DEPTH))

    def test_mix_and_send_safety_bounds(self):
        self.assertTrue(all(0.0 <= value <= 1.0 for value in VOLUMES))
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in PANS))
        self.assertLessEqual(max(ROOM_SENDS), 0.48)
        self.assertLessEqual(max(MEMORY_SENDS), 0.28)


if __name__ == "__main__":
    unittest.main()
