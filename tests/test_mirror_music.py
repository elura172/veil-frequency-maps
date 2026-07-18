import math

import numpy as np

from mirror_listener.features import analyze_stereo
from mirror_listener.language import number_words, poetic_descriptor
from mirror_listener.memory import TemporalMemory
from mirror_listener.model import CORE_QUALITIES
from mirror_listener.output import osc_message
from mirror_listener.perception import MirrorMusicEar


RATE = 16000
N = 4000
TIME = np.arange(N) / RATE


def frame_for(audio, previous=None, previous_rms=0.0):
    return analyze_stereo(np.asarray(audio, dtype=np.float32), RATE, previous, previous_rms)[0]


def test_stereo_cochlea_distinguishes_weight_and_width():
    low = .25 * np.sin(2 * np.pi * 55 * TIME)
    low_frame = frame_for(np.column_stack([low, low]))
    high_left = .16 * np.sin(2 * np.pi * 5000 * TIME)
    high_right = .16 * np.sin(2 * np.pi * 5000 * TIME + np.pi / 2)
    high_frame = frame_for(np.column_stack([high_left, high_right]))
    assert low_frame.sub + low_frame.low > high_frame.sub + high_frame.low
    assert high_frame.centroid > low_frame.centroid
    assert high_frame.width > low_frame.width


def test_twelve_quality_field_is_bounded_and_evidence_backed():
    tone = .2 * np.sin(2 * np.pi * 220 * TIME)
    features = frame_for(np.column_stack([tone, tone]))
    result = MirrorMusicEar("test").update(features, 0.0)
    assert set(result.state) == set(CORE_QUALITIES)
    assert all(0 <= quality.value <= 1 for quality in result.state.values())
    assert all(0 <= quality.confidence <= 1 for quality in result.state.values())
    assert result.source == "test"


def test_bright_wide_audio_maps_brighter_and_more_spacious_than_low_mono():
    low = .24 * np.sin(2 * np.pi * 60 * TIME)
    bright_left = .18 * np.sin(2 * np.pi * 4200 * TIME)
    bright_right = .18 * np.sin(2 * np.pi * 5100 * TIME)
    low_result = MirrorMusicEar().update(frame_for(np.column_stack([low, low])), 0.0)
    bright_result = MirrorMusicEar().update(frame_for(np.column_stack([bright_left, bright_right])), 0.0)
    assert bright_result.state["brightness"].value > low_result.state["brightness"].value
    assert bright_result.state["spaciousness"].value > low_result.state["spaciousness"].value
    assert low_result.state["weight"].value > bright_result.state["weight"].value


def test_numeric_image_is_deterministic_and_spoken():
    tone = .22 * np.sin(2 * np.pi * 880 * TIME)
    features = frame_for(np.column_stack([tone, tone]))
    first = MirrorMusicEar().update(features, 0.0).numeric_image
    second = MirrorMusicEar().update(features, 0.0).numeric_image
    assert first == second
    assert first.words == number_words(first.value)
    assert first.descriptor.startswith(first.words + " ")
    assert len(first.descriptor.split()) == 4


def test_descriptor_can_form_seventy_six_bright_embers_rise():
    qualities = {name: .1 for name in CORE_QUALITIES}
    qualities.update(energy=.9, brightness=.95, warmth=.8, motion=.9)
    assert poetic_descriptor(76, qualities) == "seventy-six bright embers rise"


def test_compact_osc_packet_encodes_numeric_image():
    packet = osc_message("/mirror/listener/v1/numeric_image", [76, .7, "seventy-six bright embers rise"])
    assert packet.startswith(b"/mirror/listener/v1/numeric_image")
    assert b"seventy-six bright embers rise" in packet


def test_digital_silence_does_not_invent_perception():
    features = frame_for(np.zeros((N, 2), dtype=np.float32))
    result = MirrorMusicEar().update(features, 0.0)

    assert features.centroid_hz == 0.0
    assert all(quality.value == 0.0 for quality in result.state.values())
    assert all(quality.confidence == 0.0 for quality in result.state.values())
    assert result.events == []
    assert result.numeric_image.value == 0


def test_quality_state_includes_nested_temporal_evidence():
    tone = .2 * np.sin(2 * np.pi * 440 * TIME)
    ear = MirrorMusicEar()
    ear.update(frame_for(np.column_stack([tone, tone])), 0.0)
    result = ear.update(frame_for(np.column_stack([tone * .5, tone * .5])), 1.0)

    brightness = result.state["brightness"]
    assert brightness.recent_min <= brightness.value <= brightness.recent_max
    assert -1.0 <= brightness.short_trend <= 1.0
    assert -1.0 <= brightness.long_trend <= 1.0
    assert set(result.memory) == {"moment", "gesture", "passage", "session", "recurrence"}


def test_passage_recurrence_has_stable_remembered_id_and_uncertainty():
    memory = TemporalMemory(passage_seconds=2.0)
    state = {name: .25 for name in CORE_QUALITIES}
    emitted = []
    for now in (0.0, 1.0, 2.0, 3.0, 4.0):
        _, events = memory.update(now, state, .8)
        emitted.extend(events)

    recurrence = [event for event in emitted if event["type"] == "recurrence"]
    assert recurrence[0]["passage_id"] == "passage-0001"
    assert recurrence[0]["similarity"] == 1.0
    assert 0.0 < recurrence[0]["confidence"] <= .8
    assert memory.passages[-1]["id"] == "passage-0002"
