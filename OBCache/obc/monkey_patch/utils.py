import types

from .llama import llama_attention_forward as llama_attention_optimal_brain_cache 
from .llama import llama_flashattention2_forward as llama_flashattention2_optimal_brain_cache
from .llama import llama_attention_streaming_forward as llama_attention_optimal_brain_cache_streaming

from transformers.models.llama.modeling_llama import LlamaAttention, LlamaFlashAttention2
from transformers.models.qwen2.modeling_qwen2 import Qwen2Attention, Qwen2FlashAttention2


def enable_optimal_brain_kv(model, model_name="llama"):
    # llama_attention_optimal_brain_cache: llama_forward supports score tracking and eviction
    for name, module in reversed(model._modules.items()):
        if len(list(module.children())) > 0:
            enable_optimal_brain_kv(module, model_name)

        if isinstance(module, LlamaAttention) or isinstance(module, Qwen2Attention):
            model._modules[name].forward = types.MethodType(
                llama_attention_optimal_brain_cache, model._modules[name]
            )


def enable_optimal_brain_kv_flashattn2(model, model_name="llama"):
    # llama_flashattention2_optimal_brain_cache: llama_forward supports score tracking and eviction (using FlashAttn2 for prefill)
    for name, module in reversed(model._modules.items()):
        if len(list(module.children())) > 0:
            enable_optimal_brain_kv_flashattn2(module, model_name)

        if isinstance(module, LlamaFlashAttention2) or isinstance(module, Qwen2FlashAttention2):
            model._modules[name].forward = types.MethodType(
                llama_flashattention2_optimal_brain_cache, model._modules[name]
            )


def enable_optimal_brain_kv_streamingattn(model, model_name="llama"):
    # llama_attention_optimal_brain_cache_streaming: llama_forward supports score tracking (eviction at higher level)
    for name, module in reversed(model._modules.items()):
        if len(list(module.children())) > 0:
            enable_optimal_brain_kv_streamingattn(module, model_name)

        if isinstance(module, LlamaAttention) or isinstance(module, Qwen2Attention):
            model._modules[name].forward = types.MethodType(
                llama_attention_optimal_brain_cache_streaming, model._modules[name]
            )