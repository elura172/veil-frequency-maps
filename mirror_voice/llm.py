from __future__ import annotations

import json
from urllib.request import Request, urlopen

from .model import QUALITIES, SemanticFrame, clamp

SYSTEM = """You are the semantic ear of a musical instrument. Return only JSON.
Read the speaker's language as overlapping continuous qualities, never as a diagnosis.
Schema: {"energy":0..1,"brightness":0..1,"warmth":0..1,"shimmer":0..1,"motion":0..1,"density":0..1,"confidence":0..1}
Energy is intensity; brightness is clarity/air; warmth is tenderness/roundness; shimmer is numinous or spectral delicacy; motion is change/flow; density is layering/semantic concentration."""


def _semantic_frame(result: dict, source: str) -> SemanticFrame:
    values = {key: clamp(result[key]) for key in QUALITIES}
    return SemanticFrame(values, clamp(result.get("confidence", .7)), source)


def _json_object(content: str) -> dict:
    """Accept strict JSON, or recover one object from harmless model framing."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(content[start:end + 1])


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
        result = _json_object(envelope["message"]["content"])
        return _semantic_frame(result, "ollama:" + self.model)


class LocalChatSemanticEar:
    """Semantic ear for LM Studio's local `/api/v1/chat` response format."""

    def __init__(self, model: str, url: str = "http://127.0.0.1:1234/api/v1/chat", timeout: float = 30.0):
        self.model, self.url, self.timeout = model, url, timeout

    def analyze(self, text: str) -> SemanticFrame:
        body = json.dumps({
            "model": self.model,
            "system_prompt": SYSTEM,
            "input": text,
            "reasoning": "on",
            "temperature": 0.1,
            "max_output_tokens": 700,
            "store": False,
        }).encode()
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            envelope = json.load(response)
        messages = [item.get("content", "") for item in envelope.get("output", []) if item.get("type") == "message"]
        if not messages:
            raise ValueError("local chat response contained no message output")
        result = _json_object(messages[-1])
        return _semantic_frame(result, "local-chat:" + self.model)
