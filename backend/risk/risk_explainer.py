"""
backend/risk/risk_explainer.py

Converts the raw risk score breakdown into human-readable
"Because: ..." explanations for the investigator UI.

This is a PRESENTATION layer on top of risk_scorer.py — it does
NOT duplicate scoring logic, it only labels which signals fired.
Optional AI similarity / shared-neighbor signals (from ai/ and
analytics/ modules) can be passed in when available.
"""


def build_risk_explanation(breakdown: dict, ai_similarity_score: float = None,
                             shared_neighbors_count: int = None) -> list:
    """
    Args:
        breakdown: scoring_result["breakdown"] from RiskScorer.calculate_risk_score()
        ai_similarity_score: Optional Node2Vec similarity score (0-1) to a
                              known risky wallet, from ai/similarity_model.py
        shared_neighbors_count: Optional count of shared graph neighbors with
                                 a known risky wallet, from analytics/relationships.py

    Returns:
        list[str]: Human-readable reasons behind the risk score
    """
    reasons = []

    if breakdown.get("mixer_interaction", 0) > 0:
        reasons.append("Mixer interaction detected")

    if breakdown.get("known_scam", 0) > 0:
        reasons.append("Interaction with a known scam address")

    if breakdown.get("darknet_labels", 0) > 0:
        reasons.append("Connection to a darknet-labeled address")

    if breakdown.get("bridge_usage", 0) > 0:
        reasons.append("Bridge hopping across chains")

    if breakdown.get("rapid_chain_hopping", 0) > 0:
        reasons.append("Rapid, repeated fund transfers (chain hopping pattern)")

    if breakdown.get("high_frequency", 0) > 0:
        reasons.append("High transaction frequency")

    if breakdown.get("large_transactions", 0) > 0:
        reasons.append("Unusually large transaction amounts")

    if ai_similarity_score is not None and ai_similarity_score >= 0.6:
        reasons.append(f"AI similarity to known risky wallet ({round(ai_similarity_score * 100)}% match)")

    if shared_neighbors_count is not None and shared_neighbors_count > 0:
        reasons.append(f"Shares {shared_neighbors_count} graph neighbor(s) with flagged wallets")

    if not reasons:
        reasons.append("No significant risk indicators found")

    return reasons