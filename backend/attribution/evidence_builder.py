"""
backend/attribution/evidence_builder.py

Converts raw heuristic + similarity scores into a human-readable
evidence list for the investigator UI.

This is a PRESENTATION layer on top of existing engines
(heuristics.py, similarity.py, confidence.py) — it does NOT
duplicate their scoring logic, it only labels what already fired.
"""


def build_evidence_list(heuristic_breakdown: dict, similarity_result: dict, graph_distance: int = None) -> list:
    """
    Args:
        heuristic_breakdown: Output of HeuristicEngine.calculate_total_score()
        similarity_result: Output of similarity_engine.calculate_similarity_score()
        graph_distance: Optional shortest-path hop count between the two
                         wallets (from analytics/path_analysis.py), if available

    Returns:
        list[str]: Human-readable evidence bullets
    """
    evidence = []

    if heuristic_breakdown.get("bridge_timing_score", 0) > 0:
        evidence.append("Same bridge — transaction timing matches within window")

    if heuristic_breakdown.get("amount_match_score", 0) > 0:
        evidence.append("Matching transaction amount across chains")

    if heuristic_breakdown.get("gas_pattern_score", 0) > 0:
        evidence.append("Similar gas price fingerprint")

    if heuristic_breakdown.get("activity_timing_score", 0) > 0:
        evidence.append("Same active-hours timing pattern")

    if heuristic_breakdown.get("exchange_deposit_score", 0) > 0:
        evidence.append("Deposited to the same exchange")

    similarity_score = similarity_result.get("overall_similarity_score", 0)
    if similarity_score >= 0.6:
        evidence.append(f"Similar behavioural profile ({round(similarity_score * 100)}% match)")

    if graph_distance is not None:
        hop_word = "hop" if graph_distance == 1 else "hops"
        evidence.append(f"Graph distance: {graph_distance} {hop_word}")

    if not evidence:
        evidence.append("No strong supporting evidence found")

    return evidence