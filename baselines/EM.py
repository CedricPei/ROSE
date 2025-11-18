import os
import sys
import json
import argparse
import re
from tqdm import tqdm

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluators.utils import save_json


def _em_equal(pred: str, gold: str) -> bool:
    if pred is None or gold is None:
        return False
    return pred.strip() == gold.strip()


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='input_path', default=None)
    parser.add_argument('--skip-file', type=str, default=None)
    args = parser.parse_args()

    default_input = os.path.join(base, 'data', 'annotations', 'test.json')
    input_path = args.input_path if args.input_path else default_input
    if not os.path.exists(input_path):
        print(f'Input file not found: {input_path}')
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    skip_ids = set()
    if args.skip_file and os.path.exists(args.skip_file):
        try:
            with open(args.skip_file, 'r', encoding='utf-8') as sf:
                data = json.load(sf)
                skip_ids = set(str(x) for x in data)
        except Exception:
            pass

    input_stem = re.sub(r'(-result)$', '', os.path.splitext(os.path.basename(input_path))[0])
    out_dir = os.path.join(base, 'output', input_stem, 'decisive', f'EM-{input_stem}-eval')
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, 'eval_results.json')

    processed_ids = set()
    if os.path.exists(out_file):
        try:
            with open(out_file, 'r', encoding='utf-8') as ef:
                existing = json.load(ef)
                for item in existing:
                    qid = str(item.get('question_id'))
                    if qid:
                        processed_ids.add(qid)
        except Exception:
            processed_ids = set()

    if skip_ids:
        processed_ids.update(skip_ids)

    to_process = [q for q in questions if str(q.get('question_id')) not in processed_ids]
    for q in tqdm(to_process, total=len(to_process)):
        pred_sql = q.get('predicted_sql') or ''
        gold_sql = q.get('gold_sql') or ''
        score = 1.0 if _em_equal(pred_sql, gold_sql) else 0.0
        out_row = {
            "question_id": q.get("question_id"),
            "question": q.get("question"),
            "evidence": q.get("evidence"),
            "gold_sql": gold_sql,
            "predicted_sql": pred_sql,
            "score": score,
        }
        out_row.update({k: q[k] for k in ("label", "difficulty") if k in q})
        save_json(out_row, out_file, append=True)


if __name__ == '__main__':
    main()


