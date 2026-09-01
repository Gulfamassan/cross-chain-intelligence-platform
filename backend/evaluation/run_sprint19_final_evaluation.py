"""
backend/evaluation/run_sprint19_final_evaluation.py

Sprint 19, Day 7 — Final Model Evaluation

Saare 7 methods ko n=7 ground truth par evaluate karta hai, aur
SEPARATELY "cross-chain subset" (wo cases jahan wallet_1, wallet_2
alag chains pe hain) ka breakdown deta hai — jo Sprint 19 ka poora
point tha (Sprint 14-16 ki core limitation: single-chain graph
cross-chain related wallets properly represent nahi karta tha).

⚠️ Scope disclaimer (jaisa pehle bhi kaha): Random Forest/XGBoost
`n=3 (held-out)` par evaluate hote hain (supervised, `n=4` training),
baaki sab `n=7` par (unsupervised).

Run from `backend/`: python -m evaluation.run_sprint19_final_evaluation
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
from ai.cross_chain_wallet_embeddings import classify_cross_chain_pair


def confusion_breakdown(results: list) -> dict:
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
    print(f"{name:<22}{scope:<16}{m['accuracy']:<12}{m['precision']:<12}{m['recall']:<12}{m['f1_score']:<10}")


if __name__ == "__main__":
    dataset = get_dataset()
    dev_cases = get_dev_cases()
    held_out_cases = get_held_out_cases()

    # Cross-chain subset identify karte hain (chain_a != chain_b)
    cross_chain_case_ids = {c["case_id"] for c in dataset if c["chain_a"].lower() != c["chain_b"].lower()}
    print(f"Cross-chain cases (out of n=7): {sorted(cross_chain_case_ids)}\n")

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

    # --- Random Forest (n=3 held-out) ---
    X_dev, y_dev = build_feature_matrix(dev_cases, resolve_csv_path)
    X_held_out, y_held_out = build_feature_matrix(held_out_cases, resolve_csv_path)
    random_forest_trainer.train(X_dev, y_dev)
    rf_predictions = random_forest_trainer.predict(X_held_out)
    rf_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, rf_predictions)
    ]

    # --- XGBoost (n=3 held-out) ---
    xgboost_trainer.train(X_dev, y_dev)
    xgb_predictions = xgboost_trainer.predict(X_held_out)
    xgb_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, xgb_predictions)
    ]

    # --- GraphSAGE / Sprint 18 PyG (n=7) ---
    graphsage_results = []
    for case in dataset:
        try:
            result = classify_wallet_pair(case["wallet_a"], case["wallet_b"])
            predicted = result["classification"]
        except KeyError:
            predicted = "Unrelated"
        graphsage_results.append({
            "case_id": case["case_id"], "expected": case["ground_truth"], "predicted": predicted
        })

    # --- Cross-Chain GraphSAGE / Sprint 19 (n=7) ---
    cross_chain_graphsage_results = []
    for case in dataset:
        try:
            wallet_1_full = f"{case['chain_a'].lower()}:{case['wallet_a']}"
            wallet_2_full = f"{case['chain_b'].lower()}:{case['wallet_b']}"
            result = classify_cross_chain_pair(wallet_1_full, wallet_2_full)
            predicted = result["classification"]
        except (KeyError, ValueError):
            predicted = "Unrelated"
        cross_chain_graphsage_results.append({
            "case_id": case["case_id"], "expected": case["ground_truth"], "predicted": predicted
        })

    all_methods_n7 = {
        "Rule-Based": rule_results,
        "Node2Vec": node2vec_results,
        "Hybrid": hybrid_results,
        "GraphSAGE": graphsage_results,
        "Cross-Chain GraphSAGE": cross_chain_graphsage_results,
    }
    all_methods_held_out = {
        "Random Forest": rf_results,
        "XGBoost": xgb_results,
    }

    print("=" * 84)
    print("FINAL COMPARISON TABLE")
    print("=" * 84)
    print(f"{'Model':<22}{'Scope':<16}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<10}")
    print("-" * 84)
    for name, results in all_methods_n7.items():
        print_metrics_row(name, results, "n=7")
    for name, results in all_methods_held_out.items():
        print_metrics_row(name, results, "n=3 (held-out)")

    print("\n" + "=" * 84)
    print("RELATED / UNRELATED DETECTION BREAKDOWN (full n=7 or held-out, per above)")
    print("=" * 84)
    print(f"{'Model':<22}{'Related':<12}{'Unrelated':<14}{'False Pos':<12}{'False Neg':<10}")
    print("-" * 84)
    for name, results in {**all_methods_n7, **all_methods_held_out}.items():
        b = confusion_breakdown(results)
        print(f"{name:<22}{b['related_detection']:<12}{b['unrelated_detection']:<14}"
              f"{b['false_positives']:<12}{b['false_negatives']:<10}")

    # --- Cross-chain SUBSET breakdown (Sprint 19 ka poora point) ---
    print("\n" + "=" * 84)
    print("CROSS-CHAIN SUBSET ONLY (5 of 7 cases where chain_a != chain_b)")
    print("=" * 84)
    print(f"{'Model':<22}{'Cross-chain Related':<22}{'Cross-chain Unrelated':<22}")
    print("-" * 84)
    for name, results in all_methods_n7.items():
        subset = [r for r in results if r["case_id"] in cross_chain_case_ids]
        b = confusion_breakdown(subset)
        print(f"{name:<22}{b['related_detection']:<22}{b['unrelated_detection']:<22}")

    # Random Forest/XGBoost held-out set: cross-chain subset within held-out only
    print("\n(Random Forest/XGBoost held-out n=3 cross-chain subset:)")
    for name, results in all_methods_held_out.items():
        subset = [r for r in results if r["case_id"] in cross_chain_case_ids]
        b = confusion_breakdown(subset)
        print(f"{name:<22}{b['related_detection']:<22}{b['unrelated_detection']:<22}")