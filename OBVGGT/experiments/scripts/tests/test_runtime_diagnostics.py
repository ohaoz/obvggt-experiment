import sys
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from streamvggt.utils import runtime_diagnostics as diag  # noqa: E402


class FakeTensor:
    def __init__(self, shape, stride, dtype="fake.float16", device="cuda:0", is_cuda=True):
        self.shape = shape
        self._stride = stride
        self.dtype = dtype
        self.device = device
        self.is_cuda = is_cuda

    def stride(self):
        return self._stride


class RuntimeDiagnosticsTest(unittest.TestCase):
    def setUp(self):
        diag.snapshot_runtime_diagnostics(reset=True)

    def test_record_rope2d_call_captures_first_sample(self):
        tokens = FakeTensor((1, 16, 1004, 64), (1028 * 64, 64, 64, 1))
        positions = FakeTensor((1, 1004, 2), (2008, 2, 1), dtype="fake.int64")

        diag.record_rope2d_call(tokens, positions, backend="pytorch_python", module="test.module")
        payload = diag.snapshot_runtime_diagnostics()

        self.assertEqual(payload["rope2d"]["backend"], "pytorch_python")
        self.assertEqual(payload["rope2d"]["tokens_shape"], [1, 16, 1004, 64])
        self.assertEqual(payload["rope2d"]["positions_shape"], [1, 1004, 2])
        self.assertEqual(payload["counters"]["rope2d_calls"], 1)

    def test_record_sdpa_call_captures_shapes_and_mask_state(self):
        q = FakeTensor((1, 16, 1004, 64), (1028 * 64, 64, 64, 1))
        k = FakeTensor((1, 16, 5020, 64), (5020 * 64, 64, 64, 1))
        v = FakeTensor((1, 16, 5020, 64), (5020 * 64, 64, 64, 1))

        diag.record_sdpa_call(
            q,
            k,
            v,
            attn_mask=None,
            dropout_p=0.0,
            backend_request="flash",
            backend_effective="flash",
        )
        payload = diag.snapshot_runtime_diagnostics()

        self.assertEqual(payload["sdpa"]["api"], "torch.nn.functional.scaled_dot_product_attention")
        self.assertEqual(payload["sdpa"]["backend_request"], "flash")
        self.assertEqual(payload["sdpa"]["backend_effective"], "flash")
        self.assertEqual(payload["sdpa"]["q_shape"], [1, 16, 1004, 64])
        self.assertFalse(payload["sdpa"]["attn_mask_present"])
        self.assertEqual(payload["counters"]["sdpa_calls"], 1)

    def test_sdpa_backend_request_reads_environment(self):
        with mock.patch.dict("os.environ", {"OBVGGT_SDPA_BACKEND": "efficient"}):
            self.assertEqual(diag.get_sdpa_backend_request(), "efficient")

    def test_sdpa_backend_request_rejects_invalid_value(self):
        with mock.patch.dict("os.environ", {"OBVGGT_SDPA_BACKEND": "not-a-backend"}):
            with self.assertRaises(ValueError):
                diag.get_sdpa_backend_request()

    def test_resolve_sdpa_backend_falls_back_for_float32_fused_request(self):
        q = FakeTensor((1, 16, 2, 64), (2048, 128, 64, 1), dtype="fake.float32")
        k = FakeTensor((1, 16, 2, 64), (2048, 128, 64, 1), dtype="fake.float32")
        v = FakeTensor((1, 16, 2, 64), (2048, 128, 64, 1), dtype="fake.float32")

        self.assertEqual(diag.resolve_sdpa_backend_for_call("flash", q, k, v, None), "default")
        self.assertEqual(diag.resolve_sdpa_backend_for_call("math", q, k, v, None), "math")

    def test_reset_clears_call_samples_and_counters(self):
        tokens = FakeTensor((1, 2, 3, 4), (24, 12, 4, 1))
        diag.record_rope2d_call(tokens, tokens, backend="pytorch_python", module="test.module")

        before = diag.snapshot_runtime_diagnostics(reset=True)
        after = diag.snapshot_runtime_diagnostics()

        self.assertEqual(before["counters"]["rope2d_calls"], 1)
        self.assertEqual(after["rope2d"], {})
        self.assertEqual(after["sdpa"], {})
        self.assertEqual(after["counters"]["rope2d_calls"], 0)
        self.assertEqual(after["counters"]["sdpa_calls"], 0)


if __name__ == "__main__":
    unittest.main()
