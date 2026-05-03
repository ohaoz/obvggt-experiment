import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import torch
from torch import Tensor


pooling_fn = {
    "maxpool": torch.nn.functional.max_pool1d,
    "avgpool": torch.nn.functional.avg_pool1d,
}


def _budget_is_defined(total_recent: Optional[int], total_heavy: Optional[int]) -> Tuple[int, int]:
    if total_recent is None or total_heavy is None:
        raise ValueError("Both `num_recent_tokens` and `num_heavy_tokens` must be defined.")
    return int(total_recent), int(total_heavy)


def take_gather(buf: Tensor, keep_topk_idx: Tensor, recent_cutoff: int, gather_dim: int = -2) -> Tensor:
    """
    Gather helper for KV cache and score tensors.

    Args:
        buf:            KV cache or score tensor.
        keep_topk_idx:  [B, H, K] heavy-token indices selected from historical range [0, recent_cutoff).
        recent_cutoff:  split point between historical and recent region.
        gather_dim:     -2 for KV cache [B,H,L,D], -1 for scores [B,H,L].
    """
    if gather_dim == -1:
        if buf.dim() == keep_topk_idx.dim():
            select_buf = buf[..., :recent_cutoff]  # [B,H,recent_cutoff]
            keep_recent = buf[..., recent_cutoff:]  # [B,H,recent]
        elif buf.dim() == keep_topk_idx.dim() + 1:
            select_buf = buf[..., :recent_cutoff]  # [B,H,Q,recent_cutoff]
            keep_recent = buf[..., recent_cutoff:]  # [B,H,Q,recent]
            keep_topk_idx = keep_topk_idx.unsqueeze(-2).expand(-1, -1, buf.size(-2), -1)
        else:
            raise ValueError(f"Unsupported score tensor rank: {buf.dim()}")
    elif gather_dim == -2:
        select_buf = buf[..., :recent_cutoff, :]  # [B,H,recent_cutoff,D]
        keep_recent = buf[..., recent_cutoff:, :]  # [B,H,recent,D]
        keep_topk_idx = keep_topk_idx.unsqueeze(-1).expand(-1, -1, -1, buf.size(-1))
    else:
        raise ValueError(f"Unsupported gather_dim={gather_dim}")

    selected = torch.gather(select_buf, dim=gather_dim, index=keep_topk_idx)
    if keep_recent.size(gather_dim) == 0:
        return selected
    return torch.cat([selected, keep_recent], dim=gather_dim)


def _resolve_mode_flags(method: str) -> Tuple[bool, bool, bool]:
    m = (method or "joint").lower()
    if m in {"v", "obcv"}:
        return True, False, False
    if m in {"key", "k", "obck"}:
        return False, True, False
    if m in {"joint", "vk", "obcvk"}:
        return True, True, True
    if m == "random":
        return False, False, False
    raise ValueError(f"Unknown OBC scoring method: {method}")


def resolve_token_budgets(cfg: Dict[str, Any], tokens_per_frame: int) -> Tuple[int, int, int]:
    """
    Resolve token budgets from either token-level fields or frame-level fields.

    Frame-level defaults:
        sink_tokens   = num_sink_frames   * P
        recent_tokens = num_recent_frames * P
        heavy_tokens  = (num_sink_frames + num_heavy_frames) * P
    """
    if cfg is None:
        cfg = {}

    num_sink_tokens = cfg.get("num_sink_tokens")
    num_recent_tokens = cfg.get("num_recent_tokens")
    num_heavy_tokens = cfg.get("num_heavy_tokens")

    if num_sink_tokens is None or num_recent_tokens is None or num_heavy_tokens is None:
        sink_frames = int(cfg.get("num_sink_frames", 1))
        recent_frames = int(cfg.get("num_recent_frames", 2))
        heavy_frames = int(cfg.get("num_heavy_frames", 4))
        num_sink_tokens = sink_frames * tokens_per_frame
        num_recent_tokens = recent_frames * tokens_per_frame
        num_heavy_tokens = (sink_frames + heavy_frames) * tokens_per_frame

    num_sink_tokens = int(num_sink_tokens)
    num_recent_tokens = int(num_recent_tokens)
    num_heavy_tokens = int(num_heavy_tokens)

    if num_heavy_tokens < num_sink_tokens:
        num_heavy_tokens = num_sink_tokens

    return num_sink_tokens, num_recent_tokens, num_heavy_tokens


def build_tracker_from_cfg(
    cfg: Dict[str, Any], num_sink_tokens: int
) -> "StreamOBCScoreTracker":
    method = (cfg.get("method", "joint")).lower()
    if method == "random":
        return RandomEvictionTracker(num_sink=num_sink_tokens)

    use_v_score, use_k_score, use_cross = _resolve_mode_flags(method)

    p = int(cfg.get("p", 1 if (use_v_score and not use_k_score) else 2))
    use_vnorm_default = False if (use_v_score and not use_k_score) else True
    use_vnorm = bool(cfg.get("use_vnorm", use_vnorm_default))
    pool_fn = cfg.get("pool_fn")
    ptb_window = cfg.get("ptb_window")
    ptb_is_recent = bool(cfg.get("ptb_is_recent", False))

    return StreamOBCScoreTracker(
        use_v_score=use_v_score,
        use_k_score=use_k_score,
        use_cross=use_cross,
        p=p,
        use_vnorm=use_vnorm,
        ptb_window=ptb_window,
        pool_fn=pool_fn,
        ptb_is_recent=ptb_is_recent,
        num_sink=num_sink_tokens,
    )


def select_probe_indices(
    num_tokens: int,
    patch_start_idx: int,
    cfg: Dict[str, Any],
    device: torch.device,
) -> Tensor:
    """
    Default probe policy:
      - always keep special tokens [0, patch_start_idx)
      - plus a small evenly-spaced subset from patch tokens
    """
    probe_mode = bool(cfg.get("probe_mode", True))
    if not probe_mode:
        return torch.arange(num_tokens, device=device, dtype=torch.long)

    patch_start = max(0, min(int(patch_start_idx), num_tokens))
    special = torch.arange(patch_start, device=device, dtype=torch.long)

    num_patch_probes = int(cfg.get("num_patch_probes", 8))
    if num_patch_probes <= 0 or patch_start >= num_tokens:
        return special

    patch_indices = torch.arange(patch_start, num_tokens, device=device, dtype=torch.long)
    if patch_indices.numel() <= num_patch_probes:
        probes = patch_indices
    else:
        sample_pos = torch.linspace(
            0,
            patch_indices.numel() - 1,
            steps=num_patch_probes,
            device=device,
        ).long()
        probes = patch_indices[sample_pos]

    return torch.unique(torch.cat([special, probes], dim=0), sorted=True)


@dataclass
class StreamOBCacheLayerState:
    # Flattened cache shape for StreamVGGT: [B, H, L, D]
    k: Tensor
    v: Tensor
    tracker: Optional["StreamOBCScoreTracker"] = None
    num_recent_tokens: Optional[int] = None
    num_heavy_tokens: Optional[int] = None
    num_sink_tokens: int = 0
    tokens_per_frame: Optional[int] = None
    frame_count: int = 1
    evict_calls: int = 0
    evicted_tokens_total: int = 0
    appended_tokens_total: int = 0
    reused_tokens_total: int = 0
    max_seq_len_seen: int = 0
    scored_seq_len: int = 0
    scored_frame_count: int = 0
    profile_times_ms: Optional[Dict[str, float]] = None
    profile_counts: Optional[Dict[str, int]] = None

    @property
    def seq_len(self) -> int:
        return int(self.k.size(-2))

    @property
    def max_cache_tokens(self) -> Optional[int]:
        if self.num_recent_tokens is None or self.num_heavy_tokens is None:
            return None
        return int(self.num_recent_tokens + self.num_heavy_tokens)

    def maybe_evict(self, num_coming: int = 0) -> None:
        if self.tracker is None:
            # Sliding window: truncate to budget without scoring.
            n_recent, n_heavy = _budget_is_defined(self.num_recent_tokens, self.num_heavy_tokens)
            max_cache = n_recent + n_heavy
            if self.seq_len + num_coming <= max_cache:
                return
            before_len = int(self.seq_len)
            self.max_seq_len_seen = max(self.max_seq_len_seen, before_len)
            keep = max(max_cache - num_coming, 0)
            if keep > 0:
                self.k = self.k[..., -keep:, :]
                self.v = self.v[..., -keep:, :]
            else:
                self.k = self.k[..., :0, :]
                self.v = self.v[..., :0, :]
            after_len = int(self.seq_len)
            self.evict_calls += 1
            self.evicted_tokens_total += max(before_len - after_len, 0)
            return

        n_recent, n_heavy = _budget_is_defined(self.num_recent_tokens, self.num_heavy_tokens)
        max_cache = n_recent + n_heavy
        if self.seq_len + num_coming <= max_cache:
            return

        before_len = int(self.seq_len)
        self.max_seq_len_seen = max(self.max_seq_len_seen, before_len)
        recent_cutoff = self.seq_len - n_recent + num_coming
        keep_topk_idx = self.tracker.evict(
            num_recent_tokens=n_recent,
            num_heavy_tokens=n_heavy,
            num_coming=num_coming,
            layer_idx=0,
        ).to(self.k.device)

        self.k = take_gather(self.k, keep_topk_idx, recent_cutoff, gather_dim=-2)
        self.v = take_gather(self.v, keep_topk_idx, recent_cutoff, gather_dim=-2)
        after_len = int(self.seq_len)
        self.evict_calls += 1
        self.evicted_tokens_total += max(before_len - after_len, 0)

    def record_profile_event(self, name: str, elapsed_ms: float) -> None:
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in str(name).strip().lower()).strip("_")
        if not safe_name:
            return
        if self.profile_times_ms is None:
            self.profile_times_ms = {}
        if self.profile_counts is None:
            self.profile_counts = {}
        self.profile_times_ms[safe_name] = self.profile_times_ms.get(safe_name, 0.0) + float(elapsed_ms)
        self.profile_counts[safe_name] = self.profile_counts.get(safe_name, 0) + 1

    def snapshot(self) -> Dict[str, float]:
        denom = self.reused_tokens_total + self.appended_tokens_total
        reuse_ratio = float(self.reused_tokens_total / denom) if denom > 0 else 0.0
        snap = {
            "frame_count": float(self.frame_count),
            "seq_len": float(self.seq_len),
            "max_seq_len_seen": float(self.max_seq_len_seen),
            "evict_calls": float(self.evict_calls),
            "evicted_tokens_total": float(self.evicted_tokens_total),
            "appended_tokens_total": float(self.appended_tokens_total),
            "reused_tokens_total": float(self.reused_tokens_total),
            "cache_reuse_ratio": reuse_ratio,
            "scored_seq_len": float(self.scored_seq_len),
            "scored_frame_count": float(self.scored_frame_count),
        }
        if self.profile_times_ms:
            for name, elapsed_ms in self.profile_times_ms.items():
                snap[f"profile_{name}_ms"] = float(elapsed_ms)
                snap[f"profile_{name}_calls"] = float((self.profile_counts or {}).get(name, 0))
        return snap


class RandomEvictionTracker:
    """Random eviction baseline: selects heavy tokens randomly from history."""

    def __init__(self, num_sink: int = 0) -> None:
        self.num_sink = int(num_sink)
        self._shape: Optional[Tuple[int, int, int]] = None  # (B, H, L)
        self._device: torch.device = torch.device("cpu")

    @torch.no_grad()
    def update(
        self,
        A: Optional[Tensor] = None,
        V: Optional[Tensor] = None,
        qK: Optional[Tensor] = None,
        O: Optional[Tensor] = None,
        num_new_tokens: int = 0,
        layer_idx: int = 0,
        Q: Optional[Tensor] = None,
        K: Optional[Tensor] = None,
    ) -> None:
        if V is not None:
            self._shape = (V.size(0), V.size(1), V.size(-2))
            self._device = V.device

    @torch.no_grad()
    def evict(
        self,
        num_recent_tokens: int,
        num_heavy_tokens: int,
        num_coming: int,
        layer_idx: int,
    ) -> Tensor:
        if self._shape is None:
            raise RuntimeError("RandomEvictionTracker.evict() called before update().")
        B, H, seq_len = self._shape

        if num_coming >= num_recent_tokens:
            num_heavy_tokens -= num_coming - num_recent_tokens
            num_heavy_tokens = max(num_heavy_tokens, 0)

        recent_cutoff = seq_len - num_recent_tokens + num_coming
        topk = min(int(num_heavy_tokens), int(recent_cutoff))

        if topk <= 0:
            return torch.empty(B, H, 0, device=self._device, dtype=torch.long)

        sink_end = min(self.num_sink, recent_cutoff)

        if topk <= sink_end:
            idx = torch.arange(topk, device=self._device, dtype=torch.long)
            return idx.unsqueeze(0).unsqueeze(0).expand(B, H, -1)

        # Always keep sink tokens; randomly select the rest from non-sink history.
        candidates = recent_cutoff - sink_end
        num_to_select = min(topk - sink_end, candidates)

        rand_scores = torch.rand(B, H, candidates, device=self._device)
        _, random_idx = rand_scores.topk(num_to_select, dim=-1)
        random_idx = random_idx + sink_end  # offset past sink region

        sink_idx = torch.arange(sink_end, device=self._device, dtype=torch.long)
        sink_idx = sink_idx.unsqueeze(0).unsqueeze(0).expand(B, H, -1)
        idx = torch.cat([sink_idx, random_idx], dim=-1)
        return idx.sort(dim=-1).values

    def reset(self) -> None:
        self._shape = None


class StreamOBCScoreTracker:
    """
    StreamVGGT-tailored OBC score tracker.

    Key difference from the original LLM-oriented implementation:
    `num_new_tokens` is passed explicitly to decouple:
      - number of appended KV tokens (P, per-frame tokens),
      - number of probe queries used for scoring (Q_probe).
    In probe mode Q_probe << P, so accumulation boundaries must use P.
    """

    def __init__(
        self,
        use_v_score: bool = True,
        use_k_score: bool = True,
        use_cross: bool = True,
        p: int = 2,
        use_vnorm: bool = True,
        ptb_window: Optional[int] = None,
        pool_fn: Optional[str] = None,
        ptb_is_recent: bool = False,
        num_sink: int = 0,
    ) -> None:
        self.use_v_score = bool(use_v_score)
        self.use_k_score = bool(use_k_score)
        self.use_cross = bool(use_cross)
        self.p = int(p)
        self.use_vnorm = bool(use_vnorm)
        self.pool_fn = pool_fn
        self.ptb_is_recent = bool(ptb_is_recent)
        self.num_sink = int(num_sink)
        self.ptb_window = int(ptb_window) if ptb_window is not None else None

        if self.use_v_score:
            self.Sattn_all: List[Tensor] = []
            if self.use_vnorm:
                self.Vnormp_all: List[Tensor] = []
        if self.use_k_score:
            self.Skey_all: List[Tensor] = []

    @torch.no_grad()
    def retrieve_score(self, layer_idx: int) -> Tensor:
        score: Optional[Tensor] = None
        if self.use_v_score:
            score = self.Sattn_all[layer_idx]
            if self.use_vnorm:
                score = score * self.Vnormp_all[layer_idx]
        if self.use_k_score:
            k_score = self.Skey_all[layer_idx]
            score = k_score if score is None else (score + k_score)
        if score is None:
            raise RuntimeError("No score is available. Enable v_score and/or k_score.")
        return score

    @torch.no_grad()
    def _accumulate_with_new_token_count(self, prev: Tensor, curr: Tensor, num_new_tokens: int) -> Tensor:
        if self.ptb_is_recent and self.ptb_window == 1:
            return curr

        hist_len = max(curr.size(-1) - int(num_new_tokens), 0)
        if hist_len > 0:
            overlap = min(hist_len, prev.size(-1))
            curr[..., :overlap] += prev[..., :overlap]
        return curr

    @torch.no_grad()
    def update(
        self,
        A: Optional[Tensor],
        V: Tensor,
        qK: Optional[Tensor],
        O: Optional[Tensor],
        num_new_tokens: int,
        layer_idx: int = 0,
        Q: Optional[Tensor] = None,
        K: Optional[Tensor] = None,
    ) -> None:
        if num_new_tokens <= 0:
            raise ValueError("`num_new_tokens` must be positive.")

        if A is None:
            if Q is None or K is None:
                raise ValueError("When A is None, Q and K must be provided.")
            qK = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(Q.size(-1))
            A = torch.softmax(qK, dim=-1, dtype=torch.float32)

        if self.ptb_window is not None and A.size(-2) > self.ptb_window:
            A = A[..., -self.ptb_window :, :]
            if qK is not None:
                qK = qK[..., -self.ptb_window :, :]
            if O is not None:
                O = O[..., -self.ptb_window :, :]

        if self.use_v_score:
            self.v_update(A=A, V=V, num_new_tokens=num_new_tokens, layer_idx=layer_idx)

        if self.use_k_score:
            if qK is None or O is None:
                raise ValueError("k_score requires both qK and O.")
            self.k_update(
                A=A,
                V=V,
                qK=qK,
                O=O,
                num_new_tokens=num_new_tokens,
                layer_idx=layer_idx,
            )

    @torch.no_grad()
    def v_update(self, A: Tensor, V: Tensor, num_new_tokens: int, layer_idx: int) -> None:
        # A: [B,H,Q_probe,L]
        A_normp = A.pow(self.p).sum(dim=-2)  # [B,H,L]

        if len(self.Sattn_all) <= layer_idx:
            self.Sattn_all.append(A_normp)
        else:
            prev = self.Sattn_all[layer_idx]
            self.Sattn_all[layer_idx] = self._accumulate_with_new_token_count(prev, A_normp, num_new_tokens)

        if self.use_vnorm:
            if self.p == 1:
                V_normp_new = V[..., -num_new_tokens:, :].abs().sum(dim=-1)
            else:
                V_normp_new = V[..., -num_new_tokens:, :].pow(self.p).sum(dim=-1)

            if len(self.Vnormp_all) <= layer_idx:
                self.Vnormp_all.append(V_normp_new)
            else:
                self.Vnormp_all[layer_idx] = torch.cat([self.Vnormp_all[layer_idx], V_normp_new], dim=-1)

    @torch.no_grad()
    def k_update(self, A: Tensor, V: Tensor, qK: Tensor, O: Tensor, num_new_tokens: int, layer_idx: int) -> None:
        # A,qK: [B,H,Q_probe,L], O: [B,H,Q_probe,D], V: [B,H,L,D]
        if self.use_v_score and self.use_vnorm:
            V_normp = self.Vnormp_all[layer_idx]
        else:
            V_normp = V.pow(2).sum(dim=-1)
        O_normp = O.pow(2).sum(dim=-1)

        VO = torch.einsum("bhqd,bhkd->bhqk", O, V)
        VmO_normp = V_normp[..., None, :] + O_normp[..., :, None] - 2.0 * VO
        S_key = (A * qK).pow(2) * VmO_normp
        S_key = S_key.sum(dim=-2)

        if self.use_v_score and self.use_cross:
            VVmO = V_normp[..., None, :] - VO
            S_cross = 2.0 * A.pow(2) * qK * VVmO
            S_cross = S_cross.sum(dim=-2)
            S_key = S_key + S_cross

        if len(self.Skey_all) <= layer_idx:
            self.Skey_all.append(S_key)
        else:
            prev = self.Skey_all[layer_idx]
            self.Skey_all[layer_idx] = self._accumulate_with_new_token_count(prev, S_key, num_new_tokens)

    @torch.no_grad()
    def evict(
        self,
        num_recent_tokens: int,
        num_heavy_tokens: int,
        num_coming: int,
        layer_idx: int,
    ) -> Tensor:
        score = self.retrieve_score(layer_idx)
        _, _, seq_len = score.shape

        if num_coming >= num_recent_tokens:
            num_heavy_tokens -= (num_coming - num_recent_tokens)
            num_heavy_tokens = max(num_heavy_tokens, 0)

        recent_cutoff = seq_len - num_recent_tokens + num_coming
        score_to_select = score[..., :recent_cutoff]

        if self.pool_fn in pooling_fn and score_to_select.size(-1) > 0:
            score_to_select = pooling_fn[self.pool_fn](score_to_select, kernel_size=7, padding=3, stride=1)

        if self.num_sink > 0 and recent_cutoff > 0:
            sink_end = min(self.num_sink, recent_cutoff)
            score_to_select[:, :, :sink_end] = torch.finfo(score_to_select.dtype).max

        topk = min(int(num_heavy_tokens), int(score_to_select.size(-1)))
        if topk > 0:
            _, keep_topk_idx = torch.topk(score_to_select, topk, dim=-1)
            keep_topk_idx = keep_topk_idx.sort().values
        else:
            keep_topk_idx = torch.empty(
                score_to_select.size(0),
                score_to_select.size(1),
                0,
                device=score_to_select.device,
                dtype=torch.long,
            )

        if self.use_v_score:
            if not (self.ptb_is_recent and self.ptb_window == 1):
                self.Sattn_all[layer_idx] = take_gather(
                    self.Sattn_all[layer_idx], keep_topk_idx, recent_cutoff, gather_dim=-1
                )
            if self.use_vnorm:
                self.Vnormp_all[layer_idx] = take_gather(
                    self.Vnormp_all[layer_idx], keep_topk_idx, recent_cutoff, gather_dim=-1
                )

        if self.use_k_score and not (self.ptb_is_recent and self.ptb_window == 1):
            self.Skey_all[layer_idx] = take_gather(
                self.Skey_all[layer_idx], keep_topk_idx, recent_cutoff, gather_dim=-1
            )

        return keep_topk_idx

    def reset(self) -> None:
        if self.use_v_score:
            self.Sattn_all.clear()
            if self.use_vnorm:
                self.Vnormp_all.clear()
        if self.use_k_score:
            self.Skey_all.clear()
