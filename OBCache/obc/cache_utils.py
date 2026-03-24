"""
Inherited from Cache class in github.com/huggingface/transformers/blob/main/src/transformers/cache_utils.py
Requires transformers==4.47.0
New cache eviction functionality: 
    - SinkCache (re-implemented)
    - H2O & TOVA & SnapKV  (special case of OBCache)
    - OBCache (our method)
Needs to be used with modified attention forward functions in monkey_patch/llama.py
"""
import torch
import warnings
import math
from torch import Tensor
from typing import Any, Dict, List, Optional, Tuple
from transformers.cache_utils import Cache




class SinkCache(Cache):
    """
    Keep a small 'sink' prefix and the most recent tokens; evict the middle.

    Kept tokens after eviction (per layer):
        [ : num_sink_tokens ] + [ recent_cutoff : ]

    Configure by absolute counts (num_recent/num_heavy) or by ratios on the first
    `update()` call (recent_ratio/heavy_ratio). Ratios are applied to the number
    of tokens in the very first `update()` (i.e., prompt length).

    Args:
        num_recent: number of recent tokens to keep
        num_heavy: number of sink tokens to keep
        cache_ratio: fixed cache ratio of prompt length, required when fix_sink_token is True
    """
    def __init__(
        self,
        num_recent: Optional[int] = None,
        num_heavy: Optional[int] = None,
        fix_sink_token: bool = False,
        cache_ratio: float = None,  # fixed cache ratio of prompt length, required when fix_sink is True
    ) -> None:
        super().__init__()
        self.key_cache: List[torch.Tensor] = []
        self.value_cache: List[torch.Tensor] = []

        self.num_recent_tokens: Optional[int] = num_recent
        self.num_sink_tokens: Optional[int] = num_heavy

        self.fix_sink_token = fix_sink_token
        if self.fix_sink_token:
            self.num_recent_tokens = None
            assert cache_ratio is not None, "When fix_sink_token is True, cache_ratio should be provided."
            self.cache_ratio = cache_ratio

        self._seen_tokens = 0  # Used in `generate` to keep tally of how many tokens the cache has seen

    def get_seq_length(self, layer_idx: Optional[int] = 0) -> int:
        """Returns the sequence length of the cached states. A layer index can be optionally passed."""
        if len(self.key_cache) <= layer_idx:
            return 0
        return self.key_cache[layer_idx].shape[-2]

    def get_max_cache_shape(self) -> Optional[int]:
        """Returns the maximum sequence length of the cache object, in case of H2OCache it is the window length."""
        return self.num_recent_tokens + self.num_sink_tokens

    def update(
        self,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        layer_idx: int,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Concatenate new keys/values to the cache.

        Shapes:
            key_states:   [bsz, num_kv_heads, q_len, head_dim]
            value_states: [bsz, num_kv_heads, q_len, head_dim]
        """
        num_coming = int(key_states.shape[-2])
        if layer_idx == 0:
            self._seen_tokens += num_coming

        if len(self.key_cache) <= layer_idx:
            ## Empty cache
            if hasattr(self, "cache_ratio"):
                kv_budget = int(num_coming * self.cache_ratio)
                self.num_recent_tokens = kv_budget - self.num_sink_tokens
                assert self.num_recent_tokens > 0, f"Cache ratio {self.cache_ratio} is too small for num_sink_tokens {self.num_sink_tokens}"
                _budget_is_defined(self.num_recent_tokens, self.num_sink_tokens)

            self.key_cache.append(key_states)
            self.value_cache.append(value_states)
        else:
            ## Growing cache
            self.key_cache[layer_idx] = torch.cat([self.key_cache[layer_idx], key_states], dim=-2)
            self.value_cache[layer_idx] = torch.cat([self.value_cache[layer_idx], value_states], dim=-2)

        return self.key_cache[layer_idx], self.value_cache[layer_idx]
    
    def evict(self, num_coming=0):
        """
        Evict middle tokens for all layers if (seq_len + num_coming) exceeds the budget.
        """
        seq_len = self.get_seq_length()
        if seq_len + num_coming <= self.get_max_cache_shape():
            return
        
        n_recent, n_sink = _budget_is_defined(self.num_recent_tokens, self.num_sink_tokens)
        recent_cutoff = seq_len - n_recent + num_coming
        for layer_idx in range(len(self.key_cache)):
            k = self.key_cache[layer_idx]
            v = self.value_cache[layer_idx]

            self.key_cache[layer_idx] = torch.cat(
                [
                    k[:, :, :n_sink], 
                    k[:, :, recent_cutoff:]
                ], dim=-2
            )
            self.value_cache[layer_idx] = torch.cat(
                [
                    v[:, :, :n_sink], 
                    v[:, :, recent_cutoff:]
                ], dim=-2
            )

    def reset(self):
        self.key_cache.clear()
        self.value_cache.clear()
        self._seen_tokens = 0

    def __repr__(self):
        return (
            "SinkCache("
            f"num_recent_tokens={self.num_recent_tokens}, "
            f"num_sink_tokens={self.num_sink_tokens}, "
            f"cache_ratio={getattr(self, 'cache_ratio', None)})"
        )


class OBCache(Cache):
    """
    Optimal Brain Cache (OBCache) implementation.
    Keeps `num_recent_tokens` most recent tokens and
    selects `num_heavy_tokens` highest-scoring historical tokens using `OBCScoreTracker`.

    Args:
        num_recent: number of recent tokens to keep
        num_heavy: number of heavy tokens to keep
        recent_ratio / heavy_ratio: if set, derive counts from first update prompt length
        decode_evict: if False, run `evict` only in prefilling phase
        fix_recent_token: if True, `num_recent_tokens` is fixed and `num_heavy_tokens`
            is derived from `cache_ratio * prompt_len - num_recent_tokens`
        cache_ratio: required when `fix_recent_token=True`
        **score_tracker_kwargs: OBCScoreTracker arguments
    """
    def __init__(
        self,
        num_recent: Optional[int] = None,
        num_heavy: Optional[int] = None,
        recent_ratio: Optional[float] = None,
        heavy_ratio: Optional[float] = None,
        decode_evict: bool = True,
        fix_recent_token: bool = False,
        cache_ratio: Optional[float] = None,
        **score_tracker_kwargs: Any,
    ) -> None:
        super().__init__()
        
        self.key_cache: List[torch.Tensor] = []
        self.value_cache: List[torch.Tensor] = []   

        self.num_recent_tokens: Optional[int] = num_recent
        self.num_heavy_tokens: Optional[int] = num_heavy

        if recent_ratio is not None:
            self.recent_ratio = recent_ratio
        if heavy_ratio is not None:
            self.heavy_ratio = heavy_ratio

        self.score_tracker = OBCScoreTracker(**score_tracker_kwargs)

        self.fix_recent_token = fix_recent_token
        if self.fix_recent_token:
            if cache_ratio is None:
                raise ValueError(
                    "When `fix_recent_token=True`, `cache_ratio` must be provided."
                )
            if self.num_recent_tokens is None:
                raise ValueError(
                    "When `fix_recent_token=True`, `num_recent` must be provided."
                )
            self.cache_ratio = float(cache_ratio)
            self.num_heavy_tokens = None  # derived at first update()
    
        self._seen_tokens: int = 0
        self.decode_evict = bool(decode_evict)
        self.method = "default"

    def get_seq_length(self, layer_idx: Optional[int] = 0) -> int:
        """Returns the sequence length of the cached states. A layer index can be optionally passed."""
        if len(self.key_cache) <= layer_idx:
            return 0
        return self.key_cache[layer_idx].shape[-2]

    def get_max_cache_shape(self) -> Optional[int]:
        """Returns the maximum sequence length of the cache object, in case of H2OCache it is the window length."""
        return self.num_recent_tokens + self.num_heavy_tokens
    
    def update(
        self,
        key_states: Tensor,
        value_states: Tensor,
        layer_idx: int,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Tensor, Tensor]:
        """ Cache update method called in hf's attention forward """ 

        num_coming = int(key_states.shape[-2])
        if layer_idx == 0:
            self._seen_tokens += num_coming

        if len(self.key_cache) <= layer_idx:
            ## Empty cache
            if self.fix_recent_token:
                kv_budget = int(num_coming * self.cache_ratio)
                self.num_heavy_tokens = kv_budget - self.num_recent_tokens
                assert self.num_heavy_tokens > 0, f"Cache ratio {self.cache_ratio} is too small for num_recent_tokens {self.num_recent_tokens}"

            if hasattr(self, "recent_ratio") and hasattr(self, "heavy_ratio"):
                self.num_recent_tokens = int(num_coming * self.recent_ratio)
                self.num_heavy_tokens = int(num_coming * self.heavy_ratio)
                if not (
                    getattr(self.score_tracker, "ptb_window", None) == 1
                    and getattr(self.score_tracker, "ptb_is_recent", False)
                ):  # For non-tova methods, ptb_window=num_recent; otherwise, ptb_window=1 
                    self.score_tracker.ptb_window = self.num_recent_tokens

            _budget_is_defined(self.num_recent_tokens, self.num_heavy_tokens)
            
            self.key_cache.append(key_states)
            self.value_cache.append(value_states)
        else:
            ## Growing cache
            self.key_cache[layer_idx] = torch.cat([self.key_cache[layer_idx], key_states], dim=-2)
            self.value_cache[layer_idx] = torch.cat([self.value_cache[layer_idx], value_states], dim=-2)

        return self.key_cache[layer_idx], self.value_cache[layer_idx]

    def evict(self, layer_idx, num_coming=0):
        """
        Evict tokens for a single layer when exceeding budget using scores
        from `OBCScoreTracker`. Keeps:
            heavy (scored) + recent (tail).
        """
        seq_len = self.get_seq_length(layer_idx)
        if seq_len + num_coming <= self.get_max_cache_shape():
            return

        n_recent, n_heavy = _budget_is_defined(self.num_recent_tokens, self.num_heavy_tokens)
        recent_cutoff = seq_len - n_recent + num_coming

        k = self.key_cache[layer_idx]
        v = self.value_cache[layer_idx]

        keep_topk_idx = self.score_tracker.evict(
            n_recent, n_heavy, num_coming, layer_idx,
        ).to(k.device)

        self.key_cache[layer_idx] = take_gather(k, keep_topk_idx, recent_cutoff, gather_dim=-2)
        self.value_cache[layer_idx] = take_gather(v, keep_topk_idx, recent_cutoff, gather_dim=-2)

    def evict_all_layers(self, num_coming=0):
        for layer_idx in range(len(self.key_cache)):
            self.evict(layer_idx, num_coming=num_coming)

    def reset(self):
        self.key_cache.clear()
        self.value_cache.clear()
        self._seen_tokens = 0
        self.score_tracker.reset()

    def __repr__(self):
        return (
            f"------ OBCache Configuration (method={self.method}) ------\n"
            f"num_recent_tokens={self.num_recent_tokens}, "
            f"num_heavy_tokens={self.num_heavy_tokens}\n"
            f"recent_ratio={getattr(self, 'recent_ratio', None)}, "
            f"heavy_ratio={getattr(self, 'heavy_ratio', None)}, "
            f"cache_ratio={getattr(self, 'cache_ratio', None)}\n"
            f"use_v_score={self.score_tracker.use_v_score}, "
            f"use_k_score={self.score_tracker.use_k_score}, "
            f"use_cross={self.score_tracker.use_cross}\n"
            f"p={self.score_tracker.p}, use_vnorm={self.score_tracker.use_vnorm}\n"
            f"ptb_window={getattr(self.score_tracker, 'ptb_window', None)}, "
            f"ptb_is_recent={getattr(self.score_tracker, 'ptb_is_recent', None)}\n"
            f"pool_fn={self.score_tracker.pool_fn}, "
            f"decode_evict={self.decode_evict}\n"
            + "-"*len(f'------ OBCache Configuration (method={self.method}) -------')
        )


class OBCScoreTracker:
    """
    Tracks per-position scores used by OBCache to select heavy tokens.

    Args:
        use_v_score / use_k_score / use_cross (boolean): which score components to use
        p (int): p-norm for attention/activations
        use_vnorm (boolean): whether to include value cache norms in v_score
        ptb_window (int): size of perturbation window `s-w` (None -> accumulate all)
        pool_fn (str): smoothing function over scores; one of {None, 'maxpool', 'avgpool'}
        ptb_is_recent (boolean): treat ptb_window as "recent-only" (TOVA-like)
        num_sink (int): force-keep this many prefix tokens (never evict)

    When use_v_score=True, p=1, use_vnorm=False:
        OBCache reduces to pure attention-based methods (H2O, TOVA, SnapKV),
        where the score is the accumulated attention over different query positions.
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
    ):
        self.use_v_score = use_v_score
        self.use_k_score = use_k_score
        self.use_cross = use_cross
        self.p = int(p)
        self.use_vnorm = use_vnorm
        self.pool_fn = pool_fn
        self.ptb_is_recent = bool(ptb_is_recent)
        self.num_sink = int(num_sink)

        if ptb_window is not None:
            self.ptb_window = int(ptb_window)

        if self.use_v_score:
            self.Sattn_all: List[Tensor] = []  # [(bsz, heads, kv_len), ...]
            if self.use_vnorm:
                self.Vnormp_all: List[Tensor] = []  # [(bsz, heads, kv_len), ...]

        if self.use_k_score:
            self.Skey_all: List[Tensor] = []  # [(bsz, heads, kv_len), ...]

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
            raise RuntimeError("No scores available; enable v_score and/or k_score.")
        return score  # [bsz, heads, kv_len]

    @torch.no_grad()
    def update(
        self,
        A: Optional[Tensor],
        V: Optional[Tensor],
        qK: Optional[Tensor],
        O: Optional[Tensor],
        Q: Optional[Tensor] = None,
        K: Optional[Tensor] = None,
        layer_idx: int = 0,
    ) -> None:
        """
        Update OBCache scores (prefill or decode).

        Args:
            A: attn_weights   [bsz, heads, q_len, kv_len(+q_len)]
            V: value_states   [bsz, heads, kv_len(+q_len), head_dim]
            qK: attn_logits   [bsz, heads, q_len, kv_len(+q_len)] (used for k_score)
            O: attn_outputs   [bsz, heads, q_len, head_dim] (used for k_score)
            Q,K: (optional) only needed when A, qK are None (e.g., in FlashAttention prefill)
        """

        if A is not None:  # when prefill/decoding w. eager attn
            _, _, q_len, kv_len = A.shape
            if q_len == kv_len and hasattr(self, 'ptb_window'):
                A = A[..., -self.ptb_window :, :]
                qK = qK[..., -self.ptb_window :, :] if qK is not None else None
                O = O[..., -self.ptb_window :, :] if O is not None else None

        else:  # when prefill w. flashattn (A=None, qK=None), manually re-computing A (attn_weights)
            if hasattr(self, 'ptb_window'):
                Q = Q[..., -self.ptb_window :, :]    
                O = O[..., -self.ptb_window :, :] if O is not None else None

            qK = torch.matmul(Q, K.transpose(2, 3)) / math.sqrt(Q.size(-1))
            mask = torch.full((Q.size(-2), Q.size(-2)), torch.finfo(qK.dtype).min, device=qK.device)
            ar = torch.arange(mask.size(-1), device=qK.device)
            mask.masked_fill_(ar < (ar + 1).view(mask.size(-1), 1), 0)
            attention_mask = mask[None, None, :, :]

            A = qK
            A[:, :, -Q.size(-2):, -Q.size(-2):] += attention_mask
            A = torch.nn.functional.softmax(A, dim=-1, dtype=torch.float32).to(Q.dtype)
            q_len = A.size(-1) # A: [bsz, num_heads, q_len (or ptb_window), kv_len=q_len]

        if self.use_v_score:
            self.v_update(A, V, q_len, layer_idx=layer_idx)

        if self.use_k_score:
            self.k_update(A, V, qK, O, q_len, layer_idx=layer_idx)

    @torch.no_grad()
    def v_update(
        self, 
        A: Tensor, 
        V: Tensor, 
        q_len: int, 
        layer_idx: int
    ) -> None:

        # compute attention-based eviction scores
        A_normp = A.pow(self.p).sum(-2)

        if len(self.Sattn_all) <= layer_idx:
            self.Sattn_all.append(A_normp)
        else:
            if self.ptb_is_recent and getattr(self, "ptb_window", None) == 1:
                # no accumulation, only keep the latest scores
                self.Sattn_all[layer_idx] = A_normp
            else:
                # accumulation: [bsz, num_heads, prev_kv_len] -> [bsz, num_heads, prev_kv_len+q_len]
                prev = self.Sattn_all[layer_idx]
                A_normp[..., :-q_len] += prev
                self.Sattn_all[layer_idx] = A_normp
        ### Existing cache eviction scores end here ###

        if self.use_vnorm:
            if self.p == 1:
                V_normp = V[..., -q_len:, :].abs().sum(dim=-1)
            else:
                V_normp = V[..., -q_len:, :].pow(self.p).sum(dim=-1)

            if len(self.Vnormp_all) <= layer_idx:
                self.Vnormp_all.append(V_normp)
            else:
                V_normp = torch.cat([self.Vnormp_all[layer_idx], V_normp], dim=2)
                self.Vnormp_all[layer_idx] = V_normp

    @torch.no_grad()
    def k_update(
        self,
        A: Tensor,
        V: Tensor,
        qK: Optional[Tensor],
        O: Optional[Tensor],
        q_len: int,
        layer_idx: int,
    ) -> None:
        
        # compute key-pruning score
        if self.use_v_score and self.use_vnorm:
            V_normp = self.Vnormp_all[layer_idx]
        else:
            V_normp = V.pow(2).sum(dim=-1)  # [bsz, num_heads, kv_len]
        O_normp = O.pow(2).sum(dim=-1)      # [bsz, num_heads, q_len]

        VO = torch.einsum('bhqd,bhpd->bhqp', O, V)
        VmO_normp = V_normp[..., None, :] + O_normp[..., None] - 2.0 * VO
        S_key = (A * qK).pow(2) * VmO_normp
        S_key = S_key.sum(dim=-2)           # sum over q_len

        if self.use_v_score and self.use_cross:
            # compute joint-pruning score
            VVmO = V_normp[..., None, :] - VO
            S_cross = 2.0 * A.pow(2) * qK * VVmO
            S_cross = S_cross.sum(dim=-2)   # sum over q_len
        else:
            S_cross = 0

        S_key = S_key + S_cross

        # accumulate S_key (or S_key+S_cross) over time
        if len(self.Skey_all) <= layer_idx:
            self.Skey_all.append(S_key)
        else:
            if self.ptb_is_recent and getattr(self, "ptb_window", None) == 1:
                self.Skey_all[layer_idx] = S_key
            else:
                prev_S_key = self.Skey_all[layer_idx]
                S_key[..., :-q_len] += prev_S_key
                self.Skey_all[layer_idx] = S_key

    @torch.no_grad()
    def evict(
        self,
        num_recent_tokens: int,
        num_heavy_tokens: int,
        num_coming: int,
        layer_idx: int,
    ) -> Tensor:
        """
        Select heavy tokens to keep and update internal score tensors by
        removing evicted positions. Returns indices of selected heavy tokens.
        """
        score = self.retrieve_score(layer_idx)  # [bsz, num_heads, kv_len]
        _, _, seq_len = score.shape

        if num_coming >= num_recent_tokens:  # only in streaming mode when more tokens arrive than recent budget
            num_heavy_tokens -= (num_coming - num_recent_tokens)
            num_heavy_tokens = max(num_heavy_tokens, 0)

        recent_cutoff = seq_len - num_recent_tokens + num_coming
        score_to_select = score[..., : recent_cutoff]

        if self.pool_fn in pooling_fn:
            score_to_select = pooling_fn[self.pool_fn](
                score_to_select, kernel_size=7, padding=3, stride=1
            )

        if self.num_sink > 0:
            score_to_select[:, :, :self.num_sink] = torch.finfo(score.dtype).max

        _, keep_topk_idx = torch.topk(score_to_select, num_heavy_tokens, dim=-1)
        keep_topk_idx = keep_topk_idx.sort().values  # [bsz, num_heads, num_hh]

        # update scores by removing evicted columns
        if self.use_v_score:
            if not (self.ptb_is_recent and getattr(self, "ptb_window", None) == 1):
                self.Sattn_all[layer_idx] = take_gather(
                    self.Sattn_all[layer_idx], keep_topk_idx, recent_cutoff, gather_dim=-1
                )
            if self.use_vnorm:
                self.Vnormp_all[layer_idx] = take_gather(
                    self.Vnormp_all[layer_idx], keep_topk_idx, recent_cutoff, gather_dim=-1
                )

        if self.use_k_score:
            if not (self.ptb_is_recent and getattr(self, "ptb_window", None) == 1):
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


pooling_fn = {
    'maxpool': torch.nn.functional.max_pool1d,
    'avgpool': torch.nn.functional.avg_pool1d,
}


def take_gather(buf, keep_topk_idx, recent_cutoff, gather_dim=-2):
    """
    Gather helper for KV cache and score tensors.

    Args:
        buf:            [bsz, heads, ..., seq_len, ...] (depending on gather_dim)
        keep_topk_idx:  [bsz, heads, num_hh]
        recent_cutoff:  int, split point between historical and recent
        gather_dim:     -2 for KV cache (seq at -2), -1 for scores (seq at -1)
    Returns:
        Concatenation of (selected heavy) + (recent tail) along sequence dim.
    """ 
    if gather_dim == -1: 
        if buf.dim() == keep_topk_idx.dim():
            # buf: [bsz, heads, seq_len] (accumulated scores)
            select_buf = buf[..., : recent_cutoff]                                         # [bsz, heads, recent_cutoff]
            keep_recent = buf[..., recent_cutoff :]                                        # [bsz, heads, num_recent]
        elif buf.dim() == keep_topk_idx.dim() + 1:
            # buf: [bsz, heads, q_len, seq_len] (non-accumulated scores)
            select_buf = buf[..., : recent_cutoff]                                         # [bsz, heads, q_len, recent_cutoff]
            keep_recent = buf[..., recent_cutoff :]                                        # [bsz, heads, q_len, num_recent]
            keep_topk_idx = keep_topk_idx.unsqueeze(-2).expand(-1, -1, buf.size(-2), -1)   # [bsz, heads, q_len, num_hh]

    elif gather_dim == -2:
        # buf: [bsz, heads, seq_len, head_dim]
        select_buf = buf[..., : recent_cutoff, :]                                          # [bsz, heads, recent_cutoff, head_dim]
        keep_recent = buf[..., recent_cutoff :, :]                                         # [bsz, heads, num_recent, head_dim]
        keep_topk_idx = keep_topk_idx.unsqueeze(-1).expand(-1, -1, -1, buf.size(-1))       # [bsz, heads, num_hh, head_dim]

    else:
        raise ValueError(f"gather_dim {gather_dim} not supported")

    hh = torch.gather(select_buf, dim=gather_dim, index=keep_topk_idx)  # [bsz, heads, num_hh, ...]
    return torch.cat([hh, keep_recent], dim=gather_dim)                 # [bsz, heads, num_hh + num_recent, ...]


def _budget_is_defined(total_recent: Optional[int], total_heavy: Optional[int]) -> Tuple[int, int]:
    if total_recent is None or total_heavy is None:
        raise ValueError(
            "Both `num_recent_tokens` and `num_heavy_tokens/num_sink_tokens` must be defined "
            "at first update (or via cache ratios)."
        )
    return total_recent, total_heavy