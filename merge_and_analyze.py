#!/usr/bin/env python3
"""
合并 rose-vec-bird 和 rose-vec-spider 的结果，并计算统计指标
自动查找所有在两个数据集中都存在的方法，并输出统计结果
"""
import json
import os
import argparse
from sklearn.metrics import cohen_kappa_score


def load_eval_results(eval_file: str) -> list:
    """加载评估结果文件"""
    if not os.path.exists(eval_file):
        raise FileNotFoundError(f"File not found: {eval_file}")
    with open(eval_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metrics(data: list) -> dict:
    """计算统计指标：accuracy, cohen_kappa, MCC, F1"""
    if not data:
        return None
    
    # 检查是否有 label 字段
    if not any(item.get("label") in (True, False, "true", "false") for item in data):
        return None
    
    tp = tn = fp = fn = 0
    labels = []
    scores = []
    
    for item in data:
        label = item.get("label")
        score = item.get("score")
        
        is_true_label = label in (True, "true")
        predicted_true = score == 1.0
        
        labels.append(1 if is_true_label else 0)
        scores.append(1 if predicted_true else 0)
        
        if is_true_label and predicted_true:
            tp += 1
        elif is_true_label and not predicted_true:
            fn += 1
        elif not is_true_label and predicted_true:
            fp += 1
        else:
            tn += 1
    
    total_items = len(data)
    accuracy = (tp + tn) / total_items if total_items > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    kappa = cohen_kappa_score(labels, scores) if labels else 0
    
    mcc_den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    mcc = ((tp * tn) - (fp * fn)) / (mcc_den ** 0.5) if mcc_den > 0 else 0
    
    return {
        "total_items": total_items,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "performance_metrics": {
            "cohen_kappa": f"{kappa * 100:.2f}%",
            "accuracy": f"{accuracy * 100:.2f}%",
            "mcc": f"{mcc * 100:.2f}%",
            "f1_score": f"{f1_score * 100:.2f}%"
        }
    }


def find_common_methods():
    """查找在两个数据集中都存在的所有方法（模型+方法组合）"""
    base_dir = "output/rose-vec"
    bird_dir = os.path.join(base_dir, "rose-vec-bird")
    spider_dir = os.path.join(base_dir, "rose-vec-spider")
    
    # 获取 bird 数据集的所有方法
    bird_methods = set()
    if os.path.isdir(bird_dir):
        for model in os.listdir(bird_dir):
            model_dir = os.path.join(bird_dir, model)
            if not os.path.isdir(model_dir):
                continue
            for method in os.listdir(model_dir):
                method_dir = os.path.join(model_dir, method)
                if os.path.isdir(method_dir):
                    eval_file = os.path.join(method_dir, "eval_results.json")
                    if os.path.exists(eval_file):
                        bird_methods.add((model, method))
    
    # 获取 spider 数据集的所有方法
    spider_methods = set()
    if os.path.isdir(spider_dir):
        for model in os.listdir(spider_dir):
            model_dir = os.path.join(spider_dir, model)
            if not os.path.isdir(model_dir):
                continue
            for method in os.listdir(model_dir):
                method_dir = os.path.join(model_dir, method)
                if os.path.isdir(method_dir):
                    eval_file = os.path.join(method_dir, "eval_results.json")
                    if os.path.exists(eval_file):
                        spider_methods.add((model, method))
    
    # 找出共同存在的方法
    common_methods = bird_methods & spider_methods
    return sorted(list(common_methods))


def merge_and_analyze(model: str, method: str = "ROSE"):
    """
    合并两个数据集的结果并计算统计指标
    
    Args:
        model: 模型名称，如 "o3", "deepseek-r1", "gemini-2.5-pro" 等
        method: 方法名称，如 "ROSE", "ProverOnly", "FLEX" 等，默认为 "ROSE"
    """
    base_dir = "output/rose-vec"
    
    # 构建文件路径
    bird_file = os.path.join(base_dir, "rose-vec-bird", model, method, "eval_results.json")
    spider_file = os.path.join(base_dir, "rose-vec-spider", model, method, "eval_results.json")
    
    try:
        bird_data = load_eval_results(bird_file)
        spider_data = load_eval_results(spider_file)
    except FileNotFoundError as e:
        return None
    
    # 合并数据
    merged_data = bird_data + spider_data
    
    # 计算统计指标
    metrics = calculate_metrics(merged_data)
    
    if metrics is None:
        return None
    
    # 输出结果
    result = {
        "model": model,
        "method": method,
        "datasets": {
            "rose-vec-bird": len(bird_data),
            "rose-vec-spider": len(spider_data)
        },
        **metrics
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="合并 rose-vec-bird 和 rose-vec-spider 的结果并计算统计指标"
    )
    parser.add_argument("--model", type=str, default=None, help="指定模型名称（可选，如不指定则分析所有共同方法）")
    parser.add_argument("--method", type=str, default=None, help="指定方法名称（可选，如不指定则分析所有共同方法）")
    parser.add_argument("--output", type=str, default=None, help="输出 JSON 文件路径（可选）")
    args = parser.parse_args()
    
    # 如果指定了模型和方法，只分析那一个
    if args.model and args.method:
        common_methods = [(args.model, args.method)]
    elif args.model:
        # 只指定了模型，找出该模型的所有共同方法
        all_common = find_common_methods()
        common_methods = [(m, method) for m, method in all_common if m == args.model]
    else:
        # 没有指定，找出所有共同方法
        common_methods = find_common_methods()
    
    if not common_methods:
        print("No common methods found between rose-vec-bird and rose-vec-spider.")
        return
    
    print(f"Found {len(common_methods)} common method(s):")
    for model, method in common_methods:
        print(f"  - {model}/{method}")
    print()
    
    # 分析所有方法
    all_results = []
    for model, method in common_methods:
        print(f"Processing {model}/{method}...")
        result = merge_and_analyze(model, method)
        if result:
            all_results.append(result)
            print(f"  ✓ Merged: {result['datasets']['rose-vec-bird']} + {result['datasets']['rose-vec-spider']} = {result['total_items']} items")
        else:
            print(f"  ✗ Failed to process {model}/{method}")
        print()
    
    if not all_results:
        print("No valid results to display.")
        return
    
    # 打印汇总表格
    print("="*100)
    print(f"{'Model/Method':<30} {'Total':<8} {'TP':<6} {'TN':<6} {'FP':<6} {'FN':<6} {'Kappa':<12} {'Accuracy':<12} {'MCC':<12} {'F1':<12}")
    print("="*100)
    
    for result in all_results:
        model_method = f"{result['model']}/{result['method']}"
        cm = result['confusion_matrix']
        pm = result['performance_metrics']
        print(f"{model_method:<30} {result['total_items']:<8} {cm['tp']:<6} {cm['tn']:<6} {cm['fp']:<6} {cm['fn']:<6} "
              f"{pm['cohen_kappa']:<12} {pm['accuracy']:<12} {pm['mcc']:<12} {pm['f1_score']:<12}")
    
    print("="*100)
    
    # 保存到文件
    output_file = args.output or "output/rose-vec/merged_all_metrics.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_methods": len(all_results),
                "datasets": ["rose-vec-bird", "rose-vec-spider"]
            },
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nAll results saved to: {output_file}")


if __name__ == "__main__":
    main()

