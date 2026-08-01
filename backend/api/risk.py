"""
Risk API Routes

Handles the wallet risk analysis endpoint.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from risk.risk_engine import risk_engine
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class RiskAnalyzeRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/risk/analyze")
def analyze_risk(request: RiskAnalyzeRequest):
    """
    Performs a complete risk analysis for the given wallet.

    Args:
        request (RiskAnalyzeRequest): Wallet, CSV path, chain

    Returns:
        dict: Risk score, level, and a full breakdown

    Raises:
        HTTPException: If the address is invalid (400) or the CSV is missing (404)
    """
    if not is_valid_ethereum_address(request.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    result = risk_engine.analyze(request.csv_path, request.wallet, request.chain)

    return result