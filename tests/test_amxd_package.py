import json
import struct
import tempfile
import unittest
from pathlib import Path

from scripts.package_amxd import package


class AmxdPackageTests(unittest.TestCase):
    def test_package_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "device.maxpat"
            destination = Path(directory) / "device.amxd"
            expected = {"patcher": {"fileversion": 1, "boxes": [], "lines": []}}
            source.write_text(json.dumps(expected), encoding="utf-8")
            package(source, destination)
            data = destination.read_bytes()
            self.assertEqual(data[:4], b"ampf")
            self.assertEqual(data[24:28], b"ptch")
            length = struct.unpack("<I", data[28:32])[0]
            self.assertEqual(length, len(data) - 32)
            self.assertEqual(json.loads(data[32:-1]), expected)

    def test_committed_device_matches_editable_source(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / "max-for-live" / "Instrument OSC Modulator"
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = Path(temporary) / "Instrument OSC Modulator.amxd"
            package(directory / "Instrument OSC Modulator.maxpat", rebuilt)
            self.assertEqual(
                rebuilt.read_bytes(),
                (directory / "Instrument OSC Modulator.amxd").read_bytes(),
            )

    def test_mirror_listener_matches_editable_source(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / "max-for-live" / "Mirror Listener"
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = Path(temporary) / "Mirror Listener.amxd"
            package(directory / "Mirror Listener.maxpat", rebuilt)
            self.assertEqual(rebuilt.read_bytes(), (directory / "Mirror Listener.amxd").read_bytes())

    def test_mirror_hands_has_six_remote_lanes_and_matches_source(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / "max-for-live" / "Mirror Hands"
        document = json.loads((directory / "Mirror Hands.maxpat").read_text())
        remotes = [box["box"] for box in document["patcher"]["boxes"] if box["box"].get("text") == "live.remote~ @normalized 1"]
        self.assertEqual(len(remotes), 6)
        with tempfile.TemporaryDirectory() as temporary:
            rebuilt = Path(temporary) / "Mirror Hands.amxd"
            package(directory / "Mirror Hands.maxpat", rebuilt)
            self.assertEqual(rebuilt.read_bytes(), (directory / "Mirror Hands.amxd").read_bytes())


if __name__ == "__main__":
    unittest.main()
