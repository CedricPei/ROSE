import os
import sys
import json
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluators.utils import execute_sql, write_result_to_file, run_with_timeout
from prompts.prompt_pr import system_prompt_pr, user_prompt_pr


class PR:
    """Prover-Refuter combined in one step"""
    
    def __init__(self, model: str = None, output_dir: str = "output"):
        self.model = model
        self.output_dir = output_dir
    
    def call(self, question, pred_sql: str, pred_result, gold_sql: str, gold_result):
        """Validate predicted SQL and return final verdict"""
        try:
            from evaluators.utils import get_db_info, extract_json_from_response, save_json
            import openai
            from dotenv import load_dotenv
            load_dotenv()
            
            db_info = get_db_info(question["db_id"], [pred_sql, gold_sql])
            pred_result = pred_result.head(20) if pred_result is not None else None
            gold_result = gold_result.head(20) if gold_result is not None else None
            
            user_content = user_prompt_pr.format(
                question=question["question"],
                evidence=question.get("evidence", ""),
                predicted_sql=pred_sql,
                gold_sql=gold_sql,
                db_info=db_info,
                sql_result=pred_result,
                gold_result=gold_result
            )
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_pr},
                    {"role": "user", "content": user_content}
                ],
            )

            result = json.loads(extract_json_from_response(response.choices[0].message.content))
            output_data = {
                "question_id": question["question_id"],
                "result": result
            }
            output_file = os.path.join(self.output_dir, "pr_output.json")
            save_json(output_data, output_file, append=True)

            return result.get("verdict", None), result.get("reason", "")

        except Exception as e:
            print(f"PR error: {e}")
            return None, f"Error: {e}"


def _process_question(question, pr, output_dir):
    pred_sql = question["predicted_sql"]
    db_id = question["db_id"]
    gold_sql = question["gold_sql"]
    
    pred_res = run_with_timeout(execute_sql, db_id, pred_sql, timeout=60)
    gold_res = run_with_timeout(execute_sql, db_id, gold_sql, timeout=60)
    
    score = 0.0
    pr_verdict = None

    if pred_res is None or gold_res is None:
        return 
    if pred_res is False:
        score = 0.0
        write_result_to_file(question, pred_sql, score, pr_verdict, None, output_dir)
        return 
    
    pr_verdict, _ = pr.call(question, pred_sql, pred_res, gold_sql, gold_res)
    if pr_verdict is None:
        return 
    score = 1.0 if pr_verdict else 0.0
    write_result_to_file(question, pred_sql, score, pr_verdict, None, output_dir)
    return 


def main():
    parser = argparse.ArgumentParser(description="PR (Prover-Refuter combined) ablation experiment")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--input", type=str, default="sample.json", help="Input file path")
    args = parser.parse_args()
    reasoning_model = "google/gemini-2.5-flash"

    input_stem = re.sub(r"(-result)$", "", os.path.splitext(os.path.basename(args.input))[0])
    output_dir = f"output/test/gemini-ablation/pr"
    os.makedirs(output_dir, exist_ok=True)

    pr = PR(model=reasoning_model, output_dir=output_dir)

    num_threads = max(1, int(args.threads))
    existing_results_path = os.path.join(output_dir, "eval_results.json")

    with open(args.input, "r", encoding="utf-8") as f:
        questions = json.load(f)

    existing_ids = set()
    if os.path.exists(existing_results_path):
        try:
            with open(existing_results_path, "r", encoding="utf-8") as ef:
                existing_data = json.load(ef)
                for item in existing_data:
                    qid = str(item.get("question_id"))
                    if qid:
                        existing_ids.add(qid)
        except Exception:
            existing_ids = set()

    total_input = len(questions)
    questions = [q for q in questions if str(q.get("question_id")) not in existing_ids]
    to_process = len(questions)
    print(f"Input total: {total_input}, To process: {to_process}")

    progress = tqdm(total=to_process, dynamic_ncols=True, mininterval=0.5)

    def worker(idx):
        slice_questions = questions[idx::num_threads]
        for q in slice_questions:
            _process_question(q, pr, output_dir)
            progress.update(1)
        return []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        for f in futures:
            f.result()

    progress.close()


if __name__ == "__main__":
    main()

