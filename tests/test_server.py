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
        if address == "/live/track/get/crossfade_assign":
            return [params[0], 2]
        if address.startswith("/live/device/get/"):
            device_values = {
                "/live/device/get/class_name": [params[0], params[1], "InstrumentVector"],
                "/live/device/get/parameters/name": [params[0], params[1], "Device On", "Osc 1 Position"],
                "/live/device/get/parameters/value": [params[0], params[1], 1, 0.25],
                "/live/device/get/parameters/min": [params[0], params[1], 0, 0.0],
                "/live/device/get/parameters/max": [params[0], params[1], 1, 1.0],
                "/live/device/get/parameters/is_quantized": [params[0], params[1], 1, 0],
            }
            return device_values[address]
        values = {
            "/live/song/get/tempo": [120.0],
            "/live/song/get/current_song_time": [2.5],
            "/live/song/get/signature_numerator": [4],
            "/live/song/get/crossfader": [0.25],
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

    def test_master_crossfader_gesture_is_clamped(self):
        bridge = FakeBridge(osc=True)
        Server(bridge)._emit_target({"type": "master_crossfader"}, -1.5)
        self.assertEqual(bridge.sent[-1], ("/live/song/set/crossfader", [-1.0]))

    def test_crossfader_tools_use_live_assignments(self):
        bridge = FakeBridge(osc=True)
        server = Server(bridge)
        self.assertEqual(server.call_tool("ableton_get_crossfader", {}), {"value": 0.25})
        self.assertEqual(
            server.call_tool("ableton_get_crossfade_assignment", {"track_index": 3}),
            {"track_index": 3, "assignment": "b", "value": 2},
        )
        server.call_tool("ableton_set_crossfader", {"value": 0.75})
        self.assertEqual(bridge.sent[-1], ("/live/song/set/crossfader", [0.75]))
        result = server.call_tool("ableton_assign_crossfade", {"track_index": 3, "assignment": "b"})
        self.assertEqual(bridge.sent[-1], ("/live/track/set/crossfade_assign", [3, 2]))
        self.assertEqual(result["value"], 2)

    def test_named_wavetable_parameter_is_resolved_at_runtime(self):
        bridge = FakeBridge(osc=True)
        result = Server(bridge).call_tool("ableton_set_wavetable_parameter", {
            "track_index": 2,
            "device_index": 0,
            "parameter": "osc-1 position",
            "value": 0.75,
        })
        self.assertEqual(result, {"parameter": "Osc 1 Position", "index": 1, "value": 0.75})
        self.assertEqual(bridge.sent[-1], ("/live/device/set/parameter/value", [2, 0, 1, 0.75]))

    def test_beat_duration_and_bar_quantization(self):
        server = Server(FakeBridge(osc=True))
        duration, delay = server._gesture_timing({
            "duration": 8, "duration_unit": "beats", "start_quantization": "bar"
        })
        self.assertEqual(duration, 4.0)
        self.assertAlmostEqual(delay, 0.75)


if __name__ == "__main__":
    unittest.main()
