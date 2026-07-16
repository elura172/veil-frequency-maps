/* Veil Modulator — deterministic semantic modulation engine for Max 8/9. */
autowatch = 1;
inlets = 1;
outlets = 5;

var PHI = 1.618033988749895;
var targets = [0.35, 0.55, 0.25, 0.20];
var values = targets.slice(0);
var phases = [0.0, 0.382, 0.618, 0.236];
var rates = [0.00083, 0.00051, 0.00103, 0.00127];
var running = 1;
var drift = 0.08;
var smoothing = 0.035;

function clamp(value) {
    return Math.max(0.0, Math.min(1.0, value));
}

function setTarget(index, value) {
    targets[index] = clamp(Number(value));
}

function presence(value) { setTarget(0, value); }
function distance(value) { setTarget(1, value); }
function memory(value) { setTarget(2, value); }
function shimmer(value) { setTarget(3, value); }
function active(value) { running = Number(value) !== 0; }
function drift_amount(value) { drift = clamp(Number(value)); }
function smoothing_amount(value) { smoothing = 0.002 + clamp(Number(value)) * 0.12; }

function goldenEase(value) {
    value = clamp(value);
    return Math.pow(value, 1.0 / PHI);
}

function tickPhase(index) {
    phases[index] = (phases[index] + rates[index]) % 1.0;
    var wave = 0.5 - 0.5 * Math.cos(phases[index] * Math.PI * 2.0);
    return (wave * 2.0 - 1.0) * drift;
}

function bang() {
    var names = ["presence", "distance", "memory", "shimmer"];
    for (var index = 0; index < 4; index++) {
        var desired = targets[index];
        if (running) {
            desired = clamp(desired + tickPhase(index));
        }
        values[index] += (goldenEase(desired) - values[index]) * smoothing;
        values[index] = clamp(values[index]);
        outlet(index + 1, values[index]);
        outlet(0, "/veil/" + names[index], values[index]);
    }
}

function reset() {
    values = targets.slice(0);
    phases = [0.0, 0.382, 0.618, 0.236];
}
