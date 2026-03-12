import math
from typing import Any, Dict, Optional, Tuple, Union

import torch
import torch.nn.functional as F
from torch import Tensor, nn

from streamvggt.utils.obcache_kv import (
    StreamOBCacheLayerState,
    build_tracker_from_cfg,
    resolve_token_budgets,
    select_probe_indices,
)

XFORMERS_AVAILABLE = False


class Attention(nn.Module):
    def __init__(
        self,
        dim: int,
        num_heads: int = 8,
        qkv_bias: bool = True,
        proj_bias: bool = True,
        attn_drop: float = 0.0,
        proj_drop: float = 0.0,
        norm_layer: nn.Module = nn.LayerNorm,
        qk_norm: bool = False,
        fused_attn: bool = True,
        rope=None,
    ) -> None:
        super().__init__()
        assert dim % num_heads == 0, "dim should be divisible by num_heads"
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.scale = self.head_dim**-0.5
        self.fused_attn = fused_attn

        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.q_norm = norm_layer(self.head_dim) if qk_norm else nn.Identity()
        self.k_norm = norm_layer(self.head_dim) if qk_norm else nn.Identity()
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim, bias=proj_bias)
        self.proj_drop = nn.Dropout(proj_drop)
        self.rope = rope

    def _init_obcache_state(
        self,
        k_all: Tensor,
        v_all: Tensor,
        num_new_tokens: int,
        obcache_cfg: Dict[str, Any],
    ) -> StreamOBCacheLayerState:
        num_sink_tokens, num_recent_tokens, num_heavy_tokens = resolve_token_budgets(
            obcache_cfg, tokens_per_frame=num_new_tokens
        )
        tracker = build_tracker_from_cfg(obcache_cfg, num_sink_tokens=num_sink_tokens)
        state = StreamOBCacheLayerState(
            k=k_all,
            v=v_all,
            tracker=tracker,
            num_recent_tokens=num_recent_tokens,
            num_heavy_tokens=num_heavy_tokens,
            num_sink_tokens=num_sink_tokens,
            tokens_per_frame=num_new_tokens,
            frame_count=1,
        )
        state.appended_tokens_total = int(num_new_tokens)
        state.max_seq_len_seen = int(k_all.size(-2))
        return state

    def _update_scores_and_maybe_evict(
        self,
        state: StreamOBCacheLayerState,
        q: Tensor,
        num_new_tokens: int,
        patch_start_idx: int,
        obcache_cfg: Dict[str, Any],
        attn_mask: Optional[Tensor] = None,
    ) -> None:
        """
        Probe/full scoring path for OBCache.

        Shapes:
          q        : [B, H, P, D] (current-frame queries)
          state.k  : [B, H, L, D] (flattened cache, historical + current)
          state.v  : [B, H, L, D]
          A_probe  : [B, H, Q_probe, L]

        Important: Q_probe can be much smaller than P. We therefore pass
        `num_new_tokens=P` to tracker.update() so accumulation boundaries are
        aligned with appended KV tokens rather than probe count.
        """
        with torch.no_grad():
            probe_idx = select_probe_indices(
                num_tokens=q.size(-2),
                patch_start_idx=patch_start_idx,
                cfg=obcache_cfg,
                device=q.device,
            )
            q_probe = q.index_select(dim=-2, index=probe_idx)  # [B,H,Q_probe,D]

            qk_probe = torch.matmul(q_probe.float(), state.k.transpose(-2, -1).float()) / math.sqrt(self.head_dim)
            if attn_mask is not None:
                mask_probe = attn_mask[..., probe_idx, : state.k.size(-2)]
                qk_probe = qk_probe + mask_probe.float()

            # Float32 softmax for numerical stability.
            A_probe = torch.softmax(qk_probe, dim=-1, dtype=torch.float32)
            O_probe = torch.matmul(A_probe, state.v.float())

            state.tracker.update(
                A=A_probe,
                V=state.v.float(),
                qK=qk_probe,
                O=O_probe,
                num_new_tokens=num_new_tokens,
                layer_idx=0,
            )
            state.maybe_evict(num_coming=0)

    def forward(
        self,
        x: Tensor,
        pos: Optional[Tensor] = None,
        attn_mask: Optional[Tensor] = None,
        past_key_values: Optional[Union[Tuple[Tensor, Tensor], StreamOBCacheLayerState]] = None,
        use_cache: bool = False,
        obcache_cfg: Optional[Dict[str, Any]] = None,
        patch_start_idx: int = 0,
    ) -> Union[Tensor, Tuple[Tensor, Union[Tuple[Tensor, Tensor], StreamOBCacheLayerState]]]:
        B, N, C = x.shape

        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k_new, v_new = qkv.unbind(0)  # q/k_new/v_new: [B,H,P,D], P=N

        # Normalize and apply RoPE for current-frame tokens only.
        q = self.q_norm(q)
        k_new = self.k_norm(k_new)
        if self.rope is not None:
            q = self.rope(q, pos)
            k_new = self.rope(k_new, pos)

        state: Optional[StreamOBCacheLayerState] = None
        if use_cache:
            if isinstance(past_key_values, StreamOBCacheLayerState):
                state = past_key_values
                k_all = torch.cat([state.k, k_new], dim=-2)
                v_all = torch.cat([state.v, v_new], dim=-2)
            elif past_key_values is not None:
                past_k, past_v = past_key_values
                k_all = torch.cat([past_k, k_new], dim=-2)
                v_all = torch.cat([past_v, v_new], dim=-2)
            else:
                k_all, v_all = k_new, v_new
        else:
            k_all, v_all = k_new, v_new

        if self.fused_attn:
            out = F.scaled_dot_product_attention(
                q,
                k_all,
                v_all,
                attn_mask=attn_mask,
                dropout_p=self.attn_drop.p if self.training else 0.0,
            )
        else:
            q_scaled = q * self.scale
            attn = q_scaled @ k_all.transpose(-2, -1)
            if attn_mask is not None:
                expected = (N, k_all.size(-2))
                assert attn_mask.shape[-2:] == expected, f"Expected mask shape [...,{expected[0]},{expected[1]}], got {attn_mask.shape}"
                attn = attn + attn_mask
            attn = attn.softmax(dim=-1, dtype=torch.float32).to(q.dtype)
            attn = self.attn_drop(attn)
            out = attn @ v_all

        out = out.transpose(1, 2).reshape(B, N, C)
        out = self.proj(out)
        out = self.proj_drop(out)

        if not use_cache:
            return out

        obcache_enabled = bool(obcache_cfg and obcache_cfg.get("enable", False))
        if not obcache_enabled:
            return out, (k_all, v_all)

        if state is None:
            state = self._init_obcache_state(
                k_all=k_all,
                v_all=v_all,
                num_new_tokens=N,
                obcache_cfg=obcache_cfg,
            )
        else:
            old_len = int(state.seq_len)
            state.k = k_all
            state.v = v_all
            state.frame_count += 1
            state.reused_tokens_total += old_len
            state.appended_tokens_total += int(N)
            state.max_seq_len_seen = max(state.max_seq_len_seen, int(k_all.size(-2)))

        self._update_scores_and_maybe_evict(
            state=state,
            q=q,
            num_new_tokens=N,
            patch_start_idx=patch_start_idx,
            obcache_cfg=obcache_cfg,
            attn_mask=attn_mask,
        )
        return out, state


class MemEffAttention(Attention):
    def forward(self, x: Tensor, attn_bias=None, pos=None) -> Tensor:
        assert pos is None
        if not XFORMERS_AVAILABLE:
            if attn_bias is not None:
                raise AssertionError("xFormers is required for using nested tensors")
            return super().forward(x)

        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, C // self.num_heads)

        q, k, v = unbind(qkv, 2)

        x = memory_efficient_attention(q, k, v, attn_bias=attn_bias)
        x = x.reshape([B, N, C])

        x = self.proj(x)
        x = self.proj_drop(x)

        return x
