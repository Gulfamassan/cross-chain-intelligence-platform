"""
backend/evaluation/ground_truth.py

Sprint 14 Day 1 — Controlled Ground Truth Dataset for Attribution Evaluation.

Each test case pairs two wallets with a VERIFIED relationship status —
not inferred from behavior, but confirmed from an authoritative source
(public block explorer labels). This avoids the trap of labeling
"similar behavior" as "same owner" without real evidence.

Sources verified via block explorers (Etherscan/BscScan/PolygonScan),
August 2026.
"""

GROUND_TRUTH_DATASET = [
    {
        "case_id": 1,
        "wallet_a": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chain_a": "ethereum",
        "wallet_b": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "chain_b": "polygon",
        "relationship_type": "None known",
        "ground_truth": "Unrelated",
        "basis": (
            "Wallet A is an unlabeled address classified as a Personal Wallet "
            "by the system's entity resolution engine (Sprint 12). Wallet B is "
            "a publicly-verified Binance Hot Wallet 20, confirmed via "
            "Etherscan/BscScan/PolygonScan explorer labels. No structural or "
            "known-entity evidence links the two."
        ),
    },
    {
        "case_id": 2,
        "wallet_a": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        "chain_a": "polygon",
        "wallet_b": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "chain_b": "polygon",
        "relationship_type": "None known",
        "ground_truth": "Unrelated",
        "basis": (
            "Same pair as Case 1, tested same-chain instead of cross-chain, "
            "to check whether same-chain vs cross-chain comparison changes "
            "the system's output for a known-unrelated pair."
        ),
    },
    {
        "case_id": 3,
        "wallet_a": "0x28c6c06298d514db089934071355e5743bf21d60",
        "chain_a": "ethereum",
        "wallet_b": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "chain_b": "polygon",
        "relationship_type": "Same entity (Binance)",
        "ground_truth": "Related",
        "basis": (
            "Wallet A is publicly labeled 'Binance 14' (Ethereum) and Wallet B "
            "is publicly labeled 'Binance Hot Wallet 20' (Polygon) — both "
            "confirmed via Etherscan/PolygonScan explorer labels as "
            "Binance-owned exchange wallets. This is a verified same-entity, "
            "cross-chain pair, not inferred from behavioral similarity."
        ),
    },
]


def get_dataset() -> list:
    """Returns the controlled ground truth dataset for evaluation experiments."""
    return GROUND_TRUTH_DATASET