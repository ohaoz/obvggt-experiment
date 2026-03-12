import os
from datasets import load_dataset
import torch
import json
from tqdm import tqdm
import argparse
import sys

sys.path.append("../../obc")
from monkey_patch.utils import enable_optimal_brain_kv, enable_optimal_brain_kv_flashattn2
from utils import load_kv_cache, load_model_and_tokenizer, seed_everything
from cache_utils import *


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=None, choices=["Llama-2-7b-chat-4k", "Llama-3-8B-Instruct-8k", "Llama-3.1-8B-Instruct-128k", "Qwen-2.5-7B-Instruct-128k", "longchat-v1.5-7b-32k", "xgen-7b-8k", "internlm-7b-8k", "chatglm2-6b", "chatglm2-6b-32k", "chatglm3-6b-32k", "vicuna-v1.5-7b-16k"])
    parser.add_argument("--e", action="store_true", help="Evaluate on LongBench-E")
    
    parser.add_argument("--precision", type=str, default="fp16", choices=["fp16", "bf16", "fp32"], help="Model precision")
    parser.add_argument("--hf_cache_dir", type=str, default=None, help="Huggingface cache directory")
    parser.add_argument("--task", type=str, default=None, help="task name")

    parser.add_argument("--cache_type", type=str, required=True)
    parser.add_argument("--cache_ratio", type=float, default=None, help="cache ratio")
    
    parser.add_argument("--num_recent", type=int, default=None)
    parser.add_argument("--num_special", type=int, default=None)

    parser.add_argument("--no_decode_evict", action="store_true", help="only evict prefill cache, not during decoding")
    parser.add_argument("--enable_prefill_flash_attn", action="store_true", help="use flash attention for prefilling")

    parser.add_argument("--save_dir", type=str, default="pred", help="directory to save predictions")
    
    args = parser.parse_args()
    return args


# This is the customized building prompt for chat models
def build_chat(tokenizer, prompt, model_name):
    if "chatglm3" in model_name:
        prompt = tokenizer.build_chat_input(prompt)
    elif "chatglm" in model_name:
        prompt = tokenizer.build_prompt(prompt)
    elif "longchat" in model_name or "vicuna" in model_name:
        from fastchat.model import get_conversation_template
        conv = get_conversation_template("vicuna")
        conv.append_message(conv.roles[0], prompt)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()
    elif "llama-2" in model_name.lower():
        prompt = f"[INST]\n{prompt}\n[/INST]"
    elif "xgen" in model_name:
        header = (
            "A chat between a curious human and an artificial intelligence assistant. "
            "The assistant gives helpful, detailed, and polite answers to the human's questions.\n\n"
        )
        prompt = header + f" ### Human: {prompt}\n###"
    elif "llama-3" in model_name.lower() or "qwen" in model_name.lower():
        prompt = tokenizer.apply_chat_template([
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt},
        ], tokenize=False, add_generation_prompt=True)
    return prompt


def post_process(response, model_name):
    if "xgen" in model_name:
        response = response.strip().replace("Assistant:", "")
    elif "internlm" in model_name:
        response = response.split("<eoa>")[0]
    elif "llama-3" in model_name.lower():
        response = (
            response.split(".assistant")[0]
            .split("\n\nQuestion")[0]
            .split("</s>")[0]
            .strip()
        )
    return response


def get_pred(
    model,
    tokenizer,
    data,
    max_length,
    max_gen,
    prompt_format,
    dataset,
    model_name,
    past_key_values=None,
    out_path=None,
):
    with open(out_path, "w", encoding="utf-8") as out_f:
        for json_obj in tqdm(data, total=len(data), desc=f"Inference on {dataset} with {model_name}..."):
            prompt = prompt_format.format(**json_obj)
            # truncate to fit max_length (we suggest truncate in the middle, since the left and right side may contain crucial instructions)
            tokenized_prompt = tokenizer(
                prompt, truncation=False, return_tensors="pt"
            ).input_ids[0]
            if "chatglm3" in model_name:
                tokenized_prompt = tokenizer(
                    prompt, truncation=False, return_tensors="pt", add_special_tokens=False
                ).input_ids[0]
            if len(tokenized_prompt) > max_length:
                half = int(max_length / 2)
                prompt = tokenizer.decode(
                    tokenized_prompt[:half], skip_special_tokens=True
                ) + tokenizer.decode(tokenized_prompt[-half:], skip_special_tokens=True)
            if dataset not in [
                "trec",
                "triviaqa",
                "samsum",
                "lsht",
                "lcc",
                "repobench-p",
            ]:  # chat models are better off without build prompts on these tasks
                prompt = build_chat(tokenizer, prompt, model_name)

            with torch.no_grad():
                model_inputs = tokenizer([prompt], return_tensors="pt")
                generated_ids = model.generate(
                                    model_inputs.input_ids.to(model.device), 
                                    past_key_values=past_key_values,
                                    use_cache=True,
                                    max_new_tokens=max_gen,
                                    do_sample=False,
                                    temperature=1.0,
                                    num_beams=1,
                                    pad_token_id=tokenizer.eos_token_id
                                )
                generated_ids = [
                    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                ]
                pred = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

                if past_key_values is not None:
                    # empty cache
                    past_key_values.reset()

            pred = post_process(pred, model_name)
            result = {
                "pred": pred,
                "answers": json_obj["answers"],
                "all_classes": json_obj["all_classes"],
                "length": json_obj["length"],
            }

            out_f.write(json.dumps(result, ensure_ascii=False)+"\n")
            out_f.flush()


if __name__ == "__main__":
    seed_everything(42)
    args = parse_args()
    model2path = json.load(open("config/model2path.json", "r"))
    model2maxlen = json.load(open("config/model2maxlen.json", "r"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name = args.model

    model, tokenizer = load_model_and_tokenizer(
        model2path[model_name], args.precision, args.hf_cache_dir, 
        flash_attn=args.enable_prefill_flash_attn)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model.eval()
    model = model.to(device)
    print(f"Model loaded on {device}")

    if not args.enable_prefill_flash_attn:
        enable_optimal_brain_kv(model)
    else:
        enable_optimal_brain_kv_flashattn2(model)
        print("Enabled flash-attn2 for efficient prefilling")

    if args.cache_ratio is not None:
        recent_ratio = round(0.05*args.cache_ratio, 4)
        special_ratio = round(0.95*args.cache_ratio, 4)
    else:
        recent_ratio, special_ratio = None, None

    past_key_values = load_kv_cache(
        args.cache_type,
        decode_evict=(not args.no_decode_evict),
        num_recent=args.num_recent, num_heavy=args.num_special,
        recent_ratio=recent_ratio, heavy_ratio=special_ratio
    )
    print("Cache eviction algorithm loaded: \n", past_key_values)

    exp_name = f"{model_name}-no_decode_evict" if args.no_decode_evict else model_name
    if args.cache_ratio is not None:
        suffix = f"-{special_ratio:.4f}+{recent_ratio:.4f}"
    else:
        suffix = f"-{args.num_special}+{args.num_recent}"
    exp_name += suffix
    if args.cache_type == "full":
        exp_name = f"{model_name}-full"

    max_length = model2maxlen[model_name]
    if args.task is not None:
        datasets = [args.task]
    else:
        datasets = ["narrativeqa", "qasper", "multifieldqa_en", "multifieldqa_zh", "hotpotqa", "2wikimqa", "musique", \
                    "dureader", "gov_report", "qmsum", "multi_news", "vcsum", "trec", "triviaqa", "samsum", "lsht", \
                    "passage_count", "passage_retrieval_en", "passage_retrieval_zh", "lcc", "repobench-p"]
    # we design specific prompt format and max generation length for each task, feel free to modify them to optimize model output
    dataset2prompt = json.load(open("config/dataset2prompt.json", "r"))
    dataset2maxlen = json.load(open("config/dataset2maxlen.json", "r"))
    # predict on each dataset

    for dataset in datasets:
        output_dir = os.path.join(args.save_dir, "pred")
        os.makedirs(output_dir, exist_ok=True)
        data = load_dataset("THUDM/LongBench", f"{dataset}_e" if args.e else dataset, split="test")

        out_path = os.path.join(output_dir, exp_name)
        os.makedirs(out_path, exist_ok=True)
        
        out_path = f"{out_path}/{dataset}-{args.cache_type}.jsonl"
        prompt_format = dataset2prompt[dataset]
        max_gen = dataset2maxlen[dataset]
        preds = get_pred(
            model,
            tokenizer,
            data,
            max_length,
            max_gen,
            prompt_format,
            dataset,
            model_name,
            past_key_values=past_key_values,
            out_path=out_path,
        )
