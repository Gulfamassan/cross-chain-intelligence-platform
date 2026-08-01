"""
Attribution API Routes

Handles the main cross-chain wallet attribution analysis endpoint —
compares two wallets and determines whether they may belong to the
same entity.
"""

import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from features.extractor import feature_extractor
from attribution.similarity import similarity_engine
from attribution.bridge_detector import bridge_detector
from attribution.confidence import confidence_calculator
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class AttributionRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
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
    Analyzes two wallets to determine whether they may belong to the
    same entity, based on behavioral similarity and bridge activity.

    Args:
        request (AttributionRequest): Both wallets' addresses, chains, and CSV paths

    Returns:
        dict: Similarity, bridge detection, entity match, and confidence

    Raises:
        HTTPException: If an address is invalid (400) or a CSV file is missing (404)
    """
    if not is_valid_ethereum_address(request.wallet_1) or not is_valid_ethereum_address(request.wallet_2):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.wallet_1_csv) or not os.path.exists(request.wallet_2_csv):
        raise HTTPException(status_code=404, detail="Transaction CSV file(s) not found")

    profile_1 = feature_extractor.get_wallet_summary(
        request.wallet_1_csv, request.wallet_1, request.wallet_1_chain
    )
    profile_2 = feature_extractor.get_wallet_summary(
        request.wallet_2_csv, request.wallet_2, request.wallet_2_chain
    )

    similarity_result = similarity_engine.calculate_similarity_score(
        profile_1.to_dict(), profile_2.to_dict()
    )
    similarity_score = similarity_result["overall_similarity_score"]

    df_2 = pd.read_csv(request.wallet_2_csv)
    transactions_2 = df_2.to_dict("records")
    bridge_txs = bridge_detector.detect_bridge_transactions(transactions_2, request.wallet_2_chain)
    bridge_detected = len(bridge_txs) > 0
    bridge_name = bridge_txs[0]["bridge_name"] if bridge_detected else None

    combined_score = similarity_score * 100
    if bridge_detected:
        combined_score = min(100, combined_score + 20)

    entity_match = combined_score >= 50

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