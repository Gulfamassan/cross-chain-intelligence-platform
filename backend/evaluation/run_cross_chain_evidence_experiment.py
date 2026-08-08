"""
backend/evaluation/run_cross_chain_evidence_experiment.py

Sprint 14 Day 6 — tests whether replacing the structural 0
relationship_score (cross-chain pairs) with bridge-timing/amount
evidence changes Hybrid attribution outcomes.

Run from backend/: python -m evaluation.run_cross_chain_evidence_experiment
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
    tg = TransactionGraph()
    tg.load_csv(csv_path)
    tg.build_graph()
    return tg.graph


def run_case(case: dict) -> dict:
    wallet_1, chain_1 = case["wallet_a"], case["chain_a"]
    wallet_2, chain_2 = case["wallet_b"], case["chain_b"]

    csv_1 = resolve_csv_path(wallet_1, chain_1)
    csv_2 = resolve_csv_path(wallet_2, chain_2)

    graph = build_graph_from_csv(csv_2)

    rule_result = hybrid_scorer.calculate_rule_score(csv_1, csv_2, wallet_1, wallet_2, chain_2)
    embedding_score = hybrid_scorer.calculate_embedding_score(wallet_1, wallet_2)
    risk_score = hybrid_scorer.get_risk_score(csv_2, wallet_2, chain_2)

    baseline_relationship = hybrid_scorer.calculate_relationship_score(graph, wallet_1, wallet_2)
    bridge_relationship = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        graph, wallet_1, chain_1, csv_1, wallet_2, chain_2, csv_2
    )

    baseline = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=baseline_relationship["relationship_score"],
        risk_score=risk_score,
    )

    bridge_aware = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=bridge_relationship["relationship_score"],
        risk_score=risk_score,
    )

    return {
        "case_id": case["case_id"],
        "expected": case["ground_truth"],
        "rule": round(rule_result["rule_score"], 2),
        "baseline_hybrid": round(baseline["final_confidence"] / 100, 2),
        "bridge_aware_hybrid": round(bridge_aware["final_confidence"] / 100, 2),
        "bridge_relationship_score": bridge_relationship["relationship_score"],
        "bridge_source": bridge_relationship["source"],
        "matched_pairs": bridge_relationship.get("matched_bridge_pairs", 0),
    }


if __name__ == "__main__":
    dataset = get_dataset()

    print(f"{'Case':<6}{'Expected':<12}{'Rule':<8}{'Baseline':<11}{'BridgeAware':<13}{'BridgeScr':<11}{'Source':<20}{'Matches'}")
    for case in dataset:
        r = run_case(case)
        print(
            f"{r['case_id']:<6}{r['expected']:<12}{r['rule']:<8}{r['baseline_hybrid']:<11}"
            f"{r['bridge_aware_hybrid']:<13}{r['bridge_relationship_score']:<11}{r['bridge_source']:<20}{r['matched_pairs']}"
        )