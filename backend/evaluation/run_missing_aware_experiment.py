"""
backend/evaluation/run_missing_aware_experiment.py

Sprint 14 Day 4 — Missing-Signal / Cross-Chain Graph Limitation Experiment.

Compares:
  Version A (Baseline) — existing fusion, relationship_score treated as 0
                          when the graph signal is unavailable
  Version B (Missing-Aware) — relationship_score treated as None and
                          excluded from fusion, weight redistributed

Purpose: determine whether treating unavailable graph evidence as zero
is causing degradation in Hybrid scores for cross-chain pairs — NOT to
make Hybrid "beat" Rule. Report actual numbers either way.

Run from backend/: python -m evaluation.run_missing_aware_experiment
"""

import os
from evaluation.ground_truth import get_dataset
from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine
from graph.builder import TransactionGraph


def resolve_csv_path(wallet_address: str, chain: str) -> str:
    path = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return path


def build_graph_from_csv(csv_path: str):
    """Builds a fresh NetworkX graph from a single chain's CSV."""
    tg = TransactionGraph()
    tg.load_csv(csv_path)
    tg.build_graph()
    return tg.graph


def run_case(case: dict) -> dict:
    wallet_1, chain_1 = case["wallet_a"], case["chain_a"]
    wallet_2, chain_2 = case["wallet_b"], case["chain_b"]

    csv_1 = resolve_csv_path(wallet_1, chain_1)
    csv_2 = resolve_csv_path(wallet_2, chain_2)

    # Build the graph from wallet_2's chain only — same convention
    # used in Day 3's Swagger testing.
    graph = build_graph_from_csv(csv_2)

    rule_result = hybrid_scorer.calculate_rule_score(csv_1, csv_2, wallet_1, wallet_2, chain_2)
    embedding_score = hybrid_scorer.calculate_embedding_score(wallet_1, wallet_2)
    relationship_result = hybrid_scorer.calculate_relationship_score(graph, wallet_1, wallet_2)
    risk_score = hybrid_scorer.get_risk_score(csv_2, wallet_2, chain_2)

    # calculate_relationship_score() itself tells us whether wallet_1
    # was actually present in the graph (common_neighbors_count is only
    # meaningful if both wallets were found). We use that + the
    # cross-chain check together to decide "genuinely missing" vs "real 0".
    is_cross_chain = chain_1 != chain_2
    wallet_1_absent_from_graph = wallet_1.lower() not in graph

    treat_as_missing = is_cross_chain and wallet_1_absent_from_graph
    relationship_for_missing_aware = None if treat_as_missing else relationship_result["relationship_score"]

    baseline = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        risk_score=risk_score,
    )

    missing_aware = fusion_engine.combine_scores_missing_aware(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_for_missing_aware,
        risk_score=risk_score,
    )

    return {
        "case_id": case["case_id"],
        "expected": case["ground_truth"],
        "is_cross_chain": is_cross_chain,
        "treated_as_missing": treat_as_missing,
        "rule_score_100": round(rule_result["rule_score"], 2),
        "baseline_hybrid": round(baseline["final_confidence"] / 100, 2),
        "missing_aware_hybrid": round(missing_aware["final_confidence"] / 100, 2),
    }


if __name__ == "__main__":
    dataset = get_dataset()

    print(f"{'Case':<6}{'Expected':<12}{'CrossChain':<12}{'TreatMissing':<14}{'Rule':<8}{'Baseline':<11}{'MissingAware'}")
    for case in dataset:
        result = run_case(case)
        print(
            f"{result['case_id']:<6}{result['expected']:<12}"
            f"{str(result['is_cross_chain']):<12}{str(result['treated_as_missing']):<14}"
            f"{result['rule_score_100']:<8}{result['baseline_hybrid']:<11}{result['missing_aware_hybrid']}"
        )