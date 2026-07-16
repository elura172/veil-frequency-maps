import io
import json
from unittest.mock import patch

from mirror_voice.llm import LocalChatSemanticEar


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_local_chat_uses_final_message_and_clamps_values():
    payload = {
        "output": [
            {"type": "reasoning", "content": "ignore me"},
            {"type": "message", "content": "```json\n{\"energy\":1.2,\"brightness\":0.6,\"warmth\":0.7,\"shimmer\":0.8,\"motion\":0.4,\"density\":-0.1,\"confidence\":0.9}\n```"},
        ]
    }
    captured = {}
    def fake_open(request, timeout):
        captured.update(json.loads(request.data))
        return FakeResponse(json.dumps(payload).encode())
    with patch("mirror_voice.llm.urlopen", side_effect=fake_open):
        frame = LocalChatSemanticEar("gemma").analyze("silver warmth")
    assert frame.source == "local-chat:gemma"
    assert frame.values["energy"] == 1.0
    assert frame.values["density"] == 0.0
    assert frame.confidence == .9
    assert captured["reasoning"] == "on"
    assert captured["temperature"] == .1
    assert captured["max_output_tokens"] == 700
    assert captured["store"] is False


def test_local_chat_requires_message_output():
    payload = {"output": [{"type": "reasoning", "content": "only thought"}]}
    with patch("mirror_voice.llm.urlopen", return_value=FakeResponse(json.dumps(payload).encode())):
        try:
            LocalChatSemanticEar("gemma").analyze("hello")
        except ValueError as exc:
            assert "no message" in str(exc)
        else:
            raise AssertionError("expected missing message to fail")
