import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

folder = tempfile.mkdtemp()
config.DB_FILE = os.path.join(folder, "test.db")
config.DATASET_FILE = os.path.join(folder, "data.csv")

import dataset
import db
from engine import Checker
from monitor import SimulatedMonitor
from throttler import Throttler

GAMING_PC = "B8:27:EB:33:6D:04"
CAMERA = "2C:F0:5D:88:39:11"


class TestSystem(unittest.TestCase):
    def setUp(self):
        db.setup()
        db.clear_events()
        self.checker = Checker(SimulatedMonitor(start_minute=300), Throttler())

    def run_spike(self, polls=None):
        self.checker.monitor.add_spike(GAMING_PC, level=60, seconds=120)
        for _ in range(polls or config.STRIKES_NEEDED + 2):
            self.checker.step()

    def actions(self):
        return [e["action"] for e in db.get_events() if e["mac"] == GAMING_PC]

    def test_dataset_size(self):
        rows = dataset.generate(os.path.join(folder, "check.csv"))
        self.assertEqual(rows, len(dataset.DEVICES) * 1440)

    def test_all_devices_loaded(self):
        self.assertEqual(len(self.checker.monitor.devices), 18)

    def test_breach_sends_alert_and_throttles(self):
        self.run_spike()
        self.assertIn(GAMING_PC, self.checker.throttler.caps)
        for a in ["BREACH", "ALERT", "THROTTLE"]:
            self.assertIn(a, self.actions())

    def test_throttled_speed(self):
        self.run_spike()
        readings = self.checker.step()
        self.assertLessEqual(readings[GAMING_PC], config.THROTTLE_SPEED)

    def test_short_spike_ignored(self):
        self.run_spike(polls=config.STRIKES_NEEDED - 1)
        self.assertNotIn(GAMING_PC, self.checker.throttler.caps)

    def test_manual_release(self):
        self.run_spike()
        self.checker.release(GAMING_PC)
        self.assertNotIn(GAMING_PC, self.checker.throttler.caps)
        self.assertEqual(self.actions()[0], "RELEASE")

    def test_auto_release(self):
        self.run_spike()
        self.checker.throttled_at[GAMING_PC] = time.time() - config.RELEASE_AFTER - 1
        self.checker.step()
        self.assertIn("AUTO_RELEASE", self.actions())

    def test_higher_limit(self):
        self.checker.set_limit(GAMING_PC, 100)
        self.run_spike()
        self.assertNotIn(GAMING_PC, self.checker.throttler.caps)

    def test_tc_commands(self):
        self.run_spike()
        joined = " ".join(self.checker.throttler.history)
        self.assertIn("192.168.1.14/32", joined)
        self.assertIn("5mbit", joined)

    def test_camera_never_throttled(self):
        for _ in range(30):
            self.checker.step()
        self.assertNotIn(CAMERA, self.checker.throttler.caps)

    def test_usage_logged(self):
        self.checker.step()
        events, samples = db.count_rows()
        self.assertGreaterEqual(samples, 18)


if __name__ == "__main__":
    unittest.main()
