from __future__ import annotations

import re

from .model import QUALITIES, SemanticFrame, clamp

# Overlapping weights are intentional: language can be warm and bright at once.
LEXICON = {
    "energy": {"fire": .8, "urgent": .9, "strong": .75, "alive": .7, "pulse": .65, "intense": .9, "soft": -.35, "still": -.45, "tired": -.55},
    "brightness": {"bright": .9, "light": .65, "clear": .75, "silver": .7, "air": .55, "open": .45, "dark": -.65, "shadow": -.45, "deep": -.25},
    "warmth": {"warm": .9, "love": .8, "tender": .8, "heart": .65, "gentle": .7, "hold": .45, "cold": -.8, "distant": -.55, "sharp": -.35},
    "shimmer": {"shimmer": 1., "glow": .75, "sparkle": .85, "star": .6, "dream": .6, "veil": .5, "crystal": .75, "plain": -.35, "dry": -.45},
    "motion": {"move": .7, "spiral": .9, "flow": .75, "dance": .85, "drift": .55, "tremble": .65, "return": .5, "still": -.8, "rest": -.55, "stop": -.8},
    "density": {"dense": .9, "many": .65, "layer": .75, "thick": .75, "full": .55, "weave": .6, "single": -.5, "empty": -.75, "space": -.45, "silence": -.55},
}


def analyze_text(text: str) -> SemanticFrame:
    tokens = re.findall(r"[a-z']+", text.casefold())
    values = {}
    hits = 0
    for quality in QUALITIES:
        score, count = 0.0, 0
        weights = LEXICON[quality]
        for token in tokens:
            for root, weight in weights.items():
                if token == root or token.startswith(root):
                    score += weight
                    count += 1
        hits += count
        values[quality] = clamp(0.5 + (score / max(2.0, count * 1.5))) if count else 0.5
    punctuation_energy = min(0.18, (text.count("!") + text.count("?") * 0.5) * 0.04)
    values["energy"] = clamp(values["energy"] + punctuation_energy)
    confidence = min(1.0, hits / 8.0 + min(len(tokens), 40) / 160.0)
    return SemanticFrame(values, confidence, "local_lexicon")

