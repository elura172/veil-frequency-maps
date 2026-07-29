import numpy as np

from mirror_voice.capture import audio_device
from mirror_voice.engine import MirrorVoiceEngine
from mirror_voice.listen import PhraseSegmenter
from mirror_voice.model import AcousticFrame, SemanticFrame


def test_audio_device_preserves_names_and_converts_indices():
    assert audio_device("2") == 2
    assert audio_device("MacBook Air Microphone") == "MacBook Air Microphone"


def test_phrase_segmenter_keeps_preroll_and_ends_after_quiet():
    segmenter = PhraseSegmenter(100, .1, threshold=.1, endpoint_seconds=.2,
                                min_seconds=.1, preroll_seconds=.1)
    assert segmenter.push(np.zeros(10), 0.0) is None
    assert segmenter.push(np.ones(10), .2) is None
    assert segmenter.push(np.ones(10), .2) is None
    assert segmenter.push(np.zeros(10), 0.0) is None
    phrase = segmenter.push(np.zeros(10), 0.0)
    assert phrase is not None
    assert len(phrase) == 50


def test_phrase_segmenter_ignores_short_noise():
    segmenter = PhraseSegmenter(100, .1, threshold=.1, endpoint_seconds=.1,
                                min_seconds=.5, preroll_seconds=0)
    assert segmenter.push(np.ones(10), .2) is None
    assert segmenter.push(np.zeros(10), 0.0) is None


def test_engine_retains_semantics_across_acoustic_updates():
    semantic = SemanticFrame({
        "energy": .4, "brightness": .8, "warmth": .2,
        "shimmer": .9, "motion": .5, "density": .3,
    }, .75, "test")
    engine = MirrorVoiceEngine(half_life_seconds=.01)
    engine.update(AcousticFrame(rms=.1), semantic=semantic, now=1.0)
    state = engine.update(AcousticFrame(rms=.1), now=2.0)
    assert state.semantic_confidence == .75
    assert engine.semantic.source == "test"
