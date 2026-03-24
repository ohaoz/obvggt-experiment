
import re
import os
import json
import argparse

from tqdm import tqdm

def postprocess_pred(predict_str: str):
    predict_str = predict_str.strip()

    # Remove all non-printable characters
    np_pattern = re.compile(r'[\x00-\x1f]')
    predict_str = np_pattern.sub('\n', predict_str).strip()

    return predict_str


def get_pred_and_ref(
    predictions_file: str,
    input_field: str = 'input',
    references_field: str = 'outputs',
    prediction_field: str = 'response',
    metadata_field: str = 'others',
):
    lines = [json.loads(line) for line in open(predictions_file, 'r')]

    predicts = []
    references = []
    indices = []

    for line in tqdm(lines):
        predict = line[prediction_field]
        predict = postprocess_pred(predict)
        reference = line.get(references_field, [line.get('output', '')])
        index = line[metadata_field].get('id', line['index'])

        predicts.append(predict)
        references.append(reference)
        indices.append(index)
        
    return predicts, references, indices


def string_match_all(preds, refs):
    score = sum([sum([1.0 if r.lower() in pred.lower() else 0.0 for r in ref]) / len(ref) for pred, ref in zip(preds, refs)]) / len(preds) * 100
    return round(score, 2)


def run_evaluation(predictions_file):
    predicts, references, indices = get_pred_and_ref(predictions_file)

    task_nulls = f'{sum([len(x)==0 for x in predicts])}/{len(predicts)}'

    if len(references) > 0 and references[0][0] is not None:
        task_score = string_match_all(predicts, references)
    else:
        task_score = 0.0

    return task_score, task_nulls, predicts, indices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_dir', type=str, required=True)
    args = parser.parse_args()

    task_folders = os.listdir(args.save_dir)

    for task_folder in task_folders:
        if os.path.isfile(os.path.join(args.save_dir, task_folder)):
            continue
        print(f"Evaluating task: {task_folder}")
        exp_folders = os.listdir(os.path.join(args.save_dir, task_folder))
        scores = dict()
        for exp_folder in exp_folders:
            pred_file = os.path.join(args.save_dir, task_folder, exp_folder, 'pred.jsonl')
            if not os.path.exists(pred_file):
                print(f"Warning: {pred_file} not found")
                task_score = -1.0
            else:
                task_score, task_nulls, predicts, indices = run_evaluation(pred_file)
                if task_nulls != f'0/{len(predicts)}':
                    print(f"Warning: Null predictions found in {pred_file}")
            scores[exp_folder] = task_score

        out_path = os.path.join(args.save_dir, task_folder, "result.json")
        with open(out_path, "w") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
        print("Evaluation stats saved to:", out_path)


if __name__ == "__main__":
    main()