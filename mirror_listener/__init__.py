"""Project-agnostic musical perception for AI companions."""

from .model import CORE_QUALITIES, FeatureFrame, ListenerFrame, Quality
from .perception import MirrorMusicEar
from .bridge import CompanionBridge, RELATIONAL_MODES, VocabularyProfile
from .session import SessionStore
from .synesthesia import SynestheticMapper
from .api import CompanionState, start_api

__all__ = ["CORE_QUALITIES", "CompanionBridge", "CompanionState", "FeatureFrame", "ListenerFrame",
           "MirrorMusicEar", "Quality", "RELATIONAL_MODES", "SessionStore",
           "SynestheticMapper", "VocabularyProfile", "start_api"]
