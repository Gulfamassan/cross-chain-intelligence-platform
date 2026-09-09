"""
backend/evaluation/run_sprint20_final_benchmark.py

Sprint 20, Day 3 — Final Attribution Benchmark (FROZEN)

Sprint 16 ka n=7 ground truth dataset — poori Sprint 17-19 ki journey
ka final, consolidated comparison. Saare numbers is script ke FRESH
execution se aate hain (koi purana copy-paste nahi) — GraphSAGE aur
Cross-Chain GraphSAGE dono dobara train hote hain taake numbers
current code state ko reflect karein.

⚠️ Scope reminder (poori journey mein consistent): Random Forest/
XGBoost `n=4` (dev) par train, `n=3` (held-out) par evaluate —
Rule-Based/Node2Vec/GraphSAGE/Cross-Chain GNN `n=7` (poora dataset) par.

⚠️ n=7 case-study disclaimer (Day 4, Sprint 17): Ye statistically
reliable ML benchmark nahi hai — chhota, verified case-study hai.

Run from `backend/`: python -m evaluation.run_sprint20_final_benchmark
"""

import os

from evaluation.ground_truth import get_dataset
from evaluation.graphsage_split import get_dev_cases, get_held_out_cases
from evaluation.metrics import evaluation_metrics
from evaluation.run_graphsage_comparison import (
    resolve_csv_path, build_combined_graph, run_node2vec_evaluation,
)
from evaluation.experiments import similarity_experiment
from evaluation.run_cross_chain_graphsage_training import build_wallet_chain_csvs

from ai.node2vec_model import node2vec_trainer
from ai.feature_vector import build_feature_matrix
from ai.xgboost_model import xgboost_trainer
from ai.random_forest_model import random_forest_trainer
from ai.pyg_graphsage_trainer import train_pyg_graphsage
from ai.wallet_embeddings import classify_wallet_pair, save_embeddings as save_pyg_embeddings
from ai.cross_chain_wallet_embeddings import (
    classify_cross_chain_pair, save_embeddings as save_cross_chain_embeddings,
)
from graph.cross_chain_graph import build_unified_graph


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


def print_row(name: str, results: list, scope: str):
    m = evaluation_metrics.calculate_classification_metrics(results, positive_label="Related")
    print(f"{name:<20}{scope:<16}{m['accuracy']:<12}{m['precision']:<12}{m['recall']:<12}{m['f1_score']:<10}")


if __name__ == "__main__":
    dataset = get_dataset()
    dev_cases = get_dev_cases()
    held_out_cases = get_held_out_cases()

    print("Sprint 20 Day 3 — Final Attribution Benchmark (fresh execution)\n")

    # --- 1. Rule-Based (n=7) ---
    print("Running Rule-Based...")
    rule_report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)
    rule_results = [
        {"case_id": r["case_id"], "expected": r["expected"], "predicted": r["predicted"]}
        for r in rule_report["results"]
    ]

    # --- 2. Node2Vec (n=7) ---
    print("Running Node2Vec (training)...")
    combined_graph_obj = build_combined_graph(dataset)
    node2vec_embeddings = node2vec_trainer.train(combined_graph_obj.graph)
    node2vec_results = run_node2vec_evaluation(dataset, node2vec_embeddings)

    # --- 3. Random Forest (n=3 held-out, trained on n=4 dev) ---
    print("Running Random Forest (training on dev n=4)...")
    X_dev, y_dev = build_feature_matrix(dev_cases, resolve_csv_path)
    X_held_out, y_held_out = build_feature_matrix(held_out_cases, resolve_csv_path)
    random_forest_trainer.train(X_dev, y_dev)
    rf_predictions = random_forest_trainer.predict(X_held_out)
    rf_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, rf_predictions)
    ]

    # --- 4. XGBoost (n=3 held-out, trained on n=4 dev) ---
    print("Running XGBoost (training on dev n=4)...")
    xgboost_trainer.train(X_dev, y_dev)
    xgb_predictions = xgboost_trainer.predict(X_held_out)
    xgb_results = [
        {"case_id": c["case_id"], "expected": c["ground_truth"], "predicted": p["predicted"]}
        for c, p in zip(held_out_cases, xgb_predictions)
    ]

    # --- 5. GraphSAGE (n=7, fresh training — Sprint 18 methodology) ---
    print("Running GraphSAGE (fresh training on combined graph)...")
    graphsage_result = train_pyg_graphsage(
        combined_graph_obj.graph, checkpoint_path="models/pyg_graphsage_best.pt"
    )
    save_pyg_embeddings(graphsage_result["embeddings"])
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

    # --- 6. Cross-Chain GNN (n=7, fresh training — Sprint 19 methodology) ---
    print("Running Cross-Chain GNN (fresh training on unified graph)...")
    wallet_chain_csvs = build_wallet_chain_csvs()
    unified_graph = build_unified_graph(wallet_chain_csvs)
    cross_chain_result = train_pyg_graphsage(
        unified_graph, checkpoint_path="models/cross_chain_graphsage_best.pt"
    )
    save_cross_chain_embeddings(cross_chain_result["embeddings"])
    cross_chain_results = []
    for case in dataset:
        try:
            wallet_1_full = f"{case['chain_a'].lower()}:{case['wallet_a']}"
            wallet_2_full = f"{case['chain_b'].lower()}:{case['wallet_b']}"
            result = classify_cross_chain_pair(wallet_1_full, wallet_2_full)
            predicted = result["classification"]
        except (KeyError, ValueError):
            predicted = "Unrelated"
        cross_chain_results.append({
            "case_id": case["case_id"], "expected": case["ground_truth"], "predicted": predicted
        })

    # --- Final frozen table ---
    print("\n\n" + "=" * 84)
    print("FINAL ATTRIBUTION BENCHMARK (FROZEN — Sprint 16 n=7 dataset)")
    print("=" * 84)
    print(f"{'Model':<20}{'Scope':<16}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<10}")
    print("-" * 84)
    print_row("Rule-Based", rule_results, "n=7")
    print_row("Node2Vec", node2vec_results, "n=7")
    print_row("Random Forest", rf_results, "n=3 (held-out)")
    print_row("XGBoost", xgb_results, "n=3 (held-out)")
    print_row("GraphSAGE", graphsage_results, "n=7")
    print_row("Cross-Chain GNN", cross_chain_results, "n=7")

    print("\n" + "=" * 84)
    print("RELATED / UNRELATED DETECTION BREAKDOWN")
    print("=" * 84)
    print(f"{'Model':<20}{'Related':<12}{'Unrelated':<14}{'False Pos':<12}{'False Neg':<10}")
    print("-" * 84)
    for name, results in [
        ("Rule-Based", rule_results), ("Node2Vec", node2vec_results),
        ("Random Forest", rf_results), ("XGBoost", xgb_results),
        ("GraphSAGE", graphsage_results), ("Cross-Chain GNN", cross_chain_results),
    ]:
        b = confusion_breakdown(results)
        print(f"{name:<20}{b['related_detection']:<12}{b['unrelated_detection']:<14}"
              f"{b['false_positives']:<12}{b['false_negatives']:<10}")