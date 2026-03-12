import torch

from streamvggt.models.aggregator import Aggregator
from streamvggt.utils.obcache_kv import StreamOBCacheLayerState


def _layer_len(layer_cache):
    if layer_cache is None:
        return 0
    if isinstance(layer_cache, StreamOBCacheLayerState):
        return int(layer_cache.k.size(-2))
    return int(layer_cache[0].size(-2))


def run_smoke(num_frames: int = 50) -> None:
    # Small config for CPU-friendly sanity check.
    model = Aggregator(
        img_size=56,
        patch_size=14,
        embed_dim=128,
        depth=4,
        num_heads=4,
        patch_embed="conv",
    ).eval()

    obcache_cfg = {
        "enable": True,
        "method": "joint",
        "probe_mode": True,
        "num_patch_probes": 4,
        "num_sink_frames": 1,
        "num_recent_frames": 2,
        "num_heavy_frames": 3,
    }

    past_key_values = [None] * model.depth

    with torch.no_grad():
        for i in range(num_frames):
            frame = torch.rand(1, 1, 3, 56, 56)
            _, _, past_key_values = model(
                frame,
                past_key_values=past_key_values,
                use_cache=True,
                past_frame_idx=i,
                obcache_cfg=obcache_cfg,
            )

            # Track only the global blocks (where cache is used).
            lens = [_layer_len(past_key_values[j]) for j in range(model.depth)]
            print(f"frame={i:02d} kv_len(first4)={lens[:4]}")


if __name__ == "__main__":
    run_smoke(num_frames=50)
