"""
Risk API Routes

Ye module wallet ki risk analysis ka endpoint handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from risk.risk_engine import risk_engine
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class RiskAnalyzeRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/risk/analyze")
def analyze_risk(request: RiskAnalyzeRequest):
    """
    Diye gaye wallet ki poori risk analysis karta hai.

    Args:
        request (RiskAnalyzeRequest): Wallet, CSV path, chain

    Returns:
        dict: Risk score, level, aur poora breakdown

    Raises:
        HTTPException: Agar address invalid ho (400) ya CSV na mile (404)
    """
    if not is_valid_ethereum_address(request.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    result = risk_engine.analyze(request.csv_path, request.wallet, request.chain)

    return result