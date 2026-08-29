"""
backend/evaluation/run_sprint18_final_evaluation.py

Sprint 18, Day 7 — Final GNN Evaluation

⚠️ SCOPE DISCLAIMER (bahut important):
- Rule, Node2Vec, Hybrid, GraphSAGE (PyG) — UNSUPERVISED hain, poore
  n=7 ground truth par evaluate hote hain.
- Random Forest, XGBoost — SUPERVISED hain, `dev n=4` par train hue
  the (Sprint 17 Day 4 split), isliye INKA fair evaluation sirf
  `held-out n=3` par hai — n=7 par nahi. Dono ko seedha compare karna
  apples-to-oranges hoga, is script mein explicitly alag scope label
  kiya gaya hai.

⚠️ ARCHITECTURE DISCLAIMER (jaisa Day 7 instructions mein kaha gaya):
Ye GraphSAGE ek "controlled"/single-merged-graph model hai — Sprint 17
Day 6 ke true cross-chain unified graph (`(address, chain)` composite
nodes + bridge/same_address/known_exchange edges) se ALAG hai. Wo
distinction Sprint 19 mein banegi. Is evaluation ka GraphSAGE result
isliye "cross-chain attribution ka final answer" nahi hai — abhi
sirf "controlled graph par GraphSAGE kaisा perform karta hai" hai.

Run from `backend/`: python -m evaluation.run_sprint18_final_evaluation
"""

from evaluation.ground_truth import get_dataset
from evaluation.graphsage_split import get_dev_cases, get_held_out_cases
from evaluation.metrics import evaluation_metrics
from evaluation.run_graphsage_comparison import (
    resolve_csv_path, build_combined_graph, run_node2vec_evaluation,
    run_hybrid_evaluation,
)
from evaluation.experiments import similarity_experiment

from ai.node2vec_model import node2vec_trainer
from ai.feature_vector import build_feature_matrix
from ai.xgboost_model import xgboost_trainer
from ai.random_forest_model import random_forest_trainer
from ai.wallet_embeddings import classify_wallet_pair


def confusion_breakdown(results: list) -> dict:
    """
    Related Detection / Unrelated Detection / False Positives /
    False Negatives nikalta hai.
    """
    related_total = sum(1 for r in results if r["expected"] == "Related")
    unrelated_total = sum(1 for r in results if r["expected"] == "Unrelated")

    related_correct = sum(1 for r in results if r["expected"] == "Related" and r["predicted"] == "Related")
    unrelated_correct = sum(1 for r in results if r["expected"] == "Unrelated" and r["predicted"] == "Unrelated")

    false_positives = sum(1 for r in results if r["expected"] == "Unrelated" and r["predicted"] == "Related")
    false_negatives = sum(1 for r in results if r["expected"] == "Related" and r["predicted"] == "Unrelated")

    return {
        "related_detection": f"{related_correct}/{related_total}",
        "unrelated_detection": f"{unrelated_correct}/{unrelated_total}",
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def print_metrics_row(name: str, results: list, scope: str):
    m = evaluation_metrics.calculate_classification_metrics(results, positive_label="Related")
    print(f"{name:<20}{scope:<12}{m['accuracy']:<12}{m['precision']:<12}{m['recall']:<12}{m['f1_score']:<10}")


if __name__ == "__main__":
    dataset = get_dataset()
    dev_cases = get_dev_cases()
    held_out_cases = get_held_out_cases()

    # --- Rule (n=7) ---
    rule_report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)
    rule_results = [
        {"case_id": r["case_id"], "expected": r["expected"], "predicted": r["predicted"]}
        for r in rule_report["results"]
    ]

    # --- Node2Vec (n=7) ---
    combined_graph_obj = build_combined_graph(dataset)
    node2vec_embeddings = node2vec_trainer.train(combined_graph_obj.graph)
    node2vec_results = run_node2vec_evaluation(dataset, node2vec_embeddings)

    # --- Hybrid (n=7) ---
    hybrid_results = run_hybrid_evaluation(dataset, combined_graph_obj.graph)

    # --- Random Forest (held-out n=3 only, trained on dev n=4) ---
    X_dev, y_dev = build_feature_matrix(dev_cases, resolve_csv_path)
    X_held_out, y_held_out = build_feature_matrix(held_out_cases, resolve_csv_path)

    random_forest_trainer.train(X_dev, y_dev)
    rf_predictions = random_forest_trainer.predict(X_held_out)
    rf_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, rf_predictions)
    ]

    # --- XGBoost (held-out n=3 only, trained on dev n=4) ---
    xgboost_trainer.train(X_dev, y_dev)
    xgb_predictions = xgboost_trainer.predict(X_held_out)
    xgb_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, xgb_predictions)
    ]

    # --- GraphSAGE / PyG (n=7) — uses Day 5/6 trained embeddings ---
    graphsage_results = []
    for case in dataset:
        try:
            result = classify_wallet_pair(case["wallet_a"], case["wallet_b"])
            predicted = result["classification"]
        except KeyError:
            predicted = "Unrelated"  # fallback, embedding na milne par
        graphsage_results.append({
            "case_id": case["case_id"], "expected": case["ground_truth"], "predicted": predicted
        })

    print("=" * 78)
    print("FINAL COMPARISON TABLE")
    print("=" * 78)
    print(f"{'Model':<20}{'Scope':<12}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<10}")
    print("-" * 78)
    print_metrics_row("Rule-Based", rule_results, "n=7")
    print_metrics_row("Node2Vec", node2vec_results, "n=7")
    print_metrics_row("Hybrid", hybrid_results, "n=7")
    print_metrics_row("Random Forest", rf_results, "n=3 (held-out)")
    print_metrics_row("XGBoost", xgb_results, "n=3 (held-out)")
    print_metrics_row("GraphSAGE (PyG)", graphsage_results, "n=7")

    print("\n" + "=" * 78)
    print("RELATED / UNRELATED DETECTION BREAKDOWN")
    print("=" * 78)
    print(f"{'Model':<20}{'Related':<12}{'Unrelated':<14}{'False Pos':<12}{'False Neg':<10}")
    print("-" * 78)
    for name, results in [
        ("Rule-Based", rule_results), ("Node2Vec", node2vec_results),
        ("Hybrid", hybrid_results), ("Random Forest", rf_results),
        ("XGBoost", xgb_results), ("GraphSAGE (PyG)", graphsage_results),
    ]:
        b = confusion_breakdown(results)
        print(f"{name:<20}{b['related_detection']:<12}{b['unrelated_detection']:<14}"
              f"{b['false_positives']:<12}{b['false_negatives']:<10}")

    print("\n" + "=" * 78)
    print("REMINDER: Random Forest/XGBoost evaluated on n=3 (held-out) only —")
    print("not directly comparable to the n=7 rows above. See file docstring.")
    print("REMINDER: GraphSAGE (PyG) here is a controlled/single-merged-graph")
    print("model, NOT the true cross-chain unified graph (that's Sprint 19).")