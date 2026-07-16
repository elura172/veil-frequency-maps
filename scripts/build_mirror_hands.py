#!/usr/bin/env python3
"""Generate the repetitive six-lane Mirror Hands Max patch and package it."""

from __future__ import annotations

import json
from pathlib import Path

from package_amxd import package

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "max-for-live" / "Mirror Hands"
QUALITIES = ("energy", "brightness", "warmth", "shimmer", "motion", "density")


def box(identifier, maxclass, text=None, rect=(0, 0, 60, 22), **extra):
    value = {"id": identifier, "maxclass": maxclass, "patching_rect": list(map(float, rect))}
    if text is not None:
        value["text"] = text
    value.update(extra)
    return {"box": value}


def line(source, outlet, destination, inlet=0):
    return {"patchline": {"source": [source, outlet], "destination": [destination, inlet]}}


def build():
    boxes = [
        box("audio-in", "newobj", "plugin~", (25, 560, 55, 22)),
        box("audio-out", "newobj", "plugout~", (100, 560, 60, 22)),
        box("title", "comment", "MIRROR HANDS", (25, 20, 180, 24), fontsize=16.0, presentation=1, presentation_rect=[14., 8., 170., 24.]),
        box("sub", "comment", "six fuzzy currents → live.remote~", (25, 48, 260, 18), presentation=1, presentation_rect=[14., 32., 260., 18.]),
        box("rx", "newobj", "udpreceive 9000", (25, 95, 105, 22)),
        box("engine", "newobj", "js mirror_hands.js", (240, 135, 120, 22)),
        box("load", "newobj", "loadbang", (380, 95, 60, 22)),
        box("loadmsg", "message", "loadbang", (460, 95, 65, 22)),
        box("status", "newobj", "udpsend 127.0.0.1 9001", (800, 135, 155, 22)),
    ]
    lines = [line("audio-in", 0, "audio-out"), line("audio-in", 1, "audio-out", 1), line("rx", 0, "engine"), line("load", 0, "loadmsg"), line("loadmsg", 0, "engine"), line("engine", 12, "status")]
    for index, quality in enumerate(QUALITIES):
        y = 205 + index * 52
        px = 285 + index * 66
        boxes.extend([
            box(f"line-{index}", "newobj", "line~ 0.", (25, y, 60, 22)),
            box(f"remote-{index}", "newobj", "live.remote~ @normalized 1", (105, y, 165, 22)),
            box(f"dial-{index}", "live.dial", rect=(300, y, 48, 42), parameter_enable=0, presentation=1, presentation_rect=[float(px), 8., 48., 42.]),
            box(f"label-{index}", "comment", quality.upper(), (360, y, 90, 18), presentation=1, presentation_rect=[float(px-4), 51., 62., 16.]),
            box(f"led-{index}", "led", rect=(470, y, 16, 16), presentation=1, presentation_rect=[float(px+16), 69., 16., 16.]),
        ])
        lines.extend([
            line("engine", index * 2, f"line-{index}"),
            line("engine", index * 2, f"dial-{index}"),
            line("engine", index * 2 + 1, f"remote-{index}", 1),
            line(f"line-{index}", 0, f"remote-{index}"),
            line(f"remote-{index}", 0, f"led-{index}"),
        ])
    document = {"patcher": {
        "fileversion": 1, "appversion": {"major": 9, "minor": 0, "revision": 7, "architecture": "x64", "modernui": 1},
        "classnamespace": "box", "rect": [40., 80., 1000., 640.], "openinpresentation": 1, "devicewidth": 690.,
        "default_fontsize": 11., "default_fontname": "Ableton Sans Medium Regular", "boxes": boxes, "lines": lines,
        "dependency_cache": [{"name": "mirror_hands.js", "bootpath": ".", "type": "TEXT", "implicit": 1}], "latency": 0, "autosave": 0,
    }}
    source = DIRECTORY / "Mirror Hands.maxpat"
    artifact = DIRECTORY / "Mirror Hands.amxd"
    source.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    package(source, artifact)


if __name__ == "__main__":
    build()
