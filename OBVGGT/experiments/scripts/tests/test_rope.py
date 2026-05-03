import os
import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from streamvggt.layers.rope import PositionGetter, RotaryPositionEmbedding2D  # noqa: E402


class RopeTests(unittest.TestCase):
    def setUp(self):
        self.old_backend = os.environ.get("OBVGGT_ROPE2D_BACKEND")
        self.old_unsafe = os.environ.get("OBVGGT_ALLOW_UNSAFE_CUROPE")
        os.environ["OBVGGT_ROPE2D_BACKEND"] = "pytorch"
        os.environ.pop("OBVGGT_ALLOW_UNSAFE_CUROPE", None)

    def tearDown(self):
        if self.old_backend is None:
            os.environ.pop("OBVGGT_ROPE2D_BACKEND", None)
        else:
            os.environ["OBVGGT_ROPE2D_BACKEND"] = self.old_backend
        if self.old_unsafe is None:
            os.environ.pop("OBVGGT_ALLOW_UNSAFE_CUROPE", None)
        else:
            os.environ["OBVGGT_ALLOW_UNSAFE_CUROPE"] = self.old_unsafe

    def test_position_getter_reuses_cached_grid(self):
        getter = PositionGetter()
        pos_a = getter(batch_size=2, height=3, width=4, device=torch.device("cpu"))
        pos_b = getter(batch_size=2, height=3, width=4, device=torch.device("cpu"))

        self.assertEqual(pos_a.shape, (2, 12, 2))
        self.assertEqual(pos_b.shape, (2, 12, 2))
        self.assertEqual(len(getter.position_cache), 1)
        self.assertTrue(torch.equal(pos_a, pos_b))
        self.assertEqual(pos_a[0, 0].tolist(), [0, 0])
        self.assertEqual(pos_a[0, -1].tolist(), [2, 3])

    def test_rope_matches_reference_and_reuses_position_components(self):
        rope = RotaryPositionEmbedding2D()
        tokens = torch.randn(2, 3, 8, 16, dtype=torch.float32)
        positions = PositionGetter()(batch_size=2, height=2, width=4, device=torch.device("cpu"))

        output = rope(tokens, positions)
        feature_dim = tokens.size(-1) // 2
        max_position = int(positions.max().item()) + 1
        cos_comp, sin_comp = rope._compute_frequency_components(
            feature_dim,
            max_position,
            tokens.device,
            tokens.dtype,
        )

        def rotate_features(x: torch.Tensor) -> torch.Tensor:
            half = x.shape[-1] // 2
            return torch.cat((-x[..., half:], x[..., :half]), dim=-1)

        vertical, horizontal = tokens.chunk(2, dim=-1)
        cos_y = torch.nn.functional.embedding(positions[..., 0], cos_comp)[:, None, :, :]
        sin_y = torch.nn.functional.embedding(positions[..., 0], sin_comp)[:, None, :, :]
        cos_x = torch.nn.functional.embedding(positions[..., 1], cos_comp)[:, None, :, :]
        sin_x = torch.nn.functional.embedding(positions[..., 1], sin_comp)[:, None, :, :]
        reference = torch.cat(
            [
                (vertical * cos_y) + (rotate_features(vertical) * sin_y),
                (horizontal * cos_x) + (rotate_features(horizontal) * sin_x),
            ],
            dim=-1,
        )

        self.assertTrue(torch.allclose(output, reference))
        self.assertEqual(len(rope.position_component_cache), 1)

        second_output = rope(tokens, positions)
        self.assertTrue(torch.allclose(second_output, reference))
        self.assertEqual(len(rope.position_component_cache), 1)

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is required for server-side RoPE cache coverage")
    def test_rope_cuda_reuses_position_components(self):
        rope = RotaryPositionEmbedding2D().cuda()
        device = torch.device("cuda:0")
        tokens = torch.randn(2, 4, 16, 32, device=device, dtype=torch.float32)
        positions = PositionGetter()(batch_size=2, height=4, width=4, device=device)

        first = rope(tokens, positions)
        second = rope(tokens, positions)
        torch.cuda.synchronize(device)

        self.assertEqual(first.device.type, "cuda")
        self.assertTrue(torch.allclose(first, second))
        self.assertEqual(len(rope.position_component_cache), 1)


if __name__ == "__main__":
    unittest.main()
