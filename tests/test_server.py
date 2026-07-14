import unittest

from osc_mcp.server import Server, TOOLS


class FakeTCP:
    def call(self, command, params=None):
        if command == "ping":
            return {"status": "ok"}
        if command == "get_session_info":
            return {"tempo": 120.0, "track_count": 11}
        return {"command": command, "params": params or {}}


class FakeBridge:
    def __init__(self, osc=False):
        self.available = osc
        self.tcp = FakeTCP()
        self.sent = []

    def osc_available(self):
        return ["ok"] if self.available else None

    def query(self, address, params=(), timeout=0.75):
        values = {
            "/live/song/get/tempo": [120.0],
            "/live/song/get/current_song_time": [2.5],
            "/live/song/get/signature_numerator": [4],
        }
        return values.get(address, [0])

    def send(self, address, params=()):
        self.sent.append((address, list(params)))
        return {"sent": True, "address": address, "params": list(params)}

    def close(self):
        pass


class ServerTests(unittest.TestCase):
    def test_tools_are_unique(self):
        names = [tool["name"] for tool in TOOLS]
        self.assertEqual(len(names), len(set(names)))

    def test_session_falls_back_to_tcp(self):
        data = Server(FakeBridge()).call_tool("ableton_get_session", {})
        self.assertEqual(data["track_count"], 11)

    def test_tempo_prefers_osc(self):
        bridge = FakeBridge(osc=True)
        data = Server(bridge).call_tool("ableton_set_tempo", {"tempo": 96})
        self.assertEqual(bridge.sent[0], ("/live/song/set/tempo", [96]))
        self.assertEqual(data["tempo"], 120.0)

    def test_initialize(self):
        response = Server(FakeBridge()).handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
        self.assertEqual(response["result"]["protocolVersion"], "2025-11-25")

    def test_track_volume_is_clamped(self):
        bridge = FakeBridge(osc=True)
        server = Server(bridge)
        server._emit_target({"type": "track_volume", "track_index": 2}, 1.5)
        self.assertEqual(bridge.sent[-1], ("/live/track/set/volume", [2, 1.0]))

    def test_beat_duration_and_bar_quantization(self):
        server = Server(FakeBridge(osc=True))
        duration, delay = server._gesture_timing({
            "duration": 8, "duration_unit": "beats", "start_quantization": "bar"
        })
        self.assertEqual(duration, 4.0)
        self.assertAlmostEqual(delay, 0.75)


if __name__ == "__main__":
    unittest.main()
