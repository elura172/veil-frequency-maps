import unittest

from osc_mcp.operator import parameter_inventory
from osc_mcp.wavetable import checked_value, resolve_parameter


class FakeBridge:
    replies = {
        "/live/device/get/class_name": [1, 0, "Operator"],
        "/live/device/get/parameters/name": [1, 0, "Device On", "Osc-A Level", "Osc-A Fixed", "Filter Freq"],
        "/live/device/get/parameters/value": [1, 0, 1, 0.5, 0, 1200.0],
        "/live/device/get/parameters/min": [1, 0, 0, 0.0, 0, 20.0],
        "/live/device/get/parameters/max": [1, 0, 1, 1.0, 1, 20000.0],
        "/live/device/get/parameters/is_quantized": [1, 0, 1, 0, 1, 0],
    }

    def query(self, address, params=()):
        return self.replies[address]


class OperatorTests(unittest.TestCase):
    def test_inventory_and_name_resolution(self):
        inventory = parameter_inventory(FakeBridge(), 1, 0)
        fixed = resolve_parameter(inventory, "osc a fixed")
        self.assertEqual(fixed["index"], 2)
        self.assertTrue(fixed["is_quantized"])
        self.assertEqual(checked_value(fixed, 0.8), 1.0)

    def test_rejects_non_operator_devices(self):
        bridge = FakeBridge()
        bridge.replies = dict(bridge.replies, **{"/live/device/get/class_name": [1, 0, "InstrumentVector"]})
        with self.assertRaisesRegex(ValueError, "not Operator"):
            parameter_inventory(bridge, 1, 0)


if __name__ == "__main__":
    unittest.main()
