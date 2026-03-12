import torch
import json
import argparse
import sys
import os
import time
from tqdm import tqdm

sys.path.append("../../obc")
from monkey_patch.utils import enable_optimal_brain_kv, enable_optimal_brain_kv_flashattn2
from utils import load_kv_cache, load_model_and_tokenizer, seed_everything
from cache_utils import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--model_path", type=str, required=True, help="Path to the model.")
    parser.add_argument("--hf_cache_dir", type=str, default=None, help="Path to the Hugging Face cache directory.")
    parser.add_argument("--precision", type=str, default='fp16', choices=['fp16', 'bf16', 'fp32'], help="Model precision.")

    parser.add_argument("--cache_type", type=str, required=True)
    
    parser.add_argument("--num_recent", type=int, default=16)
    parser.add_argument("--cache_ratio", type=float, default=0.01, help="cache ratio")

    parser.add_argument("--no_decode_evict", action="store_true", help="only evict prefill cache, not during decoding")
    parser.add_argument("--enable_prefill_flash_attn", action="store_true", help="use flash attention for prefilling")

    parser.add_argument("--data_path", required=True, help='path to jsonl data file')
    parser.add_argument("--save_dir", required=True, help='path to save the prediction jsonl files')

    args = parser.parse_args()
    args.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return args


def build_chat(tokenizer, prompt, model_name):
    if "llama-2" in model_name.lower():
        prompt = f"[INST]\n{prompt}\n[/INST]"
    elif "llama-3" in model_name.lower():
        prompt = tokenizer.apply_chat_template([
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt},
        ], tokenize=False, add_generation_prompt=True)
    return prompt


def post_process(response, model_name):
    if "llama-3" in model_name.lower():
        response = (
            response.split(".assistant")[0]
            .split("\n\nQuestion")[0]
            .split("</s>")[0]
            .strip()
        )
    return response


def main():
    args = parse_args()
    seed_everything(42)

    model, tokenizer = load_model_and_tokenizer(
        args.model_path, args.precision, args.hf_cache_dir, 
        flash_attn=args.enable_prefill_flash_attn)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model.eval()
    model = model.to(args.device)
    print(f"Model loaded on {args.device}")

    if not args.enable_prefill_flash_attn:
        enable_optimal_brain_kv(model)
    else:
        enable_optimal_brain_kv_flashattn2(model)
        print("Enabled flash-attn2 for efficient prefilling")

    past_key_values = load_kv_cache(
        args.cache_type, 
        decode_evict=(not args.no_decode_evict),
        num_recent=args.num_recent, 
        cache_ratio=args.cache_ratio,
        fix_recent_token=True
    )
    print("Cache eviction algorithm loaded: \n", past_key_values)


    task_name = args.data_path.split("/")[-1].split(".jsonl")[0]
    save_name = f"{args.cache_type}-cr{args.cache_ratio}"
    save_name += "-no_decode_evict" if args.no_decode_evict else ""

    save_folder = os.path.join(args.save_dir, task_name, save_name)
    os.makedirs(save_folder, exist_ok=True)
    with open(args.data_path, 'r') as f:
        data = [json.loads(line) for line in f]

    start_time = time.time()
    with open(os.path.join(save_folder, f"pred.jsonl"), 'w') as f:
        with torch.no_grad():
            for item in tqdm(data, total=len(data), desc="Evaluating on NIAH..."):
                prompt = item['input']
                prompt = build_chat(tokenizer, prompt, args.model_name)

                inputs = tokenizer([prompt], return_tensors="pt")
                generated_ids = model.generate(
                    inputs.input_ids.to(model.device), 
                    attention_mask=inputs.attention_mask.to(model.device),
                    past_key_values=past_key_values,
                    max_new_tokens=64,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                generated_ids = [
                    output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
                ]
                response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
                response = post_process(response, args.model_name)
                
                if past_key_values is not None:
                    # empty cache
                    past_key_values.reset()

                result = {
                    'index': item['index'],
                    'response': response,
                    'outputs': item['outputs'],
                    'others': item.get('others', {}),
                    'truncation': item.get('truncation', -1),
                    'length': item.get('length', -1),
                }
                f.write(json.dumps(result) + '\n')
                f.flush()
    f.close()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Evaluation completed in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()