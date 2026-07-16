from __future__ import annotations

import json
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Any

from . import __version__
from .gestures import GestureScheduler
from .wavetable import checked_value, parameter_inventory, resolve_parameter

OSC_INSTALL = Path(os.getenv(
    "ABLETON_OSC_INSTALL",
    str(Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC"),
))
if str(OSC_INSTALL) not in sys.path:
    sys.path.insert(0, str(OSC_INSTALL))

from client.client import AbletonOSCClient  # noqa: E402


def object_schema(properties=None, required=None):
    result = {"type": "object", "properties": properties or {}, "additionalProperties": False}
    if required:
        result["required"] = required
    return result


JSON_VALUE = {"type": ["string", "number", "integer", "boolean"]}
TARGET_SCHEMA = object_schema({
    "type": {"type": "string", "enum": ["track_volume", "track_pan", "track_send", "device_parameter", "master_crossfader"]},
    "track_index": {"type": "integer", "minimum": 0},
    "send_index": {"type": "integer", "minimum": 0},
    "device_index": {"type": "integer", "minimum": 0},
    "parameter_index": {"type": "integer", "minimum": 0},
}, ["type"])
CURVES = [
    "linear", "ease_in", "ease_out", "ease_in_out", "exponential",
    "logarithmic", "sine", "golden", "golden_in", "golden_out",
    "silver_in", "silver_out", "bronze_in", "bronze_out",
    "fibonacci_steps",
]
RAMP_SCHEMA = object_schema({
    "target": TARGET_SCHEMA,
    "from_value": {"type": "number"},
    "to_value": {"type": "number"},
    "curve": {"type": "string", "enum": CURVES},
    "domain": {"type": "string", "enum": ["linear", "log", "db"], "default": "linear"},
}, ["target", "from_value", "to_value"])
WAVETABLE_LOCATION = {
    "track_index": {"type": "integer", "minimum": 0},
    "device_index": {"type": "integer", "minimum": 0},
}
WAVETABLE_CHANGE = object_schema({
    "parameter": {"type": "string", "minLength": 1},
    "to_value": {"type": "number"},
    "from_value": {"type": "number"},
    "curve": {"type": "string", "enum": CURVES},
    "domain": {"type": "string", "enum": ["linear", "log", "db"]},
}, ["parameter", "to_value"])
TOOLS = [
    {"name": "ableton_health", "description": "Check Ableton connectivity. Prefers AbletonOSC and reports TCP fallback status.", "inputSchema": object_schema()},
    {"name": "ableton_get_session", "description": "Get tempo, time signature, transport, loop, and track counts.", "inputSchema": object_schema()},
    {"name": "ableton_get_track", "description": "Get common properties for a track.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}}, ["track_index"])},
    {"name": "ableton_set_tempo", "description": "Set Live's tempo in BPM.", "inputSchema": object_schema({"tempo": {"type": "number", "minimum": 20, "maximum": 999}}, ["tempo"])},
    {"name": "ableton_transport", "description": "Start or stop Live playback.", "inputSchema": object_schema({"action": {"type": "string", "enum": ["start", "stop", "continue"]}}, ["action"])},
    {"name": "ableton_create_track", "description": "Create a MIDI, audio, or return track. Index -1 appends.", "inputSchema": object_schema({"track_type": {"type": "string", "enum": ["midi", "audio", "return"]}, "index": {"type": "integer", "minimum": -1, "default": -1}}, ["track_type"])},
    {"name": "ableton_create_clip", "description": "Create an empty MIDI clip in a Session View slot.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}, "clip_index": {"type": "integer", "minimum": 0}, "length_beats": {"type": "number", "exclusiveMinimum": 0}}, ["track_index", "clip_index", "length_beats"])},
    {"name": "ableton_add_notes", "description": "Add MIDI notes to a Session clip.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}, "clip_index": {"type": "integer", "minimum": 0}, "notes": {"type": "array", "minItems": 1, "items": object_schema({"pitch": {"type": "integer", "minimum": 0, "maximum": 127}, "start_time": {"type": "number", "minimum": 0}, "duration": {"type": "number", "exclusiveMinimum": 0}, "velocity": {"type": "integer", "minimum": 1, "maximum": 127}, "mute": {"type": "boolean", "default": False}}, ["pitch", "start_time", "duration", "velocity"])}}, ["track_index", "clip_index", "notes"])},
    {"name": "ableton_get_device_parameters", "description": "List device parameter names and values.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}, "device_index": {"type": "integer", "minimum": 0}}, ["track_index", "device_index"])},
    {"name": "ableton_set_device_parameter", "description": "Set a device parameter value.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}, "device_index": {"type": "integer", "minimum": 0}, "parameter_index": {"type": "integer", "minimum": 0}, "value": {"type": "number"}}, ["track_index", "device_index", "parameter_index", "value"])},
    {"name": "ableton_inspect_wavetable", "description": "Inspect a Wavetable instance by name, value, range, and quantization without relying on fixed parameter indices.", "inputSchema": object_schema(WAVETABLE_LOCATION, ["track_index", "device_index"])},
    {"name": "ableton_set_wavetable_parameter", "description": "Set one dynamically resolved Wavetable parameter by its Live display name.", "inputSchema": object_schema({**WAVETABLE_LOCATION, "parameter": {"type": "string", "minLength": 1}, "value": {"type": "number"}}, ["track_index", "device_index", "parameter", "value"])},
    {"name": "ableton_morph_wavetable", "description": "Morph multiple dynamically resolved Wavetable parameters as one cancellable, curve-shaped gesture.", "inputSchema": object_schema({**WAVETABLE_LOCATION, "changes": {"type": "array", "minItems": 1, "items": WAVETABLE_CHANGE}, "duration": {"type": "number", "exclusiveMinimum": 0}, "duration_unit": {"type": "string", "enum": ["seconds", "beats"], "default": "seconds"}, "curve": {"type": "string", "enum": CURVES, "default": "golden"}, "rate_hz": {"type": "number", "minimum": 1, "maximum": 30, "default": 20}, "delay_seconds": {"type": "number", "minimum": 0, "default": 0}, "start_quantization": {"type": "string", "enum": ["none", "beat", "bar"], "default": "none"}}, ["track_index", "device_index", "changes", "duration"])},
    {"name": "ableton_get_crossfader", "description": "Get Live's master crossfader value from -1 (A) through 0 to +1 (B).", "inputSchema": object_schema()},
    {"name": "ableton_set_crossfader", "description": "Set Live's master crossfader from -1 (A) through 0 to +1 (B).", "inputSchema": object_schema({"value": {"type": "number", "minimum": -1, "maximum": 1}}, ["value"])},
    {"name": "ableton_get_crossfade_assignment", "description": "Get a track's crossfader assignment as A, neither side, or B.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}}, ["track_index"])},
    {"name": "ableton_assign_crossfade", "description": "Assign a track to crossfader side A, neither side, or side B.", "inputSchema": object_schema({"track_index": {"type": "integer", "minimum": 0}, "assignment": {"type": "string", "enum": ["a", "none", "b"]}}, ["track_index", "assignment"])},
    {"name": "ableton_ramp", "description": "Schedule one smooth local fader, pan, send, device-parameter, or master-crossfader gesture. Metallic-ratio curves are supported.", "inputSchema": object_schema({"target": TARGET_SCHEMA, "from_value": {"type": "number"}, "to_value": {"type": "number"}, "duration": {"type": "number", "exclusiveMinimum": 0}, "duration_unit": {"type": "string", "enum": ["seconds", "beats"], "default": "seconds"}, "curve": {"type": "string", "enum": CURVES, "default": "golden"}, "domain": {"type": "string", "enum": ["linear", "log", "db"], "default": "linear"}, "rate_hz": {"type": "number", "minimum": 1, "maximum": 30, "default": 20}, "delay_seconds": {"type": "number", "minimum": 0, "default": 0}, "start_quantization": {"type": "string", "enum": ["none", "beat", "bar"], "default": "none"}}, ["target", "from_value", "to_value", "duration"])},
    {"name": "ableton_batch_ramp", "description": "Schedule coordinated parameter ramps as one cancellable gesture.", "inputSchema": object_schema({"ramps": {"type": "array", "minItems": 1, "items": RAMP_SCHEMA}, "duration": {"type": "number", "exclusiveMinimum": 0}, "duration_unit": {"type": "string", "enum": ["seconds", "beats"], "default": "seconds"}, "curve": {"type": "string", "enum": CURVES, "default": "golden"}, "rate_hz": {"type": "number", "minimum": 1, "maximum": 30, "default": 20}, "delay_seconds": {"type": "number", "minimum": 0, "default": 0}, "start_quantization": {"type": "string", "enum": ["none", "beat", "bar"], "default": "none"}}, ["ramps", "duration"])},
    {"name": "ableton_golden_crossfade", "description": "Crossfade two track volumes with complementary golden curves.", "inputSchema": object_schema({"outgoing_track": {"type": "integer", "minimum": 0}, "incoming_track": {"type": "integer", "minimum": 0}, "outgoing_from": {"type": "number", "default": 1.0}, "outgoing_to": {"type": "number", "default": 0.0}, "incoming_from": {"type": "number", "default": 0.0}, "incoming_to": {"type": "number", "default": 1.0}, "duration": {"type": "number", "exclusiveMinimum": 0}, "duration_unit": {"type": "string", "enum": ["seconds", "beats"], "default": "seconds"}, "start_quantization": {"type": "string", "enum": ["none", "beat", "bar"], "default": "bar"}}, ["outgoing_track", "incoming_track", "duration"])},
    {"name": "ableton_cancel_gesture", "description": "Cancel a scheduled or running gesture.", "inputSchema": object_schema({"gesture_id": {"type": "string"}}, ["gesture_id"])},
    {"name": "ableton_cancel_all_gestures", "description": "Cancel every scheduled or running gesture.", "inputSchema": object_schema()},
    {"name": "ableton_get_gestures", "description": "List active gestures, optionally including completed, cancelled, and failed gestures.", "inputSchema": object_schema({"include_finished": {"type": "boolean", "default": False}})},
    {"name": "ableton_osc_query", "description": "Query a documented AbletonOSC getter under /live/. Use for capabilities not covered by typed tools.", "inputSchema": object_schema({"address": {"type": "string", "pattern": "^/live/.+"}, "params": {"type": "array", "items": JSON_VALUE}}, ["address"])},
    {"name": "ableton_osc_send", "description": "Send a documented AbletonOSC command under /live/. This can change the Live Set.", "inputSchema": object_schema({"address": {"type": "string", "pattern": "^/live/.+"}, "params": {"type": "array", "items": JSON_VALUE}}, ["address"])},
]


class TCPFallback:
    def __init__(self, host="127.0.0.1", port=9877, timeout=3.0):
        self.host, self.port, self.timeout = host, port, timeout

    def call(self, command: str, params: dict[str, Any] | None = None):
        payload = json.dumps({"type": command, "params": params or {}}).encode("utf-8")
        with socket.create_connection((self.host, self.port), self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(payload)
            data = bytearray()
            while True:
                data.extend(sock.recv(65536))
                try:
                    response = json.loads(data)
                    break
                except json.JSONDecodeError:
                    if len(data) > 8 * 1024 * 1024:
                        raise RuntimeError("TCP fallback response too large")
        if response.get("status") != "success":
            raise RuntimeError(response.get("message", "AbletonMCP command failed"))
        return response.get("result")


class AbletonHybrid:
    def __init__(self):
        self._osc = None
        self._lock = threading.RLock()
        self.tcp = TCPFallback()

    def _client(self):
        if self._osc is None:
            self._osc = AbletonOSCClient(
                os.getenv("ABLETON_OSC_HOST", "127.0.0.1"),
                int(os.getenv("ABLETON_OSC_PORT", "11000")),
                int(os.getenv("ABLETON_OSC_REPLY_PORT", "11001")),
            )
        return self._osc

    def query(self, address, params=(), timeout=0.75):
        with self._lock:
            return list(self._client().query(address, tuple(params), timeout=timeout))

    def send(self, address, params=()):
        with self._lock:
            self._client().send_message(address, params)
        return {"sent": True, "address": address, "params": list(params)}

    def osc_available(self):
        try:
            return self.query("/live/test", timeout=0.75)
        except Exception:
            return None

    def close(self):
        if self._osc is not None:
            self._osc.stop()


class Server:
    def __init__(self, bridge=None):
        self.bridge = bridge or AbletonHybrid()
        self.scheduler = GestureScheduler(self._emit_target)

    def _emit_target(self, target, value):
        kind, track = target.get("type"), target.get("track_index")
        if kind != "master_crossfader" and track is None:
            raise ValueError("%s requires track_index" % kind)
        if kind == "track_volume":
            address, params = "/live/track/set/volume", [track, max(0.0, min(1.0, value))]
        elif kind == "track_pan":
            address, params = "/live/track/set/panning", [track, max(-1.0, min(1.0, value))]
        elif kind == "track_send":
            if "send_index" not in target:
                raise ValueError("track_send requires send_index")
            address, params = "/live/track/set/send", [track, target["send_index"], max(0.0, min(1.0, value))]
        elif kind == "device_parameter":
            if "device_index" not in target or "parameter_index" not in target:
                raise ValueError("device_parameter requires device_index and parameter_index")
            address, params = "/live/device/set/parameter/value", [track, target["device_index"], target["parameter_index"], value]
        elif kind == "master_crossfader":
            address, params = "/live/song/set/crossfader", [max(-1.0, min(1.0, value))]
        else:
            raise ValueError("Unknown gesture target: %s" % kind)
        self.bridge.send(address, params)

    def _gesture_timing(self, args):
        if not self.bridge.osc_available():
            raise RuntimeError("AbletonOSC must be active for smooth local gestures")
        tempo = float(self.bridge.query("/live/song/get/tempo")[0])
        duration = float(args["duration"])
        if args.get("duration_unit", "seconds") == "beats":
            duration *= 60.0 / tempo
        delay = float(args.get("delay_seconds", 0.0))
        quantize = args.get("start_quantization", "none")
        if quantize != "none":
            song_time = float(self.bridge.query("/live/song/get/current_song_time")[0])
            quantum = 1.0
            if quantize == "bar":
                quantum = float(self.bridge.query("/live/song/get/signature_numerator")[0])
            next_boundary = (int(song_time / quantum) + 1) * quantum
            delay += (next_boundary - song_time) * 60.0 / tempo
        return duration, delay

    def call_tool(self, name, args):
        b = self.bridge
        if name == "ableton_health":
            osc = b.osc_available()
            try:
                tcp = b.tcp.call("ping")
            except Exception as exc:
                tcp = {"available": False, "error": str(exc)}
            return {"healthy": bool(osc) or not (isinstance(tcp, dict) and tcp.get("available") is False), "preferred_transport": "osc" if osc else "tcp", "osc": osc, "tcp": tcp}
        if name == "ableton_get_session":
            if not b.osc_available():
                return b.tcp.call("get_session_info")
            paths = ["tempo", "signature_numerator", "signature_denominator", "is_playing", "current_song_time", "song_length", "loop", "loop_start", "loop_length", "num_tracks", "num_scenes"]
            return {key: b.query("/live/song/get/" + key)[0] for key in paths}
        if name == "ableton_get_track":
            i = args["track_index"]
            if not b.osc_available():
                return b.tcp.call("get_track_info", {"track_index": i})
            props = ["name", "mute", "solo", "arm", "volume", "panning", "num_devices", "playing_slot_index"]
            return {key: b.query("/live/track/get/" + key, [i])[-1] for key in props}
        if name == "ableton_set_tempo":
            if b.osc_available():
                b.send("/live/song/set/tempo", [args["tempo"]])
                return {"tempo": b.query("/live/song/get/tempo")[0]}
            return b.tcp.call("set_tempo", {"tempo": args["tempo"]})
        if name == "ableton_transport":
            action = args["action"]
            if b.osc_available():
                return b.send("/live/song/%s_playing" % action if action != "continue" else "/live/song/continue_playing")
            return b.tcp.call("start_playback" if action != "stop" else "stop_playback")
        if name == "ableton_create_track":
            kind, index = args["track_type"], args.get("index", -1)
            if b.osc_available():
                params = [] if kind == "return" else [index]
                return b.send("/live/song/create_%s_track" % kind, params)
            if kind != "midi":
                raise RuntimeError("OSC must be active to create %s tracks" % kind)
            return b.tcp.call("create_midi_track", {"index": index})
        if name == "ableton_create_clip":
            p = [args["track_index"], args["clip_index"], args["length_beats"]]
            if b.osc_available():
                return b.send("/live/clip_slot/create_clip", p)
            return b.tcp.call("create_clip", {"track_index": p[0], "clip_index": p[1], "length": p[2]})
        if name == "ableton_add_notes":
            flat = [args["track_index"], args["clip_index"]]
            for note in args["notes"]:
                flat.extend([note["pitch"], note["start_time"], note["duration"], note["velocity"], note.get("mute", False)])
            if b.osc_available():
                return b.send("/live/clip/add/notes", flat)
            return b.tcp.call("add_notes_to_clip", {"track_index": flat[0], "clip_index": flat[1], "notes": args["notes"]})
        if name == "ableton_get_device_parameters":
            i, d = args["track_index"], args["device_index"]
            names = b.query("/live/device/get/parameters/name", [i, d])
            values = b.query("/live/device/get/parameters/value", [i, d])
            return {"parameters": [{"index": n, "name": name, "value": values[n + 2] if n + 2 < len(values) else None} for n, name in enumerate(names[2:])]}
        if name == "ableton_set_device_parameter":
            p = [args["track_index"], args["device_index"], args["parameter_index"], args["value"]]
            return b.send("/live/device/set/parameter/value", p)
        if name == "ableton_inspect_wavetable":
            return parameter_inventory(b, args["track_index"], args["device_index"])
        if name == "ableton_set_wavetable_parameter":
            inventory = parameter_inventory(b, args["track_index"], args["device_index"])
            parameter = resolve_parameter(inventory, args["parameter"])
            value = checked_value(parameter, args["value"])
            b.send("/live/device/set/parameter/value", [args["track_index"], args["device_index"], parameter["index"], value])
            return {"parameter": parameter["name"], "index": parameter["index"], "value": value}
        if name == "ableton_morph_wavetable":
            inventory = parameter_inventory(b, args["track_index"], args["device_index"])
            ramps = []
            resolved = []
            for change in args["changes"]:
                parameter = resolve_parameter(inventory, change["parameter"])
                start = checked_value(parameter, change.get("from_value", parameter["value"]))
                end = checked_value(parameter, change["to_value"])
                ramp = {
                    "target": {"type": "device_parameter", "track_index": args["track_index"], "device_index": args["device_index"], "parameter_index": parameter["index"]},
                    "from_value": start,
                    "to_value": end,
                    "curve": change.get("curve", args.get("curve", "golden")),
                    "domain": change.get("domain", "linear"),
                }
                ramps.append(ramp)
                resolved.append({"parameter": parameter["name"], "index": parameter["index"], "from_value": start, "to_value": end})
            duration, delay = self._gesture_timing(args)
            result = self.scheduler.schedule(ramps, duration, args.get("curve", "golden"), args.get("rate_hz", 20), delay, "wavetable_morph")
            result["parameters"] = resolved
            return result
        if name == "ableton_get_crossfader":
            return {"value": float(b.query("/live/song/get/crossfader")[0])}
        if name == "ableton_set_crossfader":
            value = max(-1.0, min(1.0, float(args["value"])))
            b.send("/live/song/set/crossfader", [value])
            return {"value": value}
        if name == "ableton_get_crossfade_assignment":
            i = args["track_index"]
            value = int(b.query("/live/track/get/crossfade_assign", [i])[-1])
            labels = {0: "a", 1: "none", 2: "b"}
            return {"track_index": i, "assignment": labels[value], "value": value}
        if name == "ableton_assign_crossfade":
            assignments = {"a": 0, "none": 1, "b": 2}
            assignment = args["assignment"].lower()
            b.send("/live/track/set/crossfade_assign", [args["track_index"], assignments[assignment]])
            return {"track_index": args["track_index"], "assignment": assignment, "value": assignments[assignment]}
        if name == "ableton_ramp":
            duration, delay = self._gesture_timing(args)
            ramp = {key: args[key] for key in ("target", "from_value", "to_value")}
            ramp.update({"curve": args.get("curve", "golden"), "domain": args.get("domain", "linear")})
            return self.scheduler.schedule([ramp], duration, args.get("curve", "golden"), args.get("rate_hz", 20), delay, "ramp")
        if name == "ableton_batch_ramp":
            duration, delay = self._gesture_timing(args)
            return self.scheduler.schedule(args["ramps"], duration, args.get("curve", "golden"), args.get("rate_hz", 20), delay, "batch_ramp")
        if name == "ableton_golden_crossfade":
            duration, delay = self._gesture_timing(args)
            ramps = [
                {"target": {"type": "track_volume", "track_index": args["outgoing_track"]}, "from_value": args.get("outgoing_from", 1.0), "to_value": args.get("outgoing_to", 0.0), "curve": "golden_in"},
                {"target": {"type": "track_volume", "track_index": args["incoming_track"]}, "from_value": args.get("incoming_from", 0.0), "to_value": args.get("incoming_to", 1.0), "curve": "golden_out"},
            ]
            return self.scheduler.schedule(ramps, duration, "golden", 20, delay, "golden_crossfade")
        if name == "ableton_cancel_gesture":
            return self.scheduler.cancel(args["gesture_id"])
        if name == "ableton_cancel_all_gestures":
            return {"cancelled": self.scheduler.cancel_all()}
        if name == "ableton_get_gestures":
            return {"gestures": self.scheduler.list(args.get("include_finished", False))}
        if name == "ableton_osc_query":
            return {"address": args["address"], "values": b.query(args["address"], args.get("params", []))}
        if name == "ableton_osc_send":
            return b.send(args["address"], args.get("params", []))
        raise ValueError("Unknown tool: %s" % name)

    def handle(self, request):
        if "id" not in request:
            return None
        rid, method, params = request["id"], request.get("method"), request.get("params") or {}
        try:
            if method == "initialize":
                requested = params.get("protocolVersion", "2025-03-26")
                result = {"protocolVersion": requested, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "ableton-osc-gesture-mcp", "version": __version__}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                data = self.call_tool(params.get("name"), params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": json.dumps(data, indent=2)}], "structuredContent": {"result": data}, "isError": False}
            else:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}
            return {"jsonrpc": "2.0", "id": rid, "result": result}
        except Exception as exc:
            if method == "tools/call":
                result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
                return {"jsonrpc": "2.0", "id": rid, "result": result}
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(exc)}}

    def run(self):
        try:
            for line in sys.stdin:
                response = self.handle(json.loads(line))
                if response is not None:
                    print(json.dumps(response, separators=(",", ":")), flush=True)
        finally:
            self.scheduler.cancel_all()
            self.bridge.close()


def main():
    Server().run()


if __name__ == "__main__":
    main()
