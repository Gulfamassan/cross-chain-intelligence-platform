"""
Intelligence API Routes

Ye module ek wallet ki complete investigation report generate
karne ka endpoint handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from intelligence.intelligence_engine import intelligence_engine
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class IntelligenceReportRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/intelligence/report")
def generate_intelligence_report(request: IntelligenceReportRequest):
    """
    Diye gaye wallet ki complete investigation report banata hai —
    graph data, features, cluster, aur summary sab ek jagah.

    Args:
        request (IntelligenceReportRequest): Wallet, CSV path, aur chain

    Returns:
        dict: Complete investigation report

    Raises:
        HTTPException: Agar address invalid ho (400) ya CSV na mile (404)
    """
    if not is_valid_ethereum_address(request.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    report = intelligence_engine.generate_report(
        current_graph.graph, request.csv_path, request.wallet, request.chain
    )

    return report