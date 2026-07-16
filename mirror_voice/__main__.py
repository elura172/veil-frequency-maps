from __future__ import annotations

import argparse
import json
import sys
from time import monotonic

from .engine import MirrorVoiceEngine
from .lexicon import analyze_text
from .llm import OllamaSemanticEar
from .model import AcousticFrame
from .osc import MirrorOSCSender


def main() -> None:
    parser = argparse.ArgumentParser(description="Voice/text to six-dimensional Mirror OSC field")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--half-life", type=float, default=.8)
    parser.add_argument("--ollama-model", help="Optional local Ollama model for semantic enrichment")
    parser.add_argument("--no-osc", action="store_true", help="Print states without sending UDP")
    args = parser.parse_args()
    engine = MirrorVoiceEngine(args.half_life)
    sender = None if args.no_osc else MirrorOSCSender(args.host, args.port)
    ear = OllamaSemanticEar(args.ollama_model) if args.ollama_model else None
    try:
        for line in sys.stdin:
            event = json.loads(line)
            acoustic = AcousticFrame(**event.get("acoustic", {}))
            text = event.get("text", "")
            semantic = analyze_text(text)
            if ear and text:
                try:
                    semantic = ear.analyze(text)
                except Exception as exc:
                    event["semantic_warning"] = str(exc)
            state = engine.update(acoustic, text, semantic=semantic, now=monotonic())
            if sender:
                sender.send(state)
            output = state.to_dict()
            if "semantic_warning" in event:
                output["semantic_warning"] = event["semantic_warning"]
            print(json.dumps(output, separators=(",", ":")), flush=True)
    finally:
        if sender:
            sender.close()


if __name__ == "__main__":
    main()
