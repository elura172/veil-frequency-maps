import time
import unittest

from osc_mcp.gestures import GOLDEN_MAJOR, GestureScheduler, curve_value, shaped_value


class CurveTests(unittest.TestCase):
    def test_all_curves_reach_endpoints(self):
        names = ["linear", "ease_in", "ease_out", "ease_in_out", "exponential", "logarithmic", "sine", "golden", "golden_in", "golden_out", "fibonacci_steps"]
        for name in names:
            self.assertAlmostEqual(curve_value(name, 0), 0, msg=name)
            self.assertAlmostEqual(curve_value(name, 1), 1, msg=name)

    def test_golden_curve_hinge(self):
        self.assertAlmostEqual(curve_value("golden", GOLDEN_MAJOR), 1 - GOLDEN_MAJOR, places=6)

    def test_log_domain_uses_geometric_midpoint(self):
        self.assertAlmostEqual(shaped_value(100, 400, 0.5, "linear", "log"), 200)

    def test_db_domain_returns_linear_amplitude(self):
        self.assertAlmostEqual(shaped_value(-60, 0, 0, "linear", "db"), 0.001)
        self.assertAlmostEqual(shaped_value(-60, 0, 1, "linear", "db"), 1.0)


class SchedulerTests(unittest.TestCase):
    def test_scheduler_emits_final_value(self):
        emitted = []
        scheduler = GestureScheduler(lambda target, value: emitted.append(value))
        gesture = scheduler.schedule([{
            "target": {"type": "test", "track_index": 0},
            "from_value": 0, "to_value": 1,
        }], duration=0.03, rate_hz=30)
        deadline = time.time() + 1
        while scheduler.list() and time.time() < deadline:
            time.sleep(0.01)
        finished = {g["id"]: g for g in scheduler.list(include_finished=True)}[gesture["id"]]
        self.assertEqual(finished["state"], "completed")
        self.assertAlmostEqual(emitted[-1], 1)

    def test_cancel_delayed_gesture(self):
        scheduler = GestureScheduler(lambda target, value: None)
        gesture = scheduler.schedule([{
            "target": {"type": "test", "track_index": 0},
            "from_value": 0, "to_value": 1,
        }], duration=1, delay=1)
        scheduler.cancel(gesture["id"])
        time.sleep(0.02)
        state = {g["id"]: g for g in scheduler.list(include_finished=True)}[gesture["id"]]
        self.assertEqual(state["state"], "cancelled")


if __name__ == "__main__":
    unittest.main()
