# ROSE: An Intent-Centered Evaluation Metric for NL2SQL

**ROSE** (ReasOning ScorE) is an intent-centered evaluation metric for Natural Language to SQL (NL2SQL) that focuses on whether the predicted SQL answers the question, rather than consistency with the ground-truth SQL under the reference-dependent paradigm.

## 📖 Overview

Execution Accuracy (EX), the widely used metric for evaluating NL2SQL solutions, is becoming increasingly unreliable due to:
- **Syntactic variation**: EX cannot accommodate predictions with identical logic but different representations
- **Multiple valid interpretations**: EX misses reasonable predictions that deviate from ground-truth but still correctly answer the question
- **Erroneous ground-truth SQL**: EX propagates annotation errors to all evaluated predictions

ROSE addresses these limitations through an **adversarial Prover-Refuter cascade**:
- **SQL Prover**: Assesses the semantic correctness of predicted SQL against the user's intent independently, without accessing ground-truth SQL
- **Adversarial Refuter**: Uses ground-truth SQL as evidence to challenge and refine the Prover's judgment, identifying critical conflicts

On our expert-aligned validation set **ROSE-VEC**, ROSE achieves the best agreement with human experts, outperforming the next-best metric by nearly 24% in Cohen's Kappa.

## 🏗️ Repository Structure

```
ROSE/
├── main.py                      # Main evaluation script using ROSE
│
├── evaluators/                  # Core evaluation components
│   ├── Prover.py               # SQL Prover implementation
│   ├── Refuter.py              # Adversarial Refuter implementation
│   ├── Refuter_WOGT.py         # Refuter without ground-truth (variant)
│   ├── utils.py                # Utility functions (SQL execution, DB info)
│
├── prompts/                     # Prompt templates for LLM-based evaluators
│   ├── prompt_prover.py        # Prover prompts
│   ├── prompt_refuter.py       # Refuter prompts
│   ├── prompt_refuter_wogt.py # Refuter without ground-truth prompts
│   └── ...
│
├── baselines/                   # Baseline evaluation metrics
│   ├── EX.py                   # Execution Accuracy
│   ├── EM.py                   # Exact Match
│   ├── ETM.py                  # Execution Tree Match
│   ├── ProverOnly.py           # Prover-only evaluation
│   ├── PR.py                   # Prover-Refuter (ROSE)
│   ├── PR_WOGT.py              # PR without ground-truth
│   └── WOGT.py                 # Without ground-truth variant
│
├── data/                        # Data and annotations
│   ├── annotations/            # Expert annotations
│   │   ├── rose-vec-bird.json # ROSE-VEC Bird dataset
│   │   ├── rose-vec-spider.json # ROSE-VEC Spider dataset
│   │   └── ...
│   ├── description/            # Database schema descriptions
│   └── dev.json                # Development dataset
│
├── dev_databases/              # SQLite database files
│   ├── california_schools/
│   ├── card_games/
│   └── ...
│
├── output/                      # Evaluation results
│   ├── rose-vec/               # ROSE-VEC evaluation results
│   │   ├── rose-vec-bird/
│   │   └── rose-vec-spider/
│   └── benchmarking/           # Benchmark evaluation results
```

## 🚀 Installation

### Prerequisites

- Python 3.8+
- SQLite3
- OpenAI API key (for LLM-based evaluators)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ROSE
```

2. Install dependencies:
```bash
pip install openai python-dotenv tqdm scikit-learn pandas
```

Or create a `requirements.txt` file:
```txt
openai>=1.0.0
python-dotenv>=1.0.0
tqdm>=4.65.0
scikit-learn>=1.3.0
pandas>=2.0.0
```

Then install:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=your_base_url_here  # Optional, for custom endpoints
```

4. Prepare databases:
Ensure SQLite database files are in `dev_databases/` directory.

## 📊 ROSE-VEC Dataset

ROSE-VEC (Validation dataset with Expert Consensus) is our expert-aligned validation set containing 585 samples with detailed annotations:
- **rose-vec-bird**: 322 samples from BIRD dataset
- **rose-vec-spider**: 263 samples from Spider dataset

Each sample includes:
- `question_id`: Unique identifier
- `question`: Natural language question
- `db_id`: Database identifier
- `predicted_sql`: SQL query to evaluate
- `gold_sql`: Ground-truth SQL reference
- `evidence`: Additional context/evidence (optional)
- `label`: Expert consensus label (true/false)

## ⚡ Quick Start

**Evaluate a single dataset with ROSE:**
```bash
python main.py --input data/annotations/rose-vec-bird.json --threads 4
```

## 🔧 Usage

### 1. Running ROSE Evaluation

Evaluate predicted SQL queries using ROSE:

```bash
python main.py --input data/annotations/rose-vec-bird.json --threads 4
```

**Parameters:**
- `--input`: Path to input JSON file containing questions and predicted SQL
- `--threads`: Number of parallel threads (default: 1)

**Output:**
Results are saved to `output/rose-vec/{dataset_name}/{model}/ROSE/eval_results.json`

### 2. Running Baseline Metrics

#### Execution Accuracy (EX)
```bash
python baselines/EX.py --input data/annotations/rose-vec-bird.json
```

#### Exact Match (EM)
```bash
python baselines/EM.py --input data/annotations/rose-vec-bird.json
```

#### Execution Tree Match (ETM)
```bash
python baselines/ETM.py --input data/annotations/rose-vec-bird.json
```

## 📈 Evaluation Metrics

ROSE calculates the following metrics:

- **Cohen's Kappa**: Agreement with expert labels
- **Accuracy**: Overall correctness
- **MCC (Matthews Correlation Coefficient)**: Balanced measure
- **F1 Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: TP, TN, FP, FN counts

## 🔍 How ROSE Works

ROSE uses a two-stage adversarial cascade to evaluate SQL correctness:

### Step 1: SQL Execution & Result Comparison
- Execute both predicted SQL (`pred_sql`) and ground-truth SQL (`gold_sql`)
- Compare execution results (`pred_result` vs `gold_result`)
- **If results match**: Proceed directly to Refuter (Step 3)
- **If results differ**: Proceed to Prover (Step 2)

### Step 2: SQL Prover (when results differ)
The Prover independently evaluates whether the predicted SQL semantically answers the question:
- **Input**: Question, database schema, predicted SQL, and its execution result
- **Key feature**: Does NOT access ground-truth SQL
- **Output**: 
  - `verdict`: Boolean (true = SQL correctly answers question)
  - `reason`: Detailed reasoning explaining the judgment
  - `expected_answer`: What the question is asking for
  - `sql_description`: What the predicted SQL actually does

### Step 3: Adversarial Refuter
If Prover passes (verdict=true), the Refuter challenges this judgment:
- **Input**: Question, both SQLs, both execution results, Prover's reasoning
- **Purpose**: Use ground-truth SQL as evidence to identify critical conflicts
- **Output**:
  - `verdict`: Boolean (true = overturn Prover's pass, false = uphold)
  - `judgement`: Concise assessment of semantic correctness
  - `ambiguity`: Type of ambiguity detected (if any)
  - `gold_correct`: Whether ground-truth SQL is correct

The Refuter can identify:
- **Ambiguous Question**: Multiple valid interpretations exist
- **Ambiguous Schema**: Schema elements are semantically similar
- **Gold Fault**: Ground-truth SQL contains errors

### Step 4: Final Score Assignment
- `score = 1.0` if:
  - Results match AND Refuter upholds (verdict=false), OR
  - Results differ AND Prover passes AND Refuter upholds (verdict=false)
- `score = 0.0` otherwise

This design reduces false positives (over-permissiveness) while maintaining sensitivity to semantic correctness.

## 📝 Input Format

Input JSON file should contain a list of objects:

```json
[
  {
    "question_id": 1,
    "question": "What is the total sales?",
    "db_id": "financial",
    "predicted_sql": "SELECT SUM(amount) FROM sales",
    "gold_sql": "SELECT SUM(amount) FROM sales",
    "evidence": "Total sales refers to sum of amount column",
    "label": true
  }
]
```

## 📤 Output Format

Evaluation results are saved as JSON:

```json
[
  {
    "question_id": 1,
    "question": "What is the total sales?",
    "db_id": "financial",
    "predicted_sql": "SELECT SUM(amount) FROM sales",
    "gold_sql": "SELECT SUM(amount) FROM sales",
    "evidence": "...",
    "score": 1.0,
    "prover_result": true,
    "refuter_result": false,
    "label": true
  }
]
```

## 🎯 Key Features

1. **Intent-Centered**: Focuses on whether SQL answers the question, not exact match with ground-truth
2. **Adversarial Cascade**: Prover-Refuter design reduces false positives while maintaining sensitivity
3. **Ambiguity Detection**: Identifies ambiguous questions and schema issues
4. **Ground-Truth Error Detection**: Flags erroneous ground-truth SQL
5. **Expert-Aligned**: Validated on ROSE-VEC with expert consensus

## 📊 Results

On ROSE-VEC, ROSE achieves:
- **Best agreement** with human experts (Cohen's Kappa)
- **24% improvement** over next-best metric
- **14% improvement** in accuracy

## 🔬 Large-Scale Re-evaluation

We conducted a large-scale re-evaluation of 19 NL2SQL methods, revealing four key insights:

1. **Base model capability** is the primary performance driver, not system-level engineering
2. **Widening gap** between semantic correctness and reference matching signals an evaluation crisis
3. **Divergence** largely stems from benchmark flaws (ground-truth errors and question ambiguities)
4. **Fine-tuning** narrows the gap by aligning models to dataset's stylistic conventions

## 🙏 Acknowledgments

We thank all the expert annotators who contributed to ROSE-VEC dataset construction.

---

**Note**: This repository contains the implementation of ROSE metric and ROSE-VEC validation dataset as described in our paper. For detailed methodology and experimental results, please refer to the paper.

