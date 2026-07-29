import time
import unittest

from osc_mcp.gestures import (
    BRONZE_RATIO,
    GOLDEN_MAJOR,
    PHI,
    SILVER_RATIO,
    GestureScheduler,
    curve_value,
    shaped_value,
)


class CurveTests(unittest.TestCase):
    def test_all_curves_reach_endpoints(self):
        names = [
            "linear", "ease_in", "ease_out", "ease_in_out", "exponential",
            "logarithmic", "sine", "golden", "golden_in", "golden_out",
            "silver_in", "silver_out", "bronze_in", "bronze_out",
            "fibonacci_steps",
        ]
        for name in names:
            self.assertAlmostEqual(curve_value(name, 0), 0, msg=name)
            self.assertAlmostEqual(curve_value(name, 1), 1, msg=name)

    def test_golden_curve_hinge(self):
        self.assertAlmostEqual(curve_value("golden", GOLDEN_MAJOR), 1 - GOLDEN_MAJOR, places=6)

    def test_metallic_in_curves_have_ordered_patience(self):
        golden = curve_value("golden_in", 0.5)
        silver = curve_value("silver_in", 0.5)
        bronze = curve_value("bronze_in", 0.5)
        self.assertGreater(SILVER_RATIO, PHI)
        self.assertGreater(BRONZE_RATIO, SILVER_RATIO)
        self.assertGreater(golden, silver)
        self.assertGreater(silver, bronze)

    def test_metallic_out_curves_complement_in_curves(self):
        for metal in ("silver", "bronze"):
            for point in (0.0, 0.2, 0.5, 0.8, 1.0):
                self.assertAlmostEqual(
                    curve_value(f"{metal}_out", point),
                    1.0 - curve_value(f"{metal}_in", 1.0 - point),
                )

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
