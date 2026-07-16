from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .model import QUALITIES, SemanticFrame, clamp

SYSTEM = """You are the semantic ear of a musical instrument. Return only JSON.
Read the speaker's language as overlapping continuous qualities, never as a diagnosis.
Schema: {"energy":0..1,"brightness":0..1,"warmth":0..1,"shimmer":0..1,"motion":0..1,"density":0..1,"confidence":0..1}
Energy is intensity; brightness is clarity/air; warmth is tenderness/roundness; shimmer is numinous or spectral delicacy; motion is change/flow; density is layering/semantic concentration."""


class OllamaSemanticEar:
    def __init__(self, model: str, url: str = "http://127.0.0.1:11434/api/chat", timeout: float = 8.0):
        self.model, self.url, self.timeout = model, url, timeout

    def analyze(self, text: str) -> SemanticFrame:
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
        }).encode()
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            envelope = json.load(response)
        result = json.loads(envelope["message"]["content"])
        values = {key: clamp(result[key]) for key in QUALITIES}
        return SemanticFrame(values, clamp(result.get("confidence", .7)), "ollama:" + self.model)

