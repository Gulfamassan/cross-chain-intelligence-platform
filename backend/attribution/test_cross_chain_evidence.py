"""
backend/attribution/test_cross_chain_evidence.py

Sprint 14 Day 6, Step 10 — Unit tests for cross-chain relationship
signal integration. Run with: pytest attribution/test_cross_chain_evidence.py
(or: python -m pytest attribution/test_cross_chain_evidence.py)
"""

import pytest
from hybrid.scoring import hybrid_scorer
from graph.builder import TransactionGraph

ETH_CSV = "datasets/ethereum/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045.csv"
POLYGON_CSV = "datasets/polygon/0xF977814e90dA44bFA03b6295A0616a897441aceC.csv"
WALLET_ETH = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
WALLET_POLYGON = "0xF977814e90dA44bFA03b6295A0616a897441aceC"


def build_graph(csv_path):
    tg = TransactionGraph()
    tg.load_csv(csv_path)
    tg.build_graph()
    return tg.graph


def test_same_chain_behaves_as_before():
    """Same-chain pairs must use the graph path unchanged, source='graph'."""
    graph = build_graph(POLYGON_CSV)
    result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        graph, WALLET_POLYGON, "polygon", POLYGON_CSV,
        WALLET_POLYGON, "polygon", POLYGON_CSV
    )
    assert result["source"] == "graph"
    assert result["available"] is True


def test_cross_chain_returns_evidence_structure():
    """Cross-chain pairs must return the full evidence structure, not a bare 0."""
    graph = build_graph(POLYGON_CSV)
    result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        graph, WALLET_ETH, "ethereum", ETH_CSV,
        WALLET_POLYGON, "polygon", POLYGON_CSV
    )
    assert result["source"] in ("bridge_evidence", "no_bridge_activity")
    assert result["available"] is True
    assert isinstance(result["evidence"], list)
    assert isinstance(result["relationship_score"], float)


def test_missing_bridge_does_not_become_strong_relationship():
    """
    If no bridge evidence is found, the score must stay low (0.0) —
    absence of evidence must not be inflated into a strong relationship.
    """
    graph = build_graph(POLYGON_CSV)
    result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        graph, WALLET_ETH, "ethereum", ETH_CSV,
        WALLET_POLYGON, "polygon", POLYGON_CSV
    )
    if result["source"] == "no_bridge_activity":
        assert result["relationship_score"] == 0.0