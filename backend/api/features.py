"""
Features API Routes

Ye module wallet feature extraction se related endpoint handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from features.extractor import feature_extractor

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class ExtractFeaturesRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    csv_path: str
    wallet_address: str
    chain: str


@router.post("/extract-features")
def extract_features(request: ExtractFeaturesRequest):
    """
    Diye gaye wallet transactions CSV se features nikalta hai,
    aur unhe CSV mein bhi save karta hai.

    Args:
        request (ExtractFeaturesRequest): Transactions CSV ka path, wallet address, chain

    Returns:
        dict: Wallet ka poora feature profile (JSON), aur saved CSV path

    Raises:
        HTTPException: Agar CSV file exist nahi karti (404) ya koi error aaye (500)
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