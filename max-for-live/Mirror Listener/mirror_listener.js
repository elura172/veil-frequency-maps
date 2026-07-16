/* Mirror Listener v1 — OSC compatibility, smoothing, musical readout, health. */
autowatch = 1;
inlets = 1;
outlets = 7; // frequency, MIDI note, confidence, RMS, centroid, connected, status

var target = {frequency: 0, confidence: 0, rms: 0, centroid: 0};
var value = {frequency: 0, confidence: 0, rms: 0, centroid: 0};
var smoothingMs = 180;
var timeoutMs = 2500;
var lastMessage = 0;
var lastTick = Date.now();
var wasConnected = 0;

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, Number(v))); }
function frequency(v) { target.frequency = Math.max(0, Number(v)); touch(); }
function confidence(v) { target.confidence = clamp(v, 0, 1); touch(); }
function rms(v) { target.rms = clamp(v, 0, 1); touch(); }
function centroid(v) { target.centroid = Math.max(0, Number(v)); touch(); }
function smoothing_ms(v) { smoothingMs = Math.max(0, Number(v)); }
function timeout_ms(v) { timeoutMs = Math.max(100, Number(v)); }
function touch() { lastMessage = Date.now(); }

function midiFromHz(hz) { return hz > 0 ? 69 + 12 * Math.log(hz / 440) / Math.log(2) : 0; }
function emitStatus(address) {
    var args = arrayfromargs(arguments).slice(1);
    outlet(6, [address].concat(args));
}

function handle(address, args) {
    if (address === "/mirror/dominant_freq" || address === "/mirror/frequency") frequency(args[0]);
    else if (address === "/mirror/pitch") { frequency(args[0]); if (args.length > 1) confidence(args[1]); }
    else if (address === "/mirror/confidence") confidence(args[0]);
    else if (address === "/mirror/rms" || address === "/shimmer/rms") rms(args[0]);
    else if (address === "/mirror/centroid" || address === "/shimmer/centroid") centroid(args[0]);
    else if (address === "/mirror/reset") reset();
    else if (address === "/mirror/status") report();
}

function anything() { handle(String(messagename), arrayfromargs(arguments)); }
function list() { var args = arrayfromargs(arguments); if (args.length) handle(String(args.shift()), args); }

function bang() {
    var now = Date.now(), dt = Math.max(1, now - lastTick); lastTick = now;
    var alpha = smoothingMs <= 0 ? 1 : 1 - Math.exp(-dt / smoothingMs);
    var keys = ["frequency", "confidence", "rms", "centroid"];
    for (var i = 0; i < keys.length; i++) value[keys[i]] += (target[keys[i]] - value[keys[i]]) * alpha;
    var connected = lastMessage > 0 && now - lastMessage <= timeoutMs ? 1 : 0;
    outlet(0, value.frequency);
    outlet(1, midiFromHz(value.frequency));
    outlet(2, value.confidence);
    outlet(3, value.rms);
    outlet(4, value.centroid);
    outlet(5, connected);
    if (connected !== wasConnected) { wasConnected = connected; emitStatus("/mirror/listener/connected", connected); }
}

function report() {
    emitStatus("/mirror/listener/state", wasConnected, value.frequency, midiFromHz(value.frequency), value.confidence, value.rms, value.centroid);
}
function reset() {
    target = {frequency: 0, confidence: 0, rms: 0, centroid: 0};
    value = {frequency: 0, confidence: 0, rms: 0, centroid: 0};
    lastMessage = 0; wasConnected = 0; report();
}
