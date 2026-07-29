#!/usr/bin/env python3
"""Package Max patch JSON in the simple AMXD ptch container used by Live 12."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


HEADER = b"ampf" + struct.pack("<I", 4) + b"aaaa" + b"meta" + struct.pack("<I", 4) + b"\0\0\0\0" + b"ptch"


def package(source: Path, destination: Path) -> None:
    document = json.loads(source.read_text(encoding="utf-8"))
    payload = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8") + b"\0"
    destination.write_bytes(HEADER + struct.pack("<I", len(payload)) + payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    package(args.source, args.destination)


if __name__ == "__main__":
    main()
