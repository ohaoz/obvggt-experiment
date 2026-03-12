import random
import warnings
from typing import Optional, Tuple

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cache_utils import *


_DTYPE_MAP = {
    "fp16": torch.float16,
    "bf16": torch.bfloat16,
    "fp32": torch.float32,
}


def load_model_and_tokenizer(
    model_name_or_path: str,
    precision: str = "fp16",
    hf_cache_dir: Optional[str] = None,
    flash_attn: bool = False,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:

    attn_impl = "flash_attention_2" if flash_attn else "eager"
    if precision not in _DTYPE_MAP:
        raise ValueError(f"Unsupported precision: {precision}. Choose from {list(_DTYPE_MAP.keys())}.")
    torch_dtype = _DTYPE_MAP[precision]

    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        trust_remote_code=True,
        cache_dir=hf_cache_dir,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        attn_implementation=attn_impl,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
        cache_dir=hf_cache_dir,
    )
    return model, tokenizer


def seed_everything(seed):
    random.seed(seed) 
    np.random.seed(seed) 
    torch.manual_seed(seed) 
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def load_kv_cache(
    method: str,
    num_recent: Optional[int] = None,
    num_heavy: Optional[int] = None,
    recent_ratio: Optional[float] = None,
    heavy_ratio: Optional[float] = None,
    decode_evict: bool = True,
    fix_recent_token: bool = False,
    cache_ratio: Optional[float] = None,
    streaming: bool = False,
):
    """
    Factory for KV cache eviction implementations.

    Args:
        method: one of
            'full' (no cache eviction), 'sink' (streamingllm),
            H2O/TOVA/SnapKV presets: 'h2o', 'snapkv', 'tova',
            OBC variants (examples):
              'obcV'  corresponds to OBCache-Value in paper
              'obcK'  corresponds to OBCache-Key in paper
              'obcVK' corresponds to OBCache-Joint in paper

        num_recent / num_heavy: absolute token counts to keep.
        recent_ratio / heavy_ratio: ratios of the first update prompt length used to
            derive counts when explicit counts are not provided.
        decode_evict: if False, only evict during prefill phase.
        fix_recent_token: keep `num_recent` fixed and derive `num_heavy` from
            `cache_ratio * prompt_len - num_recent` on first update.
        cache_ratio: total cache budget (fraction of prompt length) used when
            `fix_recent_token=True`.

    Returns:
        - None for 'full' (no custom cache)
        - An instance of `SinkCache` or `OBCache` for other methods.
    """

    method = method.strip()

    if method == 'full':
        return None

    if method == 'sink':
        return SinkCache(
            num_recent=num_recent,
            num_heavy=num_heavy
        )

    obcache_like_methods = {
        "h2o", "obcV", "obcK", "obcVK", "obcV_p1",  # H2O and its Obcache-enhanced variants
        "tova", "obcV+tova", "obcK+tova", "obcVK+tova", "obcV_p1+tova",  # TOVA and its Obcache-enhanced variants
        "snapkv", "obcV+maxpool", "obcK+maxpool", "obcVK+maxpool", "obcV_p1+maxpool",  # SnapKV and its Obcache-enhanced variants
        "snapkv_avgpool", "obcV+avgpool", "obcK+avgpool", "obcVK+avgpool", "obcV_p1+avgpool",  # SnapKV (avgpool) and its Obcache-enhanced variants
        "h2o_fullhist", "obcV_fullhist", "obcK_fullhist", "obcVK_fullhist", "obcV_p1_fullhist",  # H2O (fullhist) and its Obcache-enhanced variants
        "obcVK_no_cross", "obcVK_no_cross+tova", "obcVK_no_cross+maxpool", "obcVK_no_cross+avgpool", "obcVK_no_cross_fullhist"  # OBCache variants without cross-term
    }
    if method not in obcache_like_methods:
        raise ValueError(f"Unknown cache eviction method: {method}")

    use_v_score = True
    use_k_score = True
    use_cross = True
    p = 2
    use_vnorm = True
    ptb_window: Optional[int] = None
    ptb_is_recent = False
    pool_fn: Optional[str] = None

    if method.startswith("h2o"):
        use_v_score, use_k_score, use_cross = True, False, False
        p, use_vnorm, pool_fn = 1, False, None
        ptb_window = num_recent if "fullhist" not in method else None

    elif method.startswith("snapkv"):
        use_v_score, use_k_score, use_cross = True, False, False
        ptb_window = num_recent
        p, use_vnorm = 1, False
        pool_fn = "avgpool" if "avgpool" in method else "maxpool"

    elif method == "tova":
        use_v_score, use_k_score, use_cross = True, False, False
        p, use_vnorm, pool_fn = 1, False, None
        ptb_window, ptb_is_recent = 1, True

    elif method.startswith("obcV"):
        use_v_score, use_vnorm = True, True
        ptb_window = num_recent if "fullhist" not in method else None
        pool_fn = "maxpool" if "maxpool" in method else ("avgpool" if "avgpool" in method else None)
        p = 1 if "p1" in method else 2

        if method.startswith("obcVK"):
            use_k_score = True
            use_cross = ("no_cross" not in method)
        else:
            use_k_score = False
            use_cross = False

        if "+tova" in method:
            ptb_window, ptb_is_recent = 1, True

    elif method.startswith("obcK"):
        use_v_score, use_k_score, use_cross = False, True, False
        ptb_window = num_recent if "fullhist" not in method else None
        pool_fn = "maxpool" if "maxpool" in method else ("avgpool" if "avgpool" in method else None)
        p, use_vnorm = 2, True
        if "+tova" in method:
            ptb_window, ptb_is_recent = 1, True

    if "tova" in method:
        # Move any recent budget into heavy budget
        if num_recent and num_recent > 0:
            num_heavy = (num_heavy or 0) + num_recent
            num_recent = 0
            warnings.warn(
                "For 'tova', `num_recent` should be 0. Adjusting num_recent=0 and "
                f"num_heavy={num_heavy}.",
                RuntimeWarning,
            )
        if recent_ratio and recent_ratio > 0:
            heavy_ratio = (heavy_ratio or 0.0) + recent_ratio
            recent_ratio = 0.0
            warnings.warn(
                "For 'tova', `recent_ratio` should be 0.0. Adjusting recent_ratio=0.0 and "
                f"heavy_ratio={heavy_ratio}.",
                RuntimeWarning,
            )

    past_key_values = OBCache(
        num_recent=num_recent,
        num_heavy=num_heavy,
        recent_ratio=recent_ratio,
        heavy_ratio=heavy_ratio,
        decode_evict=decode_evict,
        fix_recent_token=fix_recent_token,
        cache_ratio=cache_ratio,
        use_v_score=use_v_score,
        use_k_score=use_k_score,
        use_cross=use_cross,
        p=p,
        use_vnorm=use_vnorm,
        ptb_window=ptb_window,
        pool_fn=pool_fn,
        ptb_is_recent=ptb_is_recent,
        num_sink=0 if not streaming else 4,
    )
    past_key_values.method = method

    return past_key_values
