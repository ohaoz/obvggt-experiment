cd evaluation/needle

MODELNAME=Llama-3.1-8B-Instruct
MODELPATH=meta-llama/Llama-3.1-8B-Instruct

DATAPATH=data/ruler_8k_niah_single_2.jsonl
SAVEDIR=results/${MODELNAME}

mkdir -p $SAVEDIR

CRS=(0.01 0.02 0.03 0.04 0.05)
METHODS=(h2o obcV obcK obcVK tova obcV+tova obcK+tova obcVK+tova snapkv obcV+maxpool obcK+maxpool obcVK+maxpool)

for cr in ${CRS[@]}; do
    echo "Evaluation with $cr Cache Budget"
    for method in ${METHODS[@]}; do
        python pred.py \
            --data_path $DATAPATH \
            --save_dir $SAVEDIR \
            --model_name $MODELNAME \
            --model_path $MODELPATH \
            --precision bf16 \
            --cache_type $method \
            --num_recent 16 \
            --cache_ratio $cr \
            --no_decode_evict \
            --enable_prefill_flash_attn
    done
done


python eval.py --save_dir $SAVEDIR
