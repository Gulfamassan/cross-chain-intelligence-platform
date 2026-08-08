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

    Returns:
        dict: {
            "score": float (0-100),
            "source": "bridge_evidence" | "no_bridge_activity" | "unavailable",
            "matched_pairs": int,
        }
        "unavailable" only occurs if a CSV genuinely cannot be read.
        A wallet with no bridge activity is a real, checked answer (0.0),
        not a missing one.
    """
    try:
        df_1 = pd.read_csv(wallet_1_csv)
        df_2 = pd.read_csv(wallet_2_csv)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return {"score": None, "source": "unavailable", "matched_pairs": 0}

    transactions_1 = df_1.to_dict("records")
    transactions_2 = df_2.to_dict("records")

    # Step 1: wallet_1's transactions that touch a known bridge on chain_1
    bridge_txs = bridge_detector.detect_bridge_transactions(transactions_1, chain_1)
    wallet_1_bridge_txs = [
        tx for tx in bridge_txs
        if str(tx.get("from_address", "")).lower() == wallet_1.lower()
    ]

    if not wallet_1_bridge_txs:
        return {"score": 0.0, "source": "no_bridge_activity", "matched_pairs": 0}

    # Step 2: wallet_2's incoming transactions on chain_2
    wallet_2_key = wallet_2.lower()
    wallet_2_received_txs = [
        tx for tx in transactions_2
        if str(tx.get("to_address", "")).lower() == wallet_2_key
    ]

    if not wallet_2_received_txs:
        return {"score": 0.0, "source": "no_bridge_activity", "matched_pairs": 0}

    # Step 3: correlate every bridge-out tx with every receive tx using
    # EXISTING heuristic rules (timing + amount) — reused, not duplicated
    best_score = 0.0
    matched_pairs = 0

    for bridge_tx in wallet_1_bridge_txs:
        for receive_tx in wallet_2_received_txs:
            timing_score = heuristic_engine.rule_bridge_timing(
                bridge_tx.get("timestamp"), receive_tx.get("timestamp")
            )
            amount_score = heuristic_engine.rule_amount_match(
                bridge_tx.get("value_eth"), receive_tx.get("value_eth")
            )
            pair_score = timing_score + amount_score  # max 45 on heuristic_engine's own scale

            if pair_score > 0:
                matched_pairs += 1

            pair_score_100 = min(100, (pair_score / 45) * 100)
            best_score = max(best_score, pair_score_100)

    source = "bridge_evidence" if matched_pairs > 0 else "no_bridge_activity"

    return {
        "score": round(best_score, 2),
        "source": source,
        "matched_pairs": matched_pairs,
    }