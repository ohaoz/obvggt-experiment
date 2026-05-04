import math
import time
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
from streamvggt.utils.phase_profile import phase_profile_end, phase_profile_start
from streamvggt.utils.runtime_diagnostics import (
    get_sdpa_backend_request,
    record_sdpa_call,
    resolve_sdpa_backend_for_call,
    sdpa_kernel_context,
)

XFORMERS_AVAILABLE = False


def _obcache_profile_enabled(obcache_cfg: Optional[Dict[str, Any]]) -> bool:
    if not obcache_cfg:
        return False
    return bool(obcache_cfg.get("profile", False) or obcache_cfg.get("profile_obcache", False))


def _profile_start(enabled: bool, reference: Tensor) -> Optional[float]:
    if not enabled:
        return None
    if reference.is_cuda:
        torch.cuda.synchronize(reference.device)
    return time.perf_counter()


def _profile_end(
    state: StreamOBCacheLayerState,
    name: str,
    start: Optional[float],
    reference: Tensor,
) -> None:
    if start is None:
        return
    if reference.is_cuda:
        torch.cuda.synchronize(reference.device)
    state.record_profile_event(name, (time.perf_counter() - start) * 1000.0)


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
        self._probe_index_cache: Dict[Tuple[int, int, bool, int, str, Optional[int]], Tensor] = {}

    def _select_probe_indices_cached(
        self,
        num_tokens: int,
        patch_start_idx: int,
        obcache_cfg: Dict[str, Any],
        device: torch.device,
    ) -> Tensor:
        if not bool(obcache_cfg.get("cache_probe_indices", True)):
            return select_probe_indices(
                num_tokens=num_tokens,
                patch_start_idx=patch_start_idx,
                cfg=obcache_cfg,
                device=device,
            )

        key = (
            int(num_tokens),
            int(patch_start_idx),
            bool(obcache_cfg.get("probe_mode", True)),
            int(obcache_cfg.get("num_patch_probes", 8)),
            device.type,
            device.index,
        )
        probe_idx = self._probe_index_cache.get(key)
        if probe_idx is None:
            probe_idx = select_probe_indices(
                num_tokens=num_tokens,
                patch_start_idx=patch_start_idx,
                cfg=obcache_cfg,
                device=device,
            )
            self._probe_index_cache[key] = probe_idx
        return probe_idx

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
        method = (obcache_cfg.get("method", "joint")).lower()
        if method == "sliding_window":
            tracker = None
        else:
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
        if bool(obcache_cfg.get("prealloc_kv", False)):
            state.enable_prealloc(append_tokens=num_new_tokens)
        return state

    @staticmethod
    def _score_interval_due(state: StreamOBCacheLayerState, obcache_cfg: Dict[str, Any]) -> bool:
        interval = max(1, int(obcache_cfg.get("score_interval", 1)))
        if interval <= 1:
            return True
        if state.scored_frame_count <= 0:
            return True
        return (int(state.frame_count) - int(state.scored_frame_count)) >= interval

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
        profile_enabled = _obcache_profile_enabled(obcache_cfg)
        total_start = _profile_start(profile_enabled, q)
        total_phase = phase_profile_start("obcache_score_total", q)
        if state.tracker is None:
            # Sliding window: no scoring, just evict by truncation.
            evict_start = _profile_start(profile_enabled, q)
            evict_phase = phase_profile_start("obcache_evict", q)
            state.maybe_evict(num_coming=0)
            _profile_end(state, "evict", evict_start, q)
            phase_profile_end(evict_phase, q)
            _profile_end(state, "score_total", total_start, q)
            phase_profile_end(total_phase, q)
            return

        if not self._score_interval_due(state, obcache_cfg):
            if profile_enabled:
                state.record_profile_event("score_skipped", 0.0)
            _profile_end(state, "score_total", total_start, q)
            phase_profile_end(total_phase, q)
            return

        with torch.no_grad():
            num_score_new_tokens = max(int(state.seq_len) - int(state.scored_seq_len), int(num_new_tokens))
            probe_start = _profile_start(profile_enabled, q)
            probe_phase = phase_profile_start("obcache_probe_select", q)
            probe_idx = self._select_probe_indices_cached(
                num_tokens=q.size(-2),
                patch_start_idx=patch_start_idx,
                obcache_cfg=obcache_cfg,
                device=q.device,
            )
            q_probe = q.index_select(dim=-2, index=probe_idx)  # [B,H,Q_probe,D]
            _profile_end(state, "probe_select", probe_start, q)
            phase_profile_end(probe_phase, q)

            qk_start = _profile_start(profile_enabled, q)
            qk_phase = phase_profile_start("obcache_probe_qk", q)
            qk_probe = torch.matmul(q_probe.float(), state.k.transpose(-2, -1).float()) / math.sqrt(self.head_dim)
            if attn_mask is not None:
                mask_probe = attn_mask[..., probe_idx, : state.k.size(-2)]
                qk_probe = qk_probe + mask_probe.float()
            _profile_end(state, "probe_qk", qk_start, q)
            phase_profile_end(qk_phase, q)

            # Float32 softmax for numerical stability.
            softmax_start = _profile_start(profile_enabled, q)
            softmax_phase = phase_profile_start("obcache_probe_softmax_value", q)
            v_float = state.v.float()
            A_probe = torch.softmax(qk_probe, dim=-1, dtype=torch.float32)
            O_probe = torch.matmul(A_probe, v_float)
            _profile_end(state, "probe_softmax_value", softmax_start, q)
            phase_profile_end(softmax_phase, q)

            update_start = _profile_start(profile_enabled, q)
            update_phase = phase_profile_start("obcache_tracker_update", q)
            state.tracker.update(
                A=A_probe,
                V=v_float,
                qK=qk_probe,
                O=O_probe,
                num_new_tokens=num_score_new_tokens,
                layer_idx=0,
            )
            _profile_end(state, "tracker_update", update_start, q)
            phase_profile_end(update_phase, q)

            evict_start = _profile_start(profile_enabled, q)
            evict_phase = phase_profile_start("obcache_evict", q)
            state.maybe_evict(num_coming=0)
            _profile_end(state, "evict", evict_start, q)
            phase_profile_end(evict_phase, q)
            state.scored_seq_len = int(state.seq_len)
            state.scored_frame_count = int(state.frame_count)
            _profile_end(state, "score_total", total_start, q)
            phase_profile_end(total_phase, q)

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
        previous_seq_len: int = 0
        obcache_enabled = bool(use_cache and obcache_cfg and obcache_cfg.get("enable", False))
        if use_cache:
            profile_enabled = _obcache_profile_enabled(obcache_cfg)
            cache_append_start = _profile_start(profile_enabled, x)
            cache_append_phase = phase_profile_start("obcache_cache_append", x) if obcache_enabled else None
            if isinstance(past_key_values, StreamOBCacheLayerState):
                state = past_key_values
                previous_seq_len = int(state.seq_len)
                state.append_kv(k_new, v_new)
                k_all, v_all = state.k, state.v
            elif past_key_values is not None:
                past_k, past_v = past_key_values
                k_all = torch.cat([past_k, k_new], dim=-2)
                v_all = torch.cat([past_v, v_new], dim=-2)
            else:
                k_all, v_all = k_new, v_new
        else:
            k_all, v_all = k_new, v_new

        if self.fused_attn:
            dropout_p = self.attn_drop.p if self.training else 0.0
            sdpa_backend_request = get_sdpa_backend_request()
            sdpa_backend_effective = resolve_sdpa_backend_for_call(
                sdpa_backend_request, q, k_all, v_all, attn_mask
            )
            record_sdpa_call(
                q,
                k_all,
                v_all,
                attn_mask=attn_mask,
                dropout_p=dropout_p,
                backend_request=sdpa_backend_request,
                backend_effective=sdpa_backend_effective,
            )
            sdpa_phase = phase_profile_start("sdpa_total", q)
            with sdpa_kernel_context(sdpa_backend_effective):
                out = F.scaled_dot_product_attention(
                    q,
                    k_all,
                    v_all,
                    attn_mask=attn_mask,
                    dropout_p=dropout_p,
                )
            phase_profile_end(sdpa_phase, q)
        else:
            fallback_phase = phase_profile_start("attention_fallback_total", q)
            q_scaled = q * self.scale
            attn = q_scaled @ k_all.transpose(-2, -1)
            if attn_mask is not None:
                expected = (N, k_all.size(-2))
                assert attn_mask.shape[-2:] == expected, f"Expected mask shape [...,{expected[0]},{expected[1]}], got {attn_mask.shape}"
                attn = attn + attn_mask
            attn = attn.softmax(dim=-1, dtype=torch.float32).to(q.dtype)
            attn = self.attn_drop(attn)
            out = attn @ v_all
            phase_profile_end(fallback_phase, q)

        out = out.transpose(1, 2).reshape(B, N, C)
        out = self.proj(out)
        out = self.proj_drop(out)

        if not use_cache:
            return out

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
            state.frame_count += 1
            state.reused_tokens_total += previous_seq_len
            state.appended_tokens_total += int(N)
            state.max_seq_len_seen = max(state.max_seq_len_seen, int(k_all.size(-2)))

        _profile_end(state, "cache_append", cache_append_start, x)
        phase_profile_end(cache_append_phase, x)
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
