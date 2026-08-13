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
    {
        "case_id": 4,
        "wallet_a": "0xf92402bb795fd7cd08fb83839689db79099c8c9c",
        "chain_a": "ethereum",
        "wallet_b": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "chain_b": "polygon",
        "relationship_type": "Same entity (Binance)",
        "ground_truth": "Related",
        "basis": (
            "Wallet A is publicly labeled 'Binance Hot Wallet 1' and Wallet B "
            "is publicly labeled 'Binance Hot Wallet 20' — both confirmed via "
            "Etherscan/PolygonScan as Binance-owned. Verified cross-chain "
            "same-entity pair."
        ),
    },
{
        "case_id": 5,
        "wallet_a": "0x161ba15a5f335c9f06bb5bbb0a9ce14076fbb645",
        "chain_a": "ethereum",
        "wallet_b": "0x28c6c06298d514db089934071355e5743bf21d60",
        "chain_b": "ethereum",
        "relationship_type": "Same entity (Binance)",
        "ground_truth": "Related",
        "basis": (
            "Wallet A is publicly labeled 'Binance Hot Wallet 11' and Wallet B "
            "is publicly labeled 'Binance 14' — both confirmed via Etherscan "
            "as Binance-owned. Verified same-chain same-entity pair "
            "(chain changed from Arbitrum to Ethereum after confirming "
            "Wallet A's Arbitrum dataset was empty — 0x161ba15a... has "
            "very limited overall transaction history)."
        ),
    },
    {
        "case_id": 6,
        "wallet_a": "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        "chain_a": "ethereum",
        "wallet_b": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "chain_b": "polygon",
        "relationship_type": "Different entities (Coinbase vs Binance)",
        "ground_truth": "Unrelated",
        "basis": (
            "Wallet A is publicly labeled 'Coinbase 1' and Wallet B is "
            "publicly labeled 'Binance Hot Wallet 20' — both confirmed via "
            "Etherscan/PolygonScan, but belong to two different, competing "
            "exchanges. Verified cross-chain different-entity pair."
        ),
    },

    {
        "case_id": 7,
        "wallet_a": "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        "chain_a": "polygon",
        "wallet_b": "0xf92402bb795fd7cd08fb83839689db79099c8c9c",
        "chain_b": "arbitrum",
        "relationship_type": "Different entities (Coinbase vs Binance)",
        "ground_truth": "Unrelated",
        "basis": (
            "Wallet A is publicly labeled 'Coinbase 1' and Wallet B is "
            "publicly labeled 'Binance Hot Wallet 1' — verified different, "
            "competing exchanges. Verified cross-chain different-entity pair."
        ),
    },
]


def get_dataset() -> list:
    """Returns the controlled ground truth dataset for evaluation experiments."""
    return GROUND_TRUTH_DATASET