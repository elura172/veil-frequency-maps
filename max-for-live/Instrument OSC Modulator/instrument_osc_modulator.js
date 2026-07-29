/* Instrument OSC Modulator v1 — four normalized live.remote~ control slots. */
autowatch = 1;
inlets = 1;
outlets = 9; // value/id pairs for slots 0..3, then OSC status

var PHI = 1.618033988749895;
var SILVER = 1.0 + Math.sqrt(2.0);
var BRONZE = (3.0 + Math.sqrt(13.0)) / 2.0;
var slots = [];
var lastTick = Date.now();

function freshSlot() {
    return {mapped: 0, running: 0, id: 0, track: -1, device: -1, parameter: -1,
        shape: "sine", rate_hz: 0.1, sync_beats: 0, depth: 0.5, offset: 0.5,
        phase: 0, smoothing_ms: 20, polarity: "bipolar", quantized: 0, steps: 1};
}
for (var i = 0; i < 4; i++) slots.push(freshSlot());

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, Number(v))); }
function validSlot(v) { v = Number(v); return v >= 0 && v < 4 && Math.floor(v) === v; }
function prefix(address) { return address.indexOf("/operator-mod/v1") === 0 ? "/operator-mod/v1" : "/wavetable-mod/v1"; }

function report(address) {
    var args = arrayfromargs(arguments).slice(1);
    outlet(8, [address].concat(args));
}

function error(base, address, message) { report(base + "/error", address, String(message)); }

function mapSlot(base, args) {
    var n = Number(args[0]);
    if (!validSlot(n) || args.length < 4) return error(base, base + "/slot/map", "expected slot track device parameter");
    release(n);
    try {
        var path = "live_set tracks " + Number(args[1]) + " devices " + Number(args[2]) + " parameters " + Number(args[3]);
        var api = new LiveAPI(null, path);
        if (!api.id || api.id === 0) throw new Error("parameter path did not resolve");
        var s = slots[n];
        s.id = Number(api.id); s.track = Number(args[1]); s.device = Number(args[2]); s.parameter = Number(args[3]);
        s.quantized = Number(api.get("is_quantized")) !== 0;
        var min = Number(api.get("min")), max = Number(api.get("max"));
        s.steps = Math.max(1, Math.round(max - min));
        s.mapped = 1;
        outlet(n * 2 + 1, "id", s.id);
        slotState(base, n);
    } catch (e) { error(base, base + "/slot/map", e.message || e); }
}

function release(n) {
    if (!validSlot(n)) return;
    slots[n].running = 0; slots[n].mapped = 0; slots[n].id = 0;
    outlet(n * 2 + 1, "id", 0);
}

function setSlot(base, args) {
    var n = Number(args[0]), field = String(args[1]), value = args[2];
    if (!validSlot(n) || args.length < 3) return error(base, base + "/slot/set", "expected slot field value");
    var s = slots[n];
    if (field === "shape") {
        var shapes = ["sine", "triangle", "saw_up", "saw_down", "square", "sample_hold", "golden", "silver", "bronze"];
        if (shapes.indexOf(String(value)) < 0) return error(base, base + "/slot/set", "unknown shape");
        s.shape = String(value);
    } else if (field === "rate_hz") { s.rate_hz = Math.max(0.000001, Number(value)); s.sync_beats = 0;
    } else if (field === "sync_beats") { s.sync_beats = Math.max(0.000001, Number(value));
    } else if (field === "depth") { s.depth = clamp(value, 0, 1);
    } else if (field === "offset") { s.offset = clamp(value, 0, 1);
    } else if (field === "phase") { s.phase = ((Number(value) % 1) + 1) % 1;
    } else if (field === "smoothing_ms") { s.smoothing_ms = Math.max(0, Number(value));
    } else if (field === "polarity") {
        if (value !== "bipolar" && value !== "unipolar") return error(base, base + "/slot/set", "polarity must be bipolar or unipolar");
        s.polarity = String(value);
    } else return error(base, base + "/slot/set", "unknown field " + field);
    slotState(base, n);
}

function tempo() {
    try { return Number(new LiveAPI(null, "live_set").get("tempo")); } catch (_) { return 120; }
}

function shaped(s) {
    var p = s.phase, tri = p < 0.5 ? p * 2 : (1 - p) * 2, v;
    if (s.shape === "sine") v = 0.5 - 0.5 * Math.cos(p * Math.PI * 2);
    else if (s.shape === "triangle") v = tri;
    else if (s.shape === "saw_up") v = p;
    else if (s.shape === "saw_down") v = 1 - p;
    else if (s.shape === "square") v = p < 0.5 ? 0 : 1;
    else if (s.shape === "sample_hold") v = (Math.sin(Math.floor(p * 16) * 91.345) + 1) * 0.5;
    else if (s.shape === "golden") v = Math.pow(tri, PHI);
    else if (s.shape === "silver") v = Math.pow(tri, SILVER);
    else v = Math.pow(tri, BRONZE);
    var result = s.polarity === "unipolar" ? s.offset + v * s.depth : s.offset + (v * 2 - 1) * s.depth * 0.5;
    result = clamp(result, 0, 1);
    if (s.quantized) result = Math.round(result * s.steps) / s.steps;
    return result;
}

function tick() {
    var now = Date.now(), dt = Math.min(0.25, Math.max(0, (now - lastTick) / 1000)); lastTick = now;
    var bpm = 0;
    for (var n = 0; n < 4; n++) {
        var s = slots[n]; if (!s.mapped || !s.running) continue;
        var hz = s.rate_hz;
        if (s.sync_beats > 0) { if (!bpm) bpm = tempo(); hz = bpm / (60 * s.sync_beats); }
        s.phase = (s.phase + hz * dt) % 1;
        outlet(n * 2, shaped(s), s.smoothing_ms);
    }
}

function slotState(base, n) {
    var s = slots[n];
    report(base + "/slot/state", n, s.mapped, s.running, s.id, s.phase, shaped(s));
}

function handle(address, args) {
    var base = prefix(address);
    if (address === base + "/slot/map") mapSlot(base, args);
    else if (address === base + "/slot/unmap") { release(Number(args[0])); slotState(base, Number(args[0])); }
    else if (address === base + "/slot/start") { if (validSlot(Number(args[0]))) slots[Number(args[0])].running = 1; slotState(base, Number(args[0])); }
    else if (address === base + "/slot/stop") { if (validSlot(Number(args[0]))) slots[Number(args[0])].running = 0; slotState(base, Number(args[0])); }
    else if (address === base + "/slot/set") setSlot(base, args);
    else if (address === base + "/slot/status") slotState(base, Number(args[0]));
    else if (address === base + "/all/stop") { for (var i = 0; i < 4; i++) slots[i].running = 0; report(base + "/ready", 1, 4); }
    else if (address === base + "/status") { report(base + "/ready", 1, 4); for (var j = 0; j < 4; j++) slotState(base, j); }
    else error(base, address, "unknown request");
}

function anything() { handle(String(messagename), arrayfromargs(arguments)); }
function list() {
    var args = arrayfromargs(arguments); if (!args.length) return;
    handle(String(args.shift()), args);
}
function bang() { tick(); }
function loadbang() { report("/wavetable-mod/v1/ready", 1, 4); report("/operator-mod/v1/ready", 1, 4); }
function freebang() { for (var i = 0; i < 4; i++) release(i); }
