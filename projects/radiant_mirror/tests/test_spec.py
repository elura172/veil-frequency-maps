import unittest

from projects.radiant_mirror.spec import (
    AM_DEPTHS,
    AM_MODE_TREMOLO,
    AM_OFFSETS,
    AM_PERIOD_BASE_SECONDS,
    AM_PERIODS,
    ATTACK_SECONDS,
    CORE,
    CORONA,
    DEPTHS,
    GOLDEN,
    JUST,
    LENGTH_BEATS,
    LENGTH_SECONDS,
    LOCALIZATION_FLOOR_HZ,
    LOWER_LEAF,
    MEMORY_SENDS,
    PAIR_DEVIATIONS,
    PANS,
    PIVOT_HZ,
    RATIOS,
    RATIO_NAMES,
    RELEASE_SECONDS,
    ROOM_DECAY_SECONDS,
    ROOM_DRY_WET,
    ROOM_PREDELAY_MS,
    ROOM_RETURN_INDEX,
    ROOM_SENDS,
    TEMPO,
    THEREMIN_AM_PERIOD_SECONDS,
    THEREMIN_BASE_VOLUME,
    THEREMIN_CHAIN,
    THEREMIN_PATH,
    THEREMIN_STEPS,
    UPPER_LEAF,
    VOICES,
    VOLUMES,
    expected_names,
    pair_frequencies,
    theremin_form_seconds,
    theremin_levels,
)


class RadiantMirrorSpecTests(unittest.TestCase):
    def test_parallel_voice_arrays_are_complete(self):
        self.assertEqual(len(VOICES), 12)
        for values in (PANS, VOLUMES, ROOM_SENDS, MEMORY_SENDS):
            self.assertEqual(len(values), len(VOICES))
        self.assertEqual(len(expected_names()), len(set(expected_names())))

    def test_form_duration_matches_tempo(self):
        self.assertAlmostEqual(LENGTH_BEATS * 60.0 / TEMPO, LENGTH_SECONDS)

    def test_field_is_six_pairs_reflected_about_a_silent_pivot(self):
        self.assertEqual(len(RATIOS), 6)
        self.assertEqual(len(RATIO_NAMES), len(RATIOS))
        self.assertEqual(len(PAIR_DEVIATIONS), len(RATIOS))
        self.assertEqual(LOWER_LEAF, list(range(0, len(VOICES), 2)))
        self.assertEqual(UPPER_LEAF, list(range(1, len(VOICES), 2)))
        frequencies = [frequency for frequency, _role in VOICES]
        self.assertNotIn(PIVOT_HZ, frequencies)
        for pair, ratio in enumerate(RATIOS):
            lower, upper = pair_frequencies(ratio)
            self.assertEqual(frequencies[LOWER_LEAF[pair]], lower)
            self.assertEqual(frequencies[UPPER_LEAF[pair]], upper)
            self.assertGreater(ratio, 1.0)

    def test_every_voice_is_tunable_by_operator_fixed_frequency(self):
        for frequency, _role in VOICES:
            self.assertGreaterEqual(frequency, 10.0)
            self.assertLessEqual(frequency, 2000.0)

    def test_spatial_reflection_is_exact_where_the_ear_can_localise(self):
        for pair, deviation in enumerate(PAIR_DEVIATIONS):
            lower_index, upper_index = LOWER_LEAF[pair], UPPER_LEAF[pair]
            self.assertAlmostEqual(PANS[upper_index], deviation)
            lower_frequency = VOICES[lower_index][0]
            if lower_frequency >= LOCALIZATION_FLOOR_HZ:
                self.assertAlmostEqual(PANS[lower_index], -deviation)
            else:
                self.assertLess(abs(PANS[lower_index]), deviation)
                self.assertLess(PANS[lower_index], 0.0)

    def test_voice_groups_are_in_range_and_leaves_are_disjoint(self):
        groups = (LOWER_LEAF, UPPER_LEAF, JUST, GOLDEN, CORE, DEPTHS, CORONA)
        for group in groups:
            self.assertEqual(len(group), len(set(group)))
            self.assertTrue(all(0 <= track < len(VOICES) for track in group))
        self.assertTrue(set(LOWER_LEAF).isdisjoint(UPPER_LEAF))
        self.assertTrue(set(JUST).isdisjoint(GOLDEN))
        self.assertEqual(sorted(JUST + GOLDEN), list(range(len(VOICES))))

    def test_upper_leaf_is_brighter_and_quieter_than_its_reflection(self):
        for lower_index, upper_index in zip(LOWER_LEAF, UPPER_LEAF):
            self.assertGreater(VOICES[upper_index][0], VOICES[lower_index][0])
            self.assertLess(VOLUMES[upper_index], VOLUMES[lower_index])
            self.assertGreater(ROOM_SENDS[upper_index], ROOM_SENDS[lower_index])

    def test_only_golden_pairs_and_corona_are_allowed_to_echo(self):
        echoing = {index for index, value in enumerate(MEMORY_SENDS) if value > 0.0}
        self.assertEqual(echoing, set(GOLDEN) | set(CORONA))

    def test_mix_and_send_safety_bounds(self):
        self.assertTrue(all(0.0 <= value <= 1.0 for value in VOLUMES))
        self.assertTrue(all(-1.0 <= value <= 1.0 for value in PANS))
        self.assertLessEqual(max(ROOM_SENDS), 0.48)
        self.assertLessEqual(max(MEMORY_SENDS), 0.28)

    def test_envelope_is_slower_than_any_transient_and_releases_longer(self):
        self.assertGreaterEqual(ATTACK_SECONDS, 5.0)
        self.assertGreater(RELEASE_SECONDS, ATTACK_SECONDS)
        self.assertLess(ATTACK_SECONDS + RELEASE_SECONDS, LENGTH_SECONDS)


class RadiantMirrorBreathTests(unittest.TestCase):
    def test_a_pair_breathes_at_one_period_proportional_to_its_ratio(self):
        self.assertEqual(len(AM_PERIODS), len(RATIOS))
        for pair, ratio in enumerate(RATIOS):
            self.assertAlmostEqual(AM_PERIODS[pair], AM_PERIOD_BASE_SECONDS * ratio)
        self.assertEqual(AM_PERIODS, sorted(AM_PERIODS))

    def test_every_period_is_reachable_in_live_free_time_mode(self):
        # Auto Pan-Tremolo bottoms out at 0.10 Hz in rate mode; free time mode
        # spans 0.1 s to 200 s, which is why the spec states periods at all.
        for period in AM_PERIODS + [THEREMIN_AM_PERIOD_SECONDS]:
            self.assertGreaterEqual(period, 0.1)
            self.assertLessEqual(period, 200.0)

    def test_the_leaves_of_a_pair_are_half_a_cycle_apart(self):
        self.assertEqual(len(AM_OFFSETS), len(VOICES))
        self.assertEqual(AM_MODE_TREMOLO, 1)
        for lower, upper in zip(LOWER_LEAF, UPPER_LEAF):
            self.assertEqual(AM_OFFSETS[lower], 0.0)
            self.assertEqual(AM_OFFSETS[upper], 0.5)

    def test_breath_depth_grows_outward_and_stays_musical(self):
        self.assertEqual(len(AM_DEPTHS), len(VOICES))
        self.assertEqual(AM_DEPTHS, sorted(AM_DEPTHS))
        self.assertLessEqual(max(AM_DEPTHS), 0.45)
        self.assertGreater(min(AM_DEPTHS), 0.0)
        for lower, upper in zip(LOWER_LEAF, UPPER_LEAF):
            self.assertGreater(AM_DEPTHS[upper], AM_DEPTHS[lower])


class RadiantMirrorRoomTests(unittest.TestCase):
    def test_the_room_is_fully_wet_because_it_lives_on_a_return(self):
        self.assertEqual(ROOM_DRY_WET, 1.0)
        self.assertEqual(ROOM_RETURN_INDEX, 0)

    def test_the_room_outlasts_the_slowest_breath(self):
        self.assertGreater(ROOM_DECAY_SECONDS, RELEASE_SECONDS / 2.0)
        self.assertGreater(ROOM_PREDELAY_MS, 0.0)
        self.assertLess(ROOM_DECAY_SECONDS, LENGTH_SECONDS)


class RadiantMirrorWandererTests(unittest.TestCase):
    def test_the_wanderer_visits_every_voice_exactly_once(self):
        self.assertEqual(sorted(THEREMIN_PATH), list(range(len(VOICES))))

    def test_every_step_crosses_the_pivot(self):
        closed = THEREMIN_PATH + [THEREMIN_PATH[0]]
        for here, there in zip(closed, closed[1:]):
            self.assertNotEqual(here in LOWER_LEAF, there in LOWER_LEAF)

    def test_one_circuit_is_exactly_one_form(self):
        self.assertEqual(len(THEREMIN_STEPS), len(THEREMIN_PATH))
        self.assertAlmostEqual(theremin_form_seconds(), LENGTH_SECONDS)
        for glide, dwell, _curve in THEREMIN_STEPS:
            self.assertGreater(glide, 0.0)
            self.assertGreaterEqual(dwell, 0.0)

    def test_the_wanderer_obeys_the_field_falling_law(self):
        levels = theremin_levels()
        self.assertEqual(len(levels), len(THEREMIN_PATH))
        self.assertLessEqual(max(levels), THEREMIN_BASE_VOLUME)
        self.assertGreater(min(levels), 0.0)
        loudest = THEREMIN_PATH[levels.index(max(levels))]
        quietest = THEREMIN_PATH[levels.index(min(levels))]
        self.assertEqual(VOLUMES[loudest], max(VOLUMES[v] for v in THEREMIN_PATH))
        self.assertEqual(VOLUMES[quietest], min(VOLUMES[v] for v in THEREMIN_PATH))

    def test_the_wanderer_carries_the_radio_chain_in_order(self):
        self.assertEqual(THEREMIN_CHAIN[0], "Operator")
        self.assertEqual(THEREMIN_CHAIN[-1], "Utility")
        self.assertIn("Auto Filter", THEREMIN_CHAIN)
        self.assertIn("Erosion", THEREMIN_CHAIN)
        self.assertEqual(len(THEREMIN_CHAIN), len(set(THEREMIN_CHAIN)))


if __name__ == "__main__":
    unittest.main()
