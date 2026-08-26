"""
backend/evaluation/run_graphsage_comparison.py

Sprint 17, Day 5 — Compares all 4 attribution methods (Rule-Based,
Node2Vec, Hybrid, GraphSAGE) on the SAME n=7 ground truth dataset
(`evaluation/ground_truth.py`), using the SAME 0.5 (rule/embedding
scale) or 50 (hybrid 0-100 scale) decision threshold convention
already used elsewhere in this project.

IMPORTANT (see Day 4 disclaimer, evaluation/graphsage_split.py):
n=7 is a small case-study dataset, NOT a statistically powered ML
benchmark. Treat every number below as a qualitative signal about
these 7 specific, verified wallet pairs — not a general-purpose
accuracy claim.

Run from the `backend/` directory: python -m evaluation.run_graphsage_comparison
"""

import os
import pandas as pd

from graph.builder import TransactionGraph
from evaluation.ground_truth import get_dataset
from evaluation.experiments import similarity_experiment
from evaluation.metrics import evaluation_metrics

from ai.node2vec_model import node2vec_trainer
from ai.graphsage_model import graphsage_trainer, classify_relation
from ai.similarity_model import embedding_similarity

from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine


def resolve_csv_path(wallet_address: str, chain: str) -> str:
    """Same convention used across the project: datasets/{chain}/{address}.csv"""
    path = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return path


def build_combined_graph(ground_truth_cases: list) -> TransactionGraph:
    """
    Node2Vec aur GraphSAGE ko ek hi, saanjha (shared) graph chahiye —
    taake dono wallets ka embedding usi ek embedding-space mein bane
    (alag-alag chhote graphs pe train kiya to embeddings comparable
    nahi hongi). Isliye saare 7 cases ke unique (wallet, chain) CSVs
    ko ek combined graph mein load karte hain.
    """
    seen_files = set()
    combined_frames = []

    for case in ground_truth_cases:
        for wallet_key, chain_key in [("wallet_a", "chain_a"), ("wallet_b", "chain_b")]:
            wallet = case[wallet_key]
            chain = case[chain_key]
            csv_path = resolve_csv_path(wallet, chain)

            if csv_path in seen_files:
                continue
            seen_files.add(csv_path)

            df = pd.read_csv(csv_path)
            combined_frames.append(df)

    combined_df = pd.concat(combined_frames, ignore_index=True)

    graph = TransactionGraph()
    graph.data = combined_df
    graph.build_graph()

    return graph


def classify_by_threshold(score: float, threshold: float) -> str:
    return "Related" if score >= threshold else "Unrelated"


def run_node2vec_evaluation(ground_truth_cases: list, embeddings: dict) -> dict:
    results = []
    for case in ground_truth_cases:
        try:
            sim_result = embedding_similarity.compare_wallets(
                embeddings, case["wallet_a"], case["wallet_b"]
            )
            score = sim_result["ai_similarity"]
        except ValueError:
            score = 0.0

        predicted = classify_by_threshold(score, threshold=0.5)
        results.append({
            "case_id": case["case_id"],
            "expected": case["ground_truth"],
            "predicted": predicted,
            "score": score,
        })
    return results


def run_graphsage_evaluation(ground_truth_cases: list, embeddings: dict) -> dict:
    results = []
    for case in ground_truth_cases:
        try:
            sim_result = embedding_similarity.compare_wallets(
                embeddings, case["wallet_a"], case["wallet_b"]
            )
            score = sim_result["ai_similarity"]
        except ValueError:
            score = 0.0

        predicted = classify_relation(score, threshold=0.5)
        results.append({
            "case_id": case["case_id"],
            "expected": case["ground_truth"],
            "predicted": predicted,
            "score": score,
        })
    return results


def run_hybrid_evaluation(ground_truth_cases: list, graph) -> dict:
    """
    Full production hybrid pipeline (Rule + Node2Vec embedding +
    Relationship + Risk -> Fusion Engine) — same components
    `/hybrid/analyze` API endpoint uses.
    """
    results = []
    for case in ground_truth_cases:
        csv_a = resolve_csv_path(case["wallet_a"], case["chain_a"])
        csv_b = resolve_csv_path(case["wallet_b"], case["chain_b"])

        rule_result = hybrid_scorer.calculate_rule_score(
            csv_a, csv_b, case["wallet_a"], case["wallet_b"], case["chain_b"]
        )
        embedding_score = hybrid_scorer.calculate_embedding_score(case["wallet_a"], case["wallet_b"])
        relationship_result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
            graph, case["wallet_a"], case["chain_a"], csv_a,
            case["wallet_b"], case["chain_b"], csv_b,
        )
        risk_score = hybrid_scorer.get_risk_score(csv_b, case["wallet_b"], case["chain_b"])

        fusion_result = fusion_engine.combine_scores(
            rule_score=rule_result["rule_score"],
            embedding_score=embedding_score,
            relationship_score=relationship_result["relationship_score"],
            risk_score=risk_score,
        )

        # Consistent decision rule with the 0.5-on-0..1-scale convention
        # used elsewhere: 50 on this 0..100 scale is the same midpoint.
        predicted = classify_by_threshold(fusion_result["final_confidence"], threshold=50)

        results.append({
            "case_id": case["case_id"],
            "expected": case["ground_truth"],
            "predicted": predicted,
            "score": fusion_result["final_confidence"],
        })
    return results


def related_case_breakdown(results: list) -> str:
    related_cases = [r for r in results if r["expected"] == "Related"]
    correct = sum(1 for r in related_cases if r["predicted"] == "Related")
    return f"{correct}/{len(related_cases)}"


if __name__ == "__main__":
    dataset = get_dataset()

    print("Building combined graph from all n=7 case wallets...")
    combined_graph_obj = build_combined_graph(dataset)
    print(f"  -> {combined_graph_obj.graph.number_of_nodes()} nodes, "
          f"{combined_graph_obj.graph.number_of_edges()} edges\n")

    print("Training Node2Vec on combined graph...")
    node2vec_embeddings = node2vec_trainer.train(combined_graph_obj.graph)

    print("Training GraphSAGE on combined graph...")
    graphsage_embeddings = graphsage_trainer.train(combined_graph_obj.graph)

    # --- Rule-Based (reuses existing evaluation pipeline) ---
    rule_report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)
    rule_results = [
        {"case_id": r["case_id"], "expected": r["expected"], "predicted": r["predicted"], "score": r["ai_score"]}
        for r in rule_report["results"]
    ]

    # --- Node2Vec ---
    node2vec_results = run_node2vec_evaluation(dataset, node2vec_embeddings)

    # --- Hybrid (full fusion pipeline) ---
    hybrid_results = run_hybrid_evaluation(dataset, combined_graph_obj.graph)

    # --- GraphSAGE ---
    graphsage_results = run_graphsage_evaluation(dataset, graphsage_embeddings)

    all_methods = {
        "Rule": rule_results,
        "Node2Vec": node2vec_results,
        "Hybrid": hybrid_results,
        "GraphSAGE": graphsage_results,
    }

    print("\n" + "=" * 70)
    print("COMPARISON TABLE (n=7, full dataset — see Day 4 disclaimer)")
    print("=" * 70)
    print(f"{'Method':<12}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1':<10}")
    print("-" * 70)

    for method_name, results in all_methods.items():
        metrics = evaluation_metrics.calculate_classification_metrics(results, positive_label="Related")
        print(f"{method_name:<12}{metrics['accuracy']:<12}{metrics['precision']:<12}"
              f"{metrics['recall']:<12}{metrics['f1_score']:<10}")

    print("\n" + "=" * 70)
    print("RELATED CASES ONLY (n=3 genuine 'Related' pairs)")
    print("=" * 70)
    for method_name, results in all_methods.items():
        print(f"{method_name:<12}{related_case_breakdown(results)}")

    print("\n" + "=" * 70)
    print("PER-CASE DETAIL (GraphSAGE)")
    print("=" * 70)
    for r in graphsage_results:
        status = "correct" if r["expected"] == r["predicted"] else "WRONG"
        print(f"Case {r['case_id']}: expected={r['expected']:<10} "
              f"predicted={r['predicted']:<10} score={r['score']:<8} [{status}]")