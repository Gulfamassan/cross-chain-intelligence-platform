"""
backend/attribution/cross_chain_evidence.py

Sprint 14 Day 6 — Cross-Chain Graph Signal Improvement.

Provides a cross-chain relationship signal for wallet pairs that the
existing single-chain graph cannot resolve (Sprint 14 Day 5 finding).
Reuses EXISTING, already-tested logic — no new scoring rules invented:
  - bridge_detector.detect_bridge_transactions() to find wallet_1's
    bridge-out transactions on chain_1
  - heuristic_engine.rule_bridge_timing() / rule_amount_match() to
    correlate a bridge-out transaction with a receive transaction on
    wallet_2's chain_2

This does NOT modify graph/builder.py, node2vec, or the existing
calculate_relationship_score() — it is a new, opt-in signal only used
when two wallets are on different chains.
"""

import pandas as pd

from attribution.bridge_detector import bridge_detector
from attribution.heuristics import heuristic_engine


def calculate_cross_chain_evidence(wallet_1_csv: str, wallet_1: str, chain_1: str,
                                     wallet_2_csv: str, wallet_2: str, chain_2: str) -> dict:
    """
    Looks for bridge-timing/amount correlation between wallet_1's
    outgoing bridge activity (on chain_1) and wallet_2's incoming
    transactions (on chain_2).

    Returns a relationship-evidence record. "available" is explicit —
    False means the CSVs genuinely could not be read; True means a
    real (possibly 0) result was computed. This avoids conflating
    "we checked and found nothing" with "we couldn't check."
    """
    base = {
        "wallet_1": wallet_1,
        "chain_1": chain_1,
        "wallet_2": wallet_2,
        "chain_2": chain_2,
        "relationship_type": "cross_chain",
    }

    try:
        df_1 = pd.read_csv(wallet_1_csv)
        df_2 = pd.read_csv(wallet_2_csv)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {**base, "score": 0.0, "evidence": [], "matched_pairs": 0, "available": False}

    transactions_1 = df_1.to_dict("records")
    transactions_2 = df_2.to_dict("records")

    bridge_txs = bridge_detector.detect_bridge_transactions(transactions_1, chain_1)
    wallet_1_bridge_txs = [
        tx for tx in bridge_txs
        if str(tx.get("from_address", "")).lower() == wallet_1.lower()
    ]

    if not wallet_1_bridge_txs:
        return {**base, "score": 0.0, "evidence": [], "matched_pairs": 0, "available": True}

    wallet_2_key = wallet_2.lower()
    wallet_2_received_txs = [
        tx for tx in transactions_2
        if str(tx.get("to_address", "")).lower() == wallet_2_key
    ]

    if not wallet_2_received_txs:
        return {**base, "score": 0.0, "evidence": [], "matched_pairs": 0, "available": True}

    best_score = 0.0
    matched_pairs = 0
    evidence = []

    for bridge_tx in wallet_1_bridge_txs:
        for receive_tx in wallet_2_received_txs:
            timing_score = heuristic_engine.rule_bridge_timing(
                bridge_tx.get("timestamp"), receive_tx.get("timestamp")
            )
            amount_score = heuristic_engine.rule_amount_match(
                bridge_tx.get("value_eth"), receive_tx.get("value_eth")
            )
            pair_score = timing_score + amount_score

            if pair_score > 0:
                matched_pairs += 1
                if timing_score > 0 and "bridge_timing_match" not in evidence:
                    evidence.append("bridge_timing_match")
                if amount_score > 0 and "bridge_amount_match" not in evidence:
                    evidence.append("bridge_amount_match")

            pair_score_100 = min(100, (pair_score / 45) * 100)
            best_score = max(best_score, pair_score_100)

    return {
        **base,
        "score": round(best_score, 2),
        "evidence": evidence,
        "matched_pairs": matched_pairs,
        "available": True,
    }