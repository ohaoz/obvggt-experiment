import sys
import unittest
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "OBVGGT" / "src"
sys.path.insert(0, str(SRC_ROOT))

from streamvggt.utils.obcache_kv import StreamOBCacheLayerState  # noqa: E402
from streamvggt.layers.attention import Attention  # noqa: E402


class FixedEvictionTracker:
    def __init__(self, keep_indices: torch.Tensor):
        self.keep_indices = keep_indices

    def evict(self, num_recent_tokens: int, num_heavy_tokens: int, num_coming: int, layer_idx: int) -> torch.Tensor:
        return self.keep_indices


def make_kv(length: int) -> tuple[torch.Tensor, torch.Tensor]:
    base = torch.arange(length * 2, dtype=torch.float32).reshape(1, 1, length, 2)
    return base, base + 1000.0


class OBCachePreallocTests(unittest.TestCase):
    def test_append_kv_matches_cat_path(self) -> None:
        k0, v0 = make_kv(3)
        k1, v1 = make_kv(2)

        plain = StreamOBCacheLayerState(k=k0.clone(), v=v0.clone())
        prealloc = StreamOBCacheLayerState(k=k0.clone(), v=v0.clone())
        prealloc.enable_prealloc(append_tokens=2)

        plain.append_kv(k1, v1)
        prealloc.append_kv(k1, v1)

        self.assertEqual(plain.seq_len, prealloc.seq_len)
        self.assertTrue(torch.equal(plain.k, prealloc.k))
        self.assertTrue(torch.equal(plain.v, prealloc.v))
        self.assertGreaterEqual(prealloc.prealloc_capacity, prealloc.seq_len)

    def test_sliding_window_evict_matches_slice_path(self) -> None:
        k0, v0 = make_kv(5)
        k1, v1 = make_kv(2)
        states = []
        for use_prealloc in (False, True):
            state = StreamOBCacheLayerState(
                k=k0.clone(),
                v=v0.clone(),
                tracker=None,
                num_recent_tokens=1,
                num_heavy_tokens=3,
            )
            if use_prealloc:
                state.enable_prealloc(append_tokens=2)
            state.append_kv(k1, v1)
            state.maybe_evict(num_coming=0)
            states.append(state)

        self.assertEqual(states[0].seq_len, states[1].seq_len)
        self.assertEqual(states[0].evict_calls, states[1].evict_calls)
        self.assertEqual(states[0].evicted_tokens_total, states[1].evicted_tokens_total)
        self.assertTrue(torch.equal(states[0].k, states[1].k))
        self.assertTrue(torch.equal(states[0].v, states[1].v))

    def test_heavy_evict_matches_gather_path(self) -> None:
        k0, v0 = make_kv(4)
        k1, v1 = make_kv(2)
        keep = torch.tensor([[[0, 2]]], dtype=torch.long)
        states = []
        for use_prealloc in (False, True):
            state = StreamOBCacheLayerState(
                k=k0.clone(),
                v=v0.clone(),
                tracker=FixedEvictionTracker(keep_indices=keep),
                num_recent_tokens=2,
                num_heavy_tokens=2,
            )
            if use_prealloc:
                state.enable_prealloc(append_tokens=2)
            state.append_kv(k1, v1)
            state.maybe_evict(num_coming=0)
            states.append(state)

        self.assertEqual(states[0].seq_len, states[1].seq_len)
        self.assertEqual(states[0].evict_calls, states[1].evict_calls)
        self.assertEqual(states[0].evicted_tokens_total, states[1].evicted_tokens_total)
        self.assertTrue(torch.equal(states[0].k, states[1].k))
        self.assertTrue(torch.equal(states[0].v, states[1].v))
        self.assertEqual(states[1].snapshot()["prealloc_kv_enabled"], 1.0)

    def test_attention_two_frame_forward_matches_plain_cache(self) -> None:
        torch.manual_seed(3)
        base = Attention(dim=8, num_heads=2, attn_drop=0.0, proj_drop=0.0, fused_attn=False)
        prealloc = Attention(dim=8, num_heads=2, attn_drop=0.0, proj_drop=0.0, fused_attn=False)
        prealloc.load_state_dict(base.state_dict())
        base.eval()
        prealloc.eval()

        x0 = torch.randn(1, 4, 8)
        x1 = torch.randn(1, 4, 8)
        cfg = {
            "enable": True,
            "method": "sliding_window",
            "num_recent_tokens": 0,
            "num_heavy_tokens": 8,
        }
        prealloc_cfg = dict(cfg, prealloc_kv=True)

        out0, state0 = base(x0, use_cache=True, obcache_cfg=cfg)
        out1, state1 = base(x1, use_cache=True, past_key_values=state0, obcache_cfg=cfg)
        out0_pre, state0_pre = prealloc(x0, use_cache=True, obcache_cfg=prealloc_cfg)
        out1_pre, state1_pre = prealloc(x1, use_cache=True, past_key_values=state0_pre, obcache_cfg=prealloc_cfg)

        self.assertTrue(torch.allclose(out0, out0_pre))
        self.assertTrue(torch.allclose(out1, out1_pre))
        self.assertTrue(torch.equal(state1.k, state1_pre.k))
        self.assertTrue(torch.equal(state1.v, state1_pre.v))
        self.assertNotIn("prealloc_kv_enabled", state1.snapshot())
        self.assertEqual(state1_pre.snapshot()["prealloc_kv_enabled"], 1.0)


if __name__ == "__main__":
    unittest.main()
