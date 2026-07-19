from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .bridge import RELATIONAL_MODES


def schema(properties=None, required=None):
    result = {"type": "object", "properties": properties or {}, "additionalProperties": False}
    if required:
        result["required"] = required
    return result


TOOLS = [
    {"name": "mirror_listen_now", "description": "Get the current musical perception and recent meaningful changes together.", "inputSchema": schema()},
    {"name": "mirror_get_state", "description": "Get current qualities, evidence, memory, synesthesia, numeric image, and reflection decision.", "inputSchema": schema()},
    {"name": "mirror_get_recent_changes", "description": "Get recent perceptual and recurrence events without requesting continuous narration.", "inputSchema": schema()},
    {"name": "mirror_compare_passages", "description": "Compare two stable remembered passage IDs and return similarity and quality changes.", "inputSchema": schema({"left": {"type": "string"}, "right": {"type": "string"}}, ["left", "right"])},
    {"name": "mirror_mark_moment", "description": "Attach a human-provided label and optional note to the current derived musical state. No audio is stored.", "inputSchema": schema({"label": {"type": "string", "minLength": 1}, "note": {"type": "string", "default": ""}}, ["label"])},
    {"name": "mirror_set_relational_mode", "description": "Set how sparsely and in what register Mirror Listener offers companion context.", "inputSchema": schema({"mode": {"type": "string", "enum": list(RELATIONAL_MODES)}}, ["mode"])},
]


class MirrorAPI:
    def __init__(self, base_url: str | None = None, timeout: float = 2.0):
        self.base_url = (base_url or os.getenv("MIRROR_LISTENER_API", "http://127.0.0.1:8766")).rstrip("/")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Mirror Listener MCP may connect only to a localhost HTTP API")
        self.timeout = timeout

    def request(self, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base_url + path, data=data,
                          headers={"Content-Type": "application/json"} if data else {},
                          method="POST" if data is not None else "GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            try: message = json.load(exc).get("error", str(exc))
            except Exception: message = str(exc)
            raise RuntimeError(message) from exc
        except URLError as exc:
            raise RuntimeError("Mirror Listener API is unavailable; start the listener with --api-port 8766") from exc


class MCPServer:
    def __init__(self, api: MirrorAPI | None = None):
        self.api = api or MirrorAPI()

    def call(self, name: str, arguments: dict):
        if name == "mirror_get_state": return self.api.request("/v1/state")
        if name == "mirror_get_recent_changes": return self.api.request("/v1/recent-changes")
        if name == "mirror_listen_now":
            return {"state": self.api.request("/v1/state"),
                    "recent_changes": self.api.request("/v1/recent-changes")}
        if name == "mirror_compare_passages": return self.api.request("/v1/compare", arguments)
        if name == "mirror_mark_moment": return self.api.request("/v1/mark", arguments)
        if name == "mirror_set_relational_mode": return self.api.request("/v1/mode", arguments)
        raise ValueError(f"unknown tool: {name}")

    def handle(self, message: dict):
        method, rid = message.get("method"), message.get("id")
        if method == "initialize":
            requested = message.get("params", {}).get("protocolVersion", "2025-03-26")
            result = {"protocolVersion": requested, "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "mirror-listener", "version": "1.0.0"}}
        elif method == "ping": result = {}
        elif method == "tools/list": result = {"tools": TOOLS}
        elif method == "tools/call":
            params = message.get("params", {})
            try:
                value = self.call(params.get("name", ""), params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(value, separators=(",", ":"))}],
                          "structuredContent": value}
            except Exception as exc:
                result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        elif method and method.startswith("notifications/"): return None
        else: return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}
        return {"jsonrpc": "2.0", "id": rid, "result": result}


def main():
    server = MCPServer()
    for line in sys.stdin:
        try:
            response = server.handle(json.loads(line))
            if response is not None:
                print(json.dumps(response, separators=(",", ":")), flush=True)
        except Exception as exc:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": str(exc)}}), flush=True)


if __name__ == "__main__":
    main()
