import sys
import unittest
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "OBVGGT" / "src"
sys.path.insert(0, str(SRC_ROOT))

from streamvggt.utils.obcache_kv import StreamOBCacheLayerState
from streamvggt.layers.attention import Attention


class OBCacheProfileTests(unittest.TestCase):
    def _state(self) -> StreamOBCacheLayerState:
        k = torch.zeros(1, 2, 3, 4)
        v = torch.zeros(1, 2, 3, 4)
        return StreamOBCacheLayerState(k=k, v=v)

    def test_snapshot_omits_profile_fields_until_profile_events_are_recorded(self) -> None:
        snap = self._state().snapshot()

        self.assertNotIn("profile_score_ms", snap)
        self.assertNotIn("profile_score_calls", snap)

    def test_snapshot_includes_accumulated_profile_events(self) -> None:
        state = self._state()
        state.record_profile_event("score", 1.25)
        state.record_profile_event("score", 2.0)

        snap = state.snapshot()

        self.assertAlmostEqual(snap["profile_score_ms"], 3.25)
        self.assertEqual(snap["profile_score_calls"], 2.0)

    def test_score_interval_due_uses_last_scored_frame(self) -> None:
        state = self._state()
        cfg = {"score_interval": 2}

        state.frame_count = 1
        state.scored_frame_count = 0
        self.assertTrue(Attention._score_interval_due(state, cfg))

        state.scored_frame_count = 1
        state.frame_count = 2
        self.assertFalse(Attention._score_interval_due(state, cfg))

        state.frame_count = 3
        self.assertTrue(Attention._score_interval_due(state, cfg))


if __name__ == "__main__":
    unittest.main()
