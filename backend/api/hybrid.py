"""
Hybrid Attribution API Routes

Ye module Rule-Based aur AI-Based (Node2Vec) attribution ko combine
karke ek final hybrid confidence score aur explanation deta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine
from hybrid.confidence import hybrid_confidence_classifier
from hybrid.evaluator import explanation_engine
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class HybridAnalyzeRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet_1: str
    wallet_2: str
    wallet_1_csv: str
    wallet_2_csv: str
    chain: str = "ethereum"


@router.post("/hybrid/analyze")
def analyze_hybrid_attribution(request: HybridAnalyzeRequest):
    """
    Do wallets ko Rule-Based aur AI-Based signals combine karke
    analyze karta hai, aur ek explainable final confidence deta hai.

    Args:
        request (HybridAnalyzeRequest): Dono wallets, CSV paths, chain

    Returns:
        dict: Har score, final confidence, classification, aur explanation

    Raises:
        HTTPException: Agar address invalid ho (400) ya CSV na mile (404)
    """
    if not is_valid_ethereum_address(request.wallet_1) or not is_valid_ethereum_address(request.wallet_2):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.wallet_1_csv) or not os.path.exists(request.wallet_2_csv):
        raise HTTPException(status_code=404, detail="Transaction CSV file(s) not found")

    # Step 1: Rule-based score nikalte hain
    rule_result = hybrid_scorer.calculate_rule_score(
        request.wallet_1_csv, request.wallet_2_csv,
        request.wallet_1, request.wallet_2, request.chain
    )

    # Step 2: AI embedding score nikalte hain
    embedding_score = hybrid_scorer.calculate_embedding_score(request.wallet_1, request.wallet_2)

    # Step 3: Relationship score nikalte hain (agar graph bana ho)
    relationship_result = hybrid_scorer.calculate_relationship_score(
        current_graph.graph, request.wallet_1, request.wallet_2
    )

    # Step 4: Risk score (abhi placeholder)
    risk_score = hybrid_scorer.get_risk_score()

    # Step 5: Fusion Engine se sab kuch combine karte hain
    fusion_result = fusion_engine.combine_scores(
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        risk_score=risk_score,
    )

    # Step 6: Classification label nikalte hain
    classification = hybrid_confidence_classifier.classify(fusion_result["final_confidence"])

    # Step 7: Explanation banate hain
    explanation = explanation_engine.generate_explanation(
        bridge_detected=rule_result["bridge_detected"],
        bridge_name=rule_result["bridge_name"],
        rule_score=rule_result["rule_score"],
        embedding_score=embedding_score,
        relationship_score=relationship_result["relationship_score"],
        common_neighbors_count=relationship_result["common_neighbors_count"],
    )

    return {
        "wallet_1": request.wallet_1,
        "wallet_2": request.wallet_2,
        "rule_score": rule_result["rule_score"],
        "embedding_score": embedding_score,
        "relationship_score": relationship_result["relationship_score"],
        "risk_score": risk_score,
        "confidence": fusion_result["final_confidence"],
        "classification": classification,
        "explanation": explanation,
    }