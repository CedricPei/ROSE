import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, Any
from .utils import get_db_info, extract_json_from_response, save_json
from prompts.prompt_refuter_wogt import system_prompt_refuter_wogt, user_prompt_refuter_wogt

load_dotenv()


class Refuter_WOGT:
    """Refuter that validates predicted SQL without gold standard - focuses on finding issues and logical flaws"""
    
    def __init__(self, model: str = None, output_dir: str = "output"):
        self.model = model
        self.output_dir = output_dir
    
    def call(self, question: Dict[str, Any], pred_sql: str, pred_result: Any = None, prover_reason: str = None) -> bool:
        """Validate predicted SQL without gold standard for critical issues"""
        try:
            db_info = get_db_info(question["db_id"], pred_sql)
            
            if pred_result is not None:
                pred_result = pred_result.head(20)
                
                user_content = user_prompt_refuter_wogt.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    db_info=db_info,
                    pred_result=pred_result,
                    prover_reason=prover_reason or ""
                )
            else:
                user_content = user_prompt_refuter_wogt.format(
                    question=question["question"],
                    evidence=question.get("evidence", ""),
                    predicted_sql=pred_sql,
                    db_info=db_info,
                    pred_result="",
                    prover_reason=prover_reason or ""
                )
            
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_refuter_wogt},
                    {"role": "user", "content": user_content}
                ],
                # temperature=0
            )
            
            result = json.loads(extract_json_from_response(response.choices[0].message.content))
            # Save output to a single JSON file (append mode)
            output_data = {
                "question_id": question["question_id"],
                "result": result
            }
            output_file = os.path.join(self.output_dir, "refuter_wogt_output.json")
            save_json(output_data, output_file, append=True)

            return result.get("verdict", None)

        except Exception as e:
            print(f"Refuter_WOGT error: {e}")
            return None

