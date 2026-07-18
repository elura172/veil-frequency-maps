"""Project-agnostic musical perception for AI companions."""

from .model import CORE_QUALITIES, FeatureFrame, ListenerFrame, Quality
from .perception import MirrorMusicEar

__all__ = ["CORE_QUALITIES", "FeatureFrame", "ListenerFrame", "MirrorMusicEar", "Quality"]
