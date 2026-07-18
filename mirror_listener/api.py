from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import threading
from urllib.parse import urlparse

from .bridge import CompanionBridge, RELATIONAL_MODES
from .memory import TemporalMemory
from .model import CORE_QUALITIES, ListenerFrame, clamp
from .session import SessionStore


class CompanionState:
    def __init__(self, memory: TemporalMemory, bridge: CompanionBridge,
                 session_store: SessionStore | None = None):
        self.memory, self.bridge, self.session_store = memory, bridge, session_store
        self.frame: ListenerFrame | None = None
        self.lock = threading.RLock()

    def update(self, frame: ListenerFrame) -> None:
        with self.lock:
            self.frame = frame

    def state(self) -> dict:
        with self.lock:
            return self.frame.to_dict() if self.frame else {"status": "waiting_for_audio"}

    def recent_changes(self) -> dict:
        with self.lock:
            if not self.frame:
                return {"status": "waiting_for_audio", "events": []}
            return {"time": self.frame.time, "events": self.frame.events,
                    "reflection": self.frame.reflection}

    def mark(self, label: str, note: str = "") -> dict:
        if not label.strip():
            raise ValueError("label is required")
        with self.lock:
            now = self.frame.time if self.frame else 0.0
            result = self.memory.mark_moment(now, label.strip(), note.strip())
            if self.session_store:
                self.session_store.save(self.memory)
            return result

    def set_mode(self, mode: str) -> dict:
        if mode not in RELATIONAL_MODES:
            raise ValueError("unknown relational mode")
        with self.lock:
            self.bridge.mode = mode
            return {"mode": mode}

    def compare(self, left_id: str, right_id: str) -> dict:
        with self.lock:
            passages = {item["id"]: item for item in self.memory.passages}
            if left_id not in passages or right_id not in passages:
                raise ValueError("unknown passage id")
            left, right = passages[left_id], passages[right_id]
            distance = math.sqrt(sum((left["state"][name] - right["state"][name]) ** 2
                                     for name in CORE_QUALITIES) / len(CORE_QUALITIES))
            changes = {name: right["state"][name] - left["state"][name] for name in CORE_QUALITIES}
            return {"left": left_id, "right": right_id, "similarity": clamp(1 - distance * 1.6),
                    "changes": changes, "confidence": min(left["confidence"], right["confidence"])}


def start_api(state: CompanionState, host: str = "127.0.0.1", port: int = 8766):
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Mirror Listener API may bind only to localhost")

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/health": self.reply(200, {"healthy": True, "local_only": True})
            elif path == "/v1/state": self.reply(200, state.state())
            elif path == "/v1/recent-changes": self.reply(200, state.recent_changes())
            else: self.reply(404, {"error": "not found"})

        def do_POST(self):
            try:
                size = min(int(self.headers.get("Content-Length", 0)), 65536)
                data = json.loads(self.rfile.read(size) or b"{}")
                path = urlparse(self.path).path
                if path == "/v1/mark": result = state.mark(data.get("label", ""), data.get("note", ""))
                elif path == "/v1/mode": result = state.set_mode(data.get("mode", ""))
                elif path == "/v1/compare": result = state.compare(data.get("left", ""), data.get("right", ""))
                else: return self.reply(404, {"error": "not found"})
                self.reply(200, result)
            except (ValueError, json.JSONDecodeError) as exc:
                self.reply(400, {"error": str(exc)})

        def log_message(self, *_): pass

    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True, name="mirror-listener-api").start()
    return server
