"""
Hybrid Attribution API Routes

Combines Rule-Based and AI-Based (Node2Vec) attribution into a
final hybrid confidence score, explanation, and evidence chain.
Supports wallets on two different chains for genuine cross-chain
attribution testing.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine
from hybrid.confidence import hybrid_confidence_classifier
from hybrid.evaluator import explanation_engine
from intelligence.evidence import evidence_builder
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class HybridAnalyzeRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    Each wallet can have its own chain specified.
    """
    wallet_1: str
    wallet_2: str
    wallet_1_csv: str
    wallet_2_csv: str
    wallet_1_chain: str = "ethereum"
    wallet_2_chain: str = "ethereum"


@router.post("/hybrid/analyze")
def analyze_hybrid_attribution(request: HybridAnalyzeRequest):
    """
    Analyzes two wallets by combining Rule-Based and AI-Based signals,
    and returns an explainable final confidence score, explanation,
    and evidence chain.

    Sprint 14 Day 6: for cross-chain pairs, the relationship score now
    uses bridge-timing/amount evidence (attribution/cross_chain_evidence.py)
    instead of a structural 0 when the graph has no cross-chain edges.
    Same-chain pairs behave exactly as before (unchanged graph path).

    Args:
        request (HybridAnalyzeRequest): Both wallets, CSV paths, and their chains

    Returns:
        dict: Each score, final confidence, classification, explanation,
              evidence, and cross_chain_evidence (when applicable)

    Raises:
        HTTPException: If an address is invalid (400) or a CSV file is missing (404)
    """
    if not is_valid_ethereum_address(request.wallet_1) or not is_valid_ethereum_address(request.wallet_2):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.wallet_1_csv) or not os.path.exists(request.wallet_2_csv):
        raise HTTPException(status_code=404, detail="Transaction CSV file(s) not found")

    cross_chain_pair = request.wallet_1_chain.lower() != request.wallet_2_chain.lower()

    rule_result = hybrid_scorer.calculate_rule_score(
        request.wallet_1_csv, request.wallet_2_csv,
        request.wallet_1, request.wallet_2, request.wallet_2_chain
    )

    embedding_score = hybrid_scorer.calculate_embedding_score(request.wallet_1, request.wallet_2)

    # Sprint 14 Day 6: cross-chain-aware relationship scoring.
    # Same-chain pairs use the existing graph path unchanged (source="graph").
    # Cross-chain pairs use bridge-timing/amount evidence instead of a
    # structural 0, with explicit availability/evidence reported.
    relationship_result = hybrid_scorer.calculate_relationship_score_cross_chain_aware(
        current_graph.graph,
        request.wallet_1, request.wallet_1_chain, request.wallet_1_csv,
        request.wallet_2, request.wallet_2_chain, request.wallet_2_csv,
    )

    risk_score = hybrid_scorer.get_risk_score(
        request.wallet_2_csv, request.wallet_2, request.wallet_2_chain
    )

    fusion_result = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        risk_score=risk_score,
    )

    classification = hybrid_confidence_classifier.classify(fusion_result["final_confidence"])

    explanation = explanation_engine.generate_explanation(
        bridge_detected=rule_result["bridge_detected"],
        bridge_name=rule_result["bridge_name"],
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        common_neighbors_count=relationship_result["common_neighbors_count"],
    )

    evidence_chain = evidence_builder.build_attribution_evidence(
        bridge_detected=rule_result["bridge_detected"],
        bridge_name=rule_result["bridge_name"],
        amount_match=rule_result["rule_score"] >= 70,
        timing_match=rule_result["bridge_detected"],
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        common_neighbors_count=relationship_result["common_neighbors_count"],
        final_confidence=fusion_result["final_confidence"],
    )

    # Sprint 14 Day 6, Step 12: expose cross-chain evidence explicitly
    # for the GUI, only when the pair is actually cross-chain.
    cross_chain_evidence = None
    if cross_chain_pair:
        cross_chain_evidence = {
            "available": relationship_result.get("available", False),
            "score": relationship_result["relationship_score"],
            "source": relationship_result.get("source"),
            "bridge_evidence_detected": relationship_result.get("source") == "bridge_evidence",
            "matched_bridge_pairs": relationship_result.get("matched_bridge_pairs", 0),
        }

    return {
        "wallet_1": request.wallet_1,
        "wallet_1_chain": request.wallet_1_chain,
        "wallet_2": request.wallet_2,
        "wallet_2_chain": request.wallet_2_chain,
        "cross_chain_pair": cross_chain_pair,
        "rule_score": rule_result["rule_score"],
        "embedding_score": embedding_score,
        "relationship_score": relationship_result["relationship_score"],
        "relationship_note": (
            "Cross-chain relationship uses bridge-timing/amount evidence, not graph structure"
            if cross_chain_pair else None
        ),
        "cross_chain_evidence": cross_chain_evidence,
        "risk_score": risk_score,
        "confidence": fusion_result["final_confidence"],
        "classification": classification,
        "explanation": explanation,
        "evidence": evidence_chain,
    }