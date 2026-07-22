"""
Attribution API Routes

Ye module cross-chain wallet attribution analysis ka main endpoint
handle karta hai — do wallets ko compare karke batata hai ke kya
ye same entity ho sakte hain.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from features.extractor import feature_extractor
from attribution.similarity import similarity_engine
from attribution.bridge_detector import bridge_detector
from attribution.confidence import confidence_calculator
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class AttributionRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet_1: str
    wallet_2: str
    wallet_1_csv: str
    wallet_2_csv: str
    wallet_1_chain: str = "ethereum"
    wallet_2_chain: str = "ethereum"


@router.post("/attribution/analyze")
def analyze_attribution(request: AttributionRequest):
    """
    Do wallets ko analyze karta hai — dekhta hai kya ye same entity
    ho sakte hain, based on behavior similarity aur bridge activity.

    Args:
        request (AttributionRequest): Dono wallets ka address, chain, aur CSV path

    Returns:
        dict: Similarity, bridge detection, entity match, aur confidence

    Raises:
        HTTPException: Agar address invalid ho (400) ya CSV na mile (404)
    """
    if not is_valid_ethereum_address(request.wallet_1) or not is_valid_ethereum_address(request.wallet_2):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.wallet_1_csv) or not os.path.exists(request.wallet_2_csv):
        raise HTTPException(status_code=404, detail="Transaction CSV file(s) not found")

    # Dono wallets ke features nikalte hain
    profile_1 = feature_extractor.get_wallet_summary(
        request.wallet_1_csv, request.wallet_1, request.wallet_1_chain
    )
    profile_2 = feature_extractor.get_wallet_summary(
        request.wallet_2_csv, request.wallet_2, request.wallet_2_chain
    )

    # Similarity nikalte hain
    similarity_result = similarity_engine.calculate_similarity_score(
        profile_1.to_dict(), profile_2.to_dict()
    )
    similarity_score = similarity_result["overall_similarity_score"]

    # Wallet 2 ki transactions mein bridge activity check karte hain
    import pandas as pd
    df_2 = pd.read_csv(request.wallet_2_csv)
    transactions_2 = df_2.to_dict("records")
    bridge_txs = bridge_detector.detect_bridge_transactions(transactions_2, request.wallet_2_chain)
    bridge_detected = len(bridge_txs) > 0
    bridge_name = bridge_txs[0]["bridge_name"] if bridge_detected else None

    # Combined score: similarity (0-100) + bridge bonus (agar detect ho to +20)
    combined_score = similarity_score * 100
    if bridge_detected:
        combined_score = min(100, combined_score + 20)

    entity_match = combined_score >= 50

    # Confidence label nikalte hain
    confidence_summary = confidence_calculator.get_confidence_summary(combined_score)

    return {
        "wallet_1": request.wallet_1,
        "wallet_2": request.wallet_2,
        "similarity": round(similarity_score, 4),
        "bridge_detected": bridge_detected,
        "bridge_name": bridge_name,
        "entity_match": entity_match,
        "combined_score": round(combined_score, 2),
        "confidence": confidence_summary["confidence_label"],
    }