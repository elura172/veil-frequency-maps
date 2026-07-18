from __future__ import annotations

from .model import FeatureFrame, clamp


def _domain(scores: dict[str, float], evidence: list[str], confidence: float) -> dict:
    bounded = {name: max(0.0, float(value)) for name, value in scores.items()}
    total = sum(bounded.values())
    weights = ({name: value / total for name, value in bounded.items()} if total > 1e-9
               else {name: 1.0 / len(bounded) for name in bounded})
    ranked = sorted(weights, key=lambda name: (-weights[name], name))
    margin = weights[ranked[0]] - weights[ranked[1]] if len(ranked) > 1 else weights[ranked[0]]
    return {
        "primary": ranked[0],
        "secondary": ranked[1] if len(ranked) > 1 else None,
        "weights": weights,
        "evidence": evidence,
        "confidence": clamp(confidence * (.55 + margin)),
    }


class SynestheticMapper:
    """Deterministic metaphors with visible evidence and uncertainty."""

    def map(self, q: dict[str, float], f: FeatureFrame, confidence: float) -> dict:
        energy, brightness, warmth = q["energy"], q["brightness"], q["warmth"]
        shimmer, motion, density = q["shimmer"], q["motion"], q["density"]
        weight, space, pulse = q["weight"], q["spaciousness"], q["pulse"]
        tension, coherence, novelty = q["tension"], q["coherence"], q["novelty"]
        active_confidence = confidence * (1.0 - f.silence)

        color = _domain({
            "charcoal": weight + (1 - brightness) * .8,
            "amber": warmth * 1.2 + energy * .35,
            "silver": shimmer * 1.1 + brightness * .65,
            "indigo": space + (1 - warmth) * .55,
            "verdigris": coherence * .65 + novelty * .45,
            "pearl": space * .55 + coherence * .45 + brightness * .35,
        }, ["brightness", "warmth", "shimmer", "weight", "spaciousness"], active_confidence)
        color["luminosity"] = clamp(brightness * .72 + energy * .18 + shimmer * .10)
        color["saturation"] = clamp(novelty * .30 + tension * .25 + energy * .25 + (1 - coherence) * .20)

        texture = _domain({
            "velvet": warmth + (1 - f.flatness) * .45,
            "smoked glass": shimmer + tension * .55,
            "weathered stone": weight + density * .45,
            "fine rain": shimmer * .65 + motion * .55 + space * .35,
            "woven fiber": coherence + pulse * .55,
            "powdered mineral": brightness * .45 + f.flatness * .65,
        }, ["flatness", "warmth", "density", "shimmer", "coherence"], active_confidence)

        temperature = _domain({
            "glacial": brightness * (1 - warmth) + space * .35,
            "rain-cool": (1 - warmth) * .65 + motion * .35,
            "temperate": 1 - abs(warmth - .5) * 1.5,
            "ember-warm": warmth + energy * .35,
            "radiant": warmth * .65 + brightness * .45 + energy * .45,
        }, ["warmth", "brightness", "energy"], active_confidence)
        temperature["value"] = clamp(warmth * .78 + energy * .22)

        direction = _domain({
            "rising outward": brightness * .45 + space * .55 + max(0.0, q.get("motion", 0)),
            "circling": pulse * .65 + motion * .55,
            "descending inward": weight * .65 + (1 - space) * .45,
            "leaning forward": tension * .65 + energy * .45,
            "hovering": coherence * .55 + (1 - motion) * .65,
            "scattering": novelty * .55 + (1 - coherence) * .55 + space * .30,
        }, ["motion", "weight", "spaciousness", "pulse", "tension"], active_confidence)

        element = _domain({
            "earth": weight * .75 + density * .35,
            "water": motion * .60 + warmth * .30 + coherence * .20,
            "air": space * .70 + shimmer * .45 + brightness * .20,
            "fire": energy * .60 + tension * .45 + warmth * .25,
            "aether": space * .45 + shimmer * .40 + coherence * .35 + (1 - density) * .20,
        }, ["weight", "motion", "spaciousness", "energy", "shimmer"], active_confidence)

        weather = _domain({
            "clear high air": brightness + space * .55,
            "silver rain": shimmer * .75 + motion * .55,
            "low fog": density * .55 + weight * .45 + (1 - brightness) * .45,
            "electrical storm": tension * .75 + energy * .55 + novelty * .35,
            "warm dusk": warmth * .70 + (1 - brightness) * .35,
            "slow snowfall": space * .45 + coherence * .45 + (1 - energy) * .50,
        }, ["brightness", "motion", "density", "tension", "energy"], active_confidence)

        landscape = _domain({
            "open valley": space + coherence * .30,
            "mineral shore": brightness * .35 + weight * .45 + motion * .30,
            "dark forest": density * .60 + warmth * .25 + (1 - brightness) * .35,
            "high plateau": brightness * .45 + weight * .35 + space * .55,
            "submerged chamber": weight * .45 + space * .35 + warmth * .20,
            "distant lights": shimmer * .65 + space * .65,
        }, ["spaciousness", "weight", "density", "brightness", "shimmer"], active_confidence)

        scent = _domain({
            "mineral": brightness * .45 + weight * .45,
            "resinous": warmth * .60 + density * .35,
            "floral": shimmer * .40 + coherence * .35 + warmth * .25,
            "saline": space * .40 + motion * .40 + brightness * .25,
            "metallic": brightness * .55 + tension * .45,
            "petrichor": motion * .35 + warmth * .25 + weight * .25 + space * .20,
        }, ["brightness", "warmth", "motion", "weight", "tension"], active_confidence * .82)

        taste = _domain({
            "bitter": tension * .55 + (1 - warmth) * .35,
            "sweet": warmth * .55 + coherence * .35,
            "saline": space * .35 + motion * .30 + weight * .20,
            "smoky": density * .45 + weight * .35 + warmth * .20,
            "bright-acidic": brightness * .55 + novelty * .35 + energy * .25,
        }, ["tension", "warmth", "coherence", "brightness", "novelty"], active_confidence * .72)

        creature = _domain({
            "breathing": coherence * .45 + (1 - pulse) * .30 + motion * .25,
            "gliding": space * .55 + motion * .45 + coherence * .25,
            "trembling": shimmer * .45 + tension * .45 + f.zero_crossing * .25,
            "stalking": weight * .40 + tension * .40 + pulse * .30,
            "flocking": motion * .45 + pulse * .40 + space * .35,
            "sleeping": (1 - energy) * .60 + (1 - motion) * .45,
        }, ["motion", "pulse", "tension", "spaciousness", "zero_crossing"], active_confidence)

        return {
            "color": color, "texture": texture, "temperature": temperature,
            "direction": direction, "element": element, "weather": weather,
            "landscape": landscape, "scent": scent, "taste": taste,
            "creature_motion": creature,
        }
