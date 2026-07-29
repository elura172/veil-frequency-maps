/* Mirror Hands v1 — six semantic lanes into normalized live.remote~ targets. */
autowatch = 1;
inlets = 1;
outlets = 13; // value/id pairs for six qualities, then status

var qualities = ["energy", "brightness", "warmth", "shimmer", "motion", "density"];
var slots = {};
for (var i = 0; i < qualities.length; i++) slots[qualities[i]] = {id: 0, value: 0, smoothing: 180};

function clamp(v) { return Math.max(0, Math.min(1, Number(v))); }
function indexOfQuality(name) { return qualities.indexOf(String(name)); }
function status(address) { outlet(12, [address].concat(arrayfromargs(arguments).slice(1))); }

function setValue(name, value) {
    var i = indexOfQuality(name); if (i < 0) return;
    var slot = slots[name]; slot.value = clamp(value);
    outlet(i * 2, slot.value, slot.smoothing);
}

function mapQuality(args) {
    var name = String(args[0]), i = indexOfQuality(name);
    if (i < 0 || args.length < 4) return status("/mirror/hands/error", "map expects quality track device parameter");
    unmap(name);
    try {
        var path = "live_set tracks " + Number(args[1]) + " devices " + Number(args[2]) + " parameters " + Number(args[3]);
        var api = new LiveAPI(null, path);
        if (!api.id || api.id === 0) throw new Error("parameter path did not resolve");
        slots[name].id = Number(api.id);
        outlet(i * 2 + 1, "id", slots[name].id);
        setValue(name, slots[name].value);
        status("/mirror/hands/mapped", name, slots[name].id);
    } catch (e) { status("/mirror/hands/error", name, e.message || e); }
}

function unmap(name) {
    var i = indexOfQuality(name); if (i < 0) return;
    slots[name].id = 0; outlet(i * 2 + 1, "id", 0);
    status("/mirror/hands/unmapped", name);
}

function report() {
    var args = [];
    for (var i = 0; i < qualities.length; i++) args.push(qualities[i], slots[qualities[i]].id, slots[qualities[i]].value);
    status.apply(this, ["/mirror/hands/state"].concat(args));
}

function handle(address, args) {
    var voice = "/mirror/voice/";
    if (address.indexOf(voice) === 0) {
        var name = address.slice(voice.length);
        if (indexOfQuality(name) >= 0) setValue(name, args[0]);
    } else if (address === "/mirror/hands/map") mapQuality(args);
    else if (address === "/mirror/hands/unmap") unmap(String(args[0]));
    else if (address === "/mirror/hands/unmap_all") { for (var i = 0; i < qualities.length; i++) unmap(qualities[i]); }
    else if (address === "/mirror/hands/smoothing") {
        var i = indexOfQuality(args[0]); if (i >= 0) slots[qualities[i]].smoothing = Math.max(0, Number(args[1]));
    } else if (address === "/mirror/hands/status") report();
}

function anything() { handle(String(messagename), arrayfromargs(arguments)); }
function list() { var args = arrayfromargs(arguments); if (args.length) handle(String(args.shift()), args); }
function loadbang() { status("/mirror/hands/ready", 1, 6); }
function freebang() { for (var i = 0; i < qualities.length; i++) unmap(qualities[i]); }
