"""
Intelligence API Routes

Ye module ek wallet ki complete investigation report generate
karne ka endpoint handle karta hai.
"""

import os
import math
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


def sanitize_for_json(data):
    """
    Kisi bhi dictionary/list mein chhupi hui NaN ya Infinity values ko
    None se replace karta hai, taake JSON serialization crash na ho.

    Args:
        data: Dictionary, list, ya koi bhi value

    Returns:
        Wahi structure, lekin NaN/Infinity values None ban chuki hongi
    """
    if isinstance(data, dict):
        return {key: sanitize_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data


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

    # Poori report ko NaN-safe banate hain, taake JSON response kabhi crash na ho
    return sanitize_for_json(report)