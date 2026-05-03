import sys
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from streamvggt.utils.phase_profile import (  # noqa: E402
    phase_profile_enabled,
    phase_profile_end,
    phase_profile_start,
    reset_phase_profile,
    snapshot_phase_profile,
)


class PhaseProfileTests(unittest.TestCase):
    def setUp(self):
        self.old_env = os.environ.get("OBVGGT_PHASE_PROFILE")
        reset_phase_profile()

    def tearDown(self):
        reset_phase_profile()
        if self.old_env is None:
            os.environ.pop("OBVGGT_PHASE_PROFILE", None)
        else:
            os.environ["OBVGGT_PHASE_PROFILE"] = self.old_env

    def test_disabled_profile_returns_none_handle(self):
        os.environ["OBVGGT_PHASE_PROFILE"] = "0"
        self.assertFalse(phase_profile_enabled())
        handle = phase_profile_start("disabled_phase")
        self.assertIsNone(handle)
        self.assertEqual(snapshot_phase_profile(), {"enabled": False, "phases": {}, "pending_cuda_events": 0})

    def test_cpu_profile_accumulates_time_and_calls(self):
        os.environ["OBVGGT_PHASE_PROFILE"] = "1"
        handle = phase_profile_start("Example Phase")
        self.assertIsNotNone(handle)
        phase_profile_end(handle)
        payload = snapshot_phase_profile()
        self.assertTrue(payload["enabled"])
        self.assertIn("example_phase", payload["phases"])
        self.assertEqual(payload["phases"]["example_phase"]["calls"], 1.0)
        self.assertGreaterEqual(payload["phases"]["example_phase"]["total_ms"], 0.0)

    def test_snapshot_reset_clears_profile_state(self):
        os.environ["OBVGGT_PHASE_PROFILE"] = "1"
        phase_profile_end(phase_profile_start("one"))
        payload = snapshot_phase_profile(reset=True)
        self.assertIn("one", payload["phases"])
        self.assertEqual(snapshot_phase_profile()["phases"], {})


if __name__ == "__main__":
    unittest.main()
