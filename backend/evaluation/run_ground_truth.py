"""
backend/evaluation/run_ground_truth.py

Sprint 14 Day 2 — standalone runner script.
Executes the ground truth experiment, then converts results into
formal classification metrics (precision/recall/F1/accuracy/FPR/FNR).
Run from the `backend/` directory: python -m evaluation.run_ground_truth
"""

import os
from evaluation.ground_truth import get_dataset
from evaluation.experiments import similarity_experiment
from evaluation.metrics import evaluation_metrics


def resolve_csv_path(wallet_address: str, chain: str) -> str:
    """Same convention used across the project: datasets/{chain}/{address}.csv"""
    path = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return path


if __name__ == "__main__":
    dataset = get_dataset()
    report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)

    print(f"\nRaw Accuracy: {report['accuracy']}% ({report['correct']}/{report['total']} correct)\n")

    for r in report["results"]:
        status = "✅ CORRECT" if r["correct"] else "❌ WRONG"
        print(f"Case {r['case_id']}: {status}")
        print(f"  {r['wallet_1']} ({r['chain_1']}) vs {r['wallet_2']} ({r['chain_2']})")
        print(f"  Expected: {r['expected']} | Predicted: {r['predicted']} | AI Score: {r['ai_score']}")
        print()

    # Sprint 14 Day 2: formal classification metrics
    metrics = evaluation_metrics.calculate_classification_metrics(report["results"], positive_label="Related")

    print("=" * 50)
    print("CLASSIFICATION METRICS (positive class = 'Related')")
    print("=" * 50)
    cm = metrics["confusion_matrix"]
    print(f"True Positive:  {cm['true_positive']}")
    print(f"False Positive: {cm['false_positive']}")
    print(f"True Negative:  {cm['true_negative']}")
    print(f"False Negative: {cm['false_negative']}")
    print()
    print(f"Precision:            {metrics['precision']}")
    print(f"Recall:               {metrics['recall']}")
    print(f"F1-Score:             {metrics['f1_score']}")
    print(f"Accuracy:             {metrics['accuracy']}")
    print(f"False Positive Rate:  {metrics['false_positive_rate']}")
    print(f"False Negative Rate:  {metrics['false_negative_rate']}")
    print(f"Total Cases:          {metrics['total_cases']}")