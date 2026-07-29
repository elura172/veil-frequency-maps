import math
import struct
import unittest

from mirror_voice.engine import MirrorVoiceEngine, acoustic_qualities
from mirror_voice.lexicon import analyze_text
from mirror_voice.model import AcousticFrame, QUALITIES
from mirror_voice.osc import encode_message

try:
    import numpy as np
except ImportError:
    np = None


class MirrorVoiceTests(unittest.TestCase):
    def test_lexicon_is_fuzzy_and_overlapping(self):
        frame = analyze_text("a warm silver shimmer, gently alive and flowing")
        self.assertGreater(frame.values["warmth"], 0.5)
        self.assertGreater(frame.values["shimmer"], 0.5)
        self.assertGreater(frame.values["motion"], 0.5)
        self.assertGreater(frame.confidence, 0)

    def test_acoustic_features_map_to_all_six_qualities(self):
        values = acoustic_qualities(AcousticFrame(rms=.7, pitch_hz=440, pitch_confidence=.9, centroid_hz=4000, onset_rate=.6, speech_rate=.5))
        self.assertEqual(set(values), set(QUALITIES))
        self.assertTrue(all(0 <= value <= 1 for value in values.values()))
        self.assertGreater(values["brightness"], values["warmth"])

    def test_silence_is_presence_not_zero(self):
        engine = MirrorVoiceEngine(half_life_seconds=.1)
        engine.state.updated_at = 0
        state = engine.update(AcousticFrame(silence_seconds=8), "", now=1)
        self.assertGreater(state.silence_presence, .7)
        self.assertGreater(state.values["warmth"], state.values["motion"])
        self.assertGreater(state.values["shimmer"], 0)

    def test_smoothing_prevents_instant_jump(self):
        engine = MirrorVoiceEngine(half_life_seconds=1)
        engine.update(AcousticFrame(), "still", now=0)
        state = engine.update(AcousticFrame(rms=1, onset_rate=1, speech_rate=1), "intense fire urgent", now=1)
        self.assertLess(state.values["energy"], 1)
        self.assertGreater(state.values["energy"], 0)

    def test_osc_encoding(self):
        packet = encode_message("/mirror/voice/energy", [0.5])
        self.assertIn(b"/mirror/voice/energy\0", packet)
        self.assertIn(b",f\0", packet)
        self.assertTrue(math.isclose(struct.unpack(">f", packet[-4:])[0], .5))

    @unittest.skipIf(np is None, "numpy microphone extra not installed")
    def test_microphone_analyzer_finds_sine_pitch(self):
        from mirror_voice.capture import analyze
        rate = 8000
        samples = .2 * np.sin(2 * np.pi * 200 * np.arange(800) / rate)
        frame = analyze(samples, rate)
        self.assertAlmostEqual(frame.pitch_hz, 200, delta=8)
        self.assertGreater(frame.pitch_confidence, .5)


if __name__ == "__main__":
    unittest.main()
