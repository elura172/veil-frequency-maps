import unittest

from osc_mcp.wavetable import checked_value, parameter_inventory, resolve_parameter


class FakeBridge:
    replies = {
        "/live/device/get/class_name": [0, 1, "InstrumentVector"],
        "/live/device/get/parameters/name": [0, 1, "Device On", "Osc 1 Position", "Filter 1 Freq", "Filter 2 Freq"],
        "/live/device/get/parameters/value": [0, 1, 1, 0.25, 440.0, 880.0],
        "/live/device/get/parameters/min": [0, 1, 0, 0.0, 20.0, 20.0],
        "/live/device/get/parameters/max": [0, 1, 1, 1.0, 20000.0, 20000.0],
        "/live/device/get/parameters/is_quantized": [0, 1, 1, 0, 0, 0],
    }

    def query(self, address, params=()):
        return self.replies[address]


class WavetableTests(unittest.TestCase):
    def test_inventory_preserves_live_indices_and_ranges(self):
        inventory = parameter_inventory(FakeBridge(), 0, 1)
        self.assertEqual(inventory["parameters"][1]["name"], "Osc 1 Position")
        self.assertEqual(inventory["parameters"][1]["index"], 1)
        self.assertEqual(inventory["parameters"][2]["max"], 20000.0)

    def test_resolver_accepts_normalized_unique_names(self):
        inventory = parameter_inventory(FakeBridge(), 0, 1)
        self.assertEqual(resolve_parameter(inventory, "OSC-1 position")["index"], 1)

    def test_resolver_refuses_ambiguous_partial_names(self):
        inventory = parameter_inventory(FakeBridge(), 0, 1)
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            resolve_parameter(inventory, "filter freq")

    def test_checked_value_enforces_range_and_quantization(self):
        parameter = {"name": "Mode", "min": 0, "max": 3, "is_quantized": True}
        self.assertEqual(checked_value(parameter, 1.6), 2.0)
        with self.assertRaisesRegex(ValueError, "between"):
            checked_value(parameter, 4)

    def test_rejects_non_wavetable_devices(self):
        bridge = FakeBridge()
        bridge.replies = dict(bridge.replies, **{"/live/device/get/class_name": [0, 1, "Operator"]})
        with self.assertRaisesRegex(ValueError, "not Wavetable"):
            parameter_inventory(bridge, 0, 1)


if __name__ == "__main__":
    unittest.main()
