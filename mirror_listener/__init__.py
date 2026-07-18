"""Project-agnostic musical perception for AI companions."""

from .model import CORE_QUALITIES, FeatureFrame, ListenerFrame, Quality
from .perception import MirrorMusicEar
from .bridge import CompanionBridge, RELATIONAL_MODES, VocabularyProfile

__all__ = ["CORE_QUALITIES", "CompanionBridge", "FeatureFrame", "ListenerFrame",
           "MirrorMusicEar", "Quality", "RELATIONAL_MODES", "VocabularyProfile"]
