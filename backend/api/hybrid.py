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

    Args:
        request (HybridAnalyzeRequest): Both wallets, CSV paths, and their chains

    Returns:
        dict: Each score, final confidence, classification, explanation, evidence

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

    relationship_result = hybrid_scorer.calculate_relationship_score(
        current_graph.graph, request.wallet_1, request.wallet_2
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
            "Cross-chain graph analysis not yet available — relationship score reflects single-chain graph only"
            if cross_chain_pair else None
        ),
        "risk_score": risk_score,
        "confidence": fusion_result["final_confidence"],
        "classification": classification,
        "explanation": explanation,
        "evidence": evidence_chain,
    }