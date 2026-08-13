"""
backend/evaluation/run_entity_agreement_fusion_experiment.py

Sprint 15 Day 3 — Current (Rule+Node2Vec+Graph) vs Experimental
(+ Entity Agreement) fusion comparison, using the same 3 ground-truth
cases from Sprint 14 for direct comparability.

Run from backend/: python -m evaluation.run_entity_agreement_fusion_experiment
"""

import os
from evaluation.ground_truth import get_dataset
from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine
from attribution.entity_agreement import calculate_entity_agreement
from features.extractor import feature_extractor
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
    relationship_result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        graph, wallet_1, chain_1, csv_1, wallet_2, chain_2, csv_2
    )
    risk_score = hybrid_scorer.get_risk_score(csv_2, wallet_2, chain_2)

    profile_1 = feature_extractor.get_wallet_summary(csv_1, wallet_1, chain_1).to_dict()
    profile_2 = feature_extractor.get_wallet_summary(csv_2, wallet_2, chain_2).to_dict()
    agreement = calculate_entity_agreement(wallet_1, profile_1, False, wallet_2, profile_2, False)

    current = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        risk_score=risk_score,
    )

    experimental = fusion_engine.combine_scores_with_entity_agreement(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        risk_score=risk_score,
        entity_agreement_score=agreement["score"],
    )

    return {
        "case_id": case["case_id"],
        "expected": case["ground_truth"],
        "current_hybrid": round(current["final_confidence"] / 100, 2),
        "experimental_hybrid": round(experimental["final_confidence"] / 100, 2),
        "entity_state": agreement["state"],
        "entity_weight_used": experimental["entity_agreement_weight_used"],
    }


if __name__ == "__main__":
    dataset = get_dataset()

    print(f"{'Case':<6}{'Expected':<12}{'Current':<10}{'Experimental':<14}{'EntityState':<13}{'WeightUsed'}")
    for case in dataset:
        r = run_case(case)
        print(
            f"{r['case_id']:<6}{r['expected']:<12}{r['current_hybrid']:<10}"
            f"{r['experimental_hybrid']:<14}{r['entity_state']:<13}{r['entity_weight_used']}"
        )