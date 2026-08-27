"""
backend/evaluation/run_final_experiment.py

Sprint 17, Day 7 — Final Experiment.

Runs ALL 5 methods on the SAME n=7 ground truth dataset:
    Rule -> Node2Vec -> Existing Hybrid -> GraphSAGE -> Cross-Chain GraphSAGE

Reminder (Day 4 disclaimer still applies): n=7 hai, statistically
reliable ML benchmark nahi — chhota case-study hai. Numbers "signal"
hain, "proof" nahi.

Run from `backend/`: python -m evaluation.run_final_experiment
"""

import os

from evaluation.ground_truth import get_dataset
from evaluation.metrics import evaluation_metrics
from evaluation.run_graphsage_comparison import (
    resolve_csv_path,
    build_combined_graph,
    run_node2vec_evaluation,
    run_hybrid_evaluation,
    run_graphsage_evaluation,
    related_case_breakdown,
)
from evaluation.experiments import similarity_experiment

from graph.cross_chain_graph import build_unified_graph
from ai.node2vec_model import node2vec_trainer
from ai.graphsage_model import graphsage_trainer, classify_relation
from ai.similarity_model import embedding_similarity


def infer_chain_from_path(csv_path: str) -> str:
    """datasets/{chain}/{address}.csv se chain naam nikalta hai."""
    return csv_path.split(os.sep)[1] if os.sep in csv_path else csv_path.split("/")[1]


def run_cross_chain_graphsage_evaluation(ground_truth_cases: list) -> list:
    """
    Cross-Chain GraphSAGE: Day 6 ke unified graph (`(address, chain)`
    composite nodes) par train karta hai — taake bridge/same_address/
    known_exchange edges bhi model ko dikhein, na ke sirf raw
    transactions.
    """
    seen_files = set()
    wallet_chain_csvs = []

    for case in ground_truth_cases:
        for wallet_key, chain_key in [("wallet_a", "chain_a"), ("wallet_b", "chain_b")]:
            wallet = case[wallet_key]
            chain = case[chain_key]
            csv_path = resolve_csv_path(wallet, chain)
            if csv_path in seen_files:
                continue
            seen_files.add(csv_path)
            wallet_chain_csvs.append((csv_path, chain))

    unified_graph = build_unified_graph(wallet_chain_csvs)
    embeddings = graphsage_trainer.train(unified_graph)

    results = []
    for case in ground_truth_cases:
        node_a = f"{case['wallet_a'].lower()}__{case['chain_a'].lower()}"
        node_b = f"{case['wallet_b'].lower()}__{case['chain_b'].lower()}"

        if node_a in embeddings and node_b in embeddings:
            sim_result = embedding_similarity.compare_wallets(
                {node_a: embeddings[node_a], node_b: embeddings[node_b]}, node_a, node_b
            )
            score = sim_result["ai_similarity"]
        else:
            score = 0.0

        predicted = classify_relation(score, threshold=0.5)
        results.append({
            "case_id": case["case_id"],
            "expected": case["ground_truth"],
            "predicted": predicted,
            "score": score,
        })

    return results, unified_graph


if __name__ == "__main__":
    dataset = get_dataset()

    print("=" * 70)
    print("STAGE 1/5 — Rule")
    print("=" * 70)
    rule_report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)
    rule_results = [
        {"case_id": r["case_id"], "expected": r["expected"], "predicted": r["predicted"], "score": r["ai_score"]}
        for r in rule_report["results"]
    ]
    print(f"Done. Related cases correct: {related_case_breakdown(rule_results)}")

    print("\n" + "=" * 70)
    print("STAGE 2/5 — Node2Vec")
    print("=" * 70)
    combined_graph_obj = build_combined_graph(dataset)
    node2vec_embeddings = node2vec_trainer.train(combined_graph_obj.graph)
    node2vec_results = run_node2vec_evaluation(dataset, node2vec_embeddings)
    print(f"Done. Related cases correct: {related_case_breakdown(node2vec_results)}")

    print("\n" + "=" * 70)
    print("STAGE 3/5 — Existing Hybrid")
    print("=" * 70)
    hybrid_results = run_hybrid_evaluation(dataset, combined_graph_obj.graph)
    print(f"Done. Related cases correct: {related_case_breakdown(hybrid_results)}")

    print("\n" + "=" * 70)
    print("STAGE 4/5 — GraphSAGE (single-chain, post embedding-collapse fix)")
    print("=" * 70)
    graphsage_embeddings = graphsage_trainer.train(combined_graph_obj.graph)
    graphsage_results = run_graphsage_evaluation(dataset, graphsage_embeddings)
    print(f"Done. Related cases correct: {related_case_breakdown(graphsage_results)}")

    print("\n" + "=" * 70)
    print("STAGE 5/5 — Cross-Chain GraphSAGE (Day 6 unified graph)")
    print("=" * 70)
    cross_chain_results, unified_graph = run_cross_chain_graphsage_evaluation(dataset)
    print(f"  -> Unified graph: {unified_graph.number_of_nodes()} nodes, "
          f"{unified_graph.number_of_edges()} edges")
    print(f"Done. Related cases correct: {related_case_breakdown(cross_chain_results)}")

    all_methods = {
        "Rule": rule_results,
        "Node2Vec": node2vec_results,
        "Hybrid": hybrid_results,
        "GraphSAGE": graphsage_results,
        "Cross-Chain GraphSAGE": cross_chain_results,
    }

    print("\n\n" + "=" * 78)
    print("FINAL COMPARISON TABLE (n=7 — small case study, see Day 4 disclaimer)")
    print("=" * 78)
    print(f"{'Method':<24}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<10}")
    print("-" * 78)
    for method_name, results in all_methods.items():
        m = evaluation_metrics.calculate_classification_metrics(results, positive_label="Related")
        print(f"{method_name:<24}{m['accuracy']:<12}{m['precision']:<12}{m['recall']:<12}{m['f1_score']:<10}")

    print("\n" + "=" * 78)
    print("RELATED CASES ONLY (n=3 genuine 'Related' pairs)")
    print("=" * 78)
    for method_name, results in all_methods.items():
        print(f"{method_name:<24}{related_case_breakdown(results)}")

    print("\n" + "=" * 78)
    print("PER-CASE DETAIL — GraphSAGE vs Cross-Chain GraphSAGE")
    print("=" * 78)
    for r1, r2 in zip(graphsage_results, cross_chain_results):
        print(f"Case {r1['case_id']}: expected={r1['expected']:<10} | "
              f"GraphSAGE={r1['predicted']:<10}(score={r1['score']:.3f}) | "
              f"Cross-Chain={r2['predicted']:<10}(score={r2['score']:.3f})")