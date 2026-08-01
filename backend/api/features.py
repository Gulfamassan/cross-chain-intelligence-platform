"""
Features API Routes

Handles wallet feature extraction endpoints.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from features.extractor import feature_extractor

router = APIRouter()


class ExtractFeaturesRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    csv_path: str
    wallet_address: str
    chain: str


@router.post("/extract-features")
def extract_features(request: ExtractFeaturesRequest):
    """
    Extracts behavioral features for a wallet from its transaction
    CSV, and also saves them as a CSV file.

    Args:
        request (ExtractFeaturesRequest): CSV path, wallet address, chain

    Returns:
        dict: The wallet's full feature profile (JSON) and the saved CSV path

    Raises:
        HTTPException: If the CSV file doesn't exist (404) or an error occurs (500)
    """
    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    try:
        profile = feature_extractor.get_wallet_summary(
            request.csv_path, request.wallet_address, request.chain
        )
        csv_path = feature_extractor.save_features(profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Wallet Features Extracted Successfully",
        "features": profile.to_dict(),
        "csv_saved_at": csv_path
    }