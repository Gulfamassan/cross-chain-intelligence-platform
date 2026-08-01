"""
Intelligence API Routes

Handles generating a wallet's complete investigation report.
"""

import os
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from intelligence.intelligence_engine import intelligence_engine
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class IntelligenceReportRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


def sanitize_for_json(data):
    """
    Recursively replaces any hidden NaN or Infinity values in a
    dictionary/list with None, so that JSON serialization never crashes.

    Args:
        data: A dictionary, list, or any other value

    Returns:
        The same structure, with any NaN/Infinity values converted to None
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
    Generates a wallet's complete investigation report — graph data,
    features, cluster, and summary, all in one response.

    Args:
        request (IntelligenceReportRequest): Wallet, CSV path, and chain

    Returns:
        dict: The complete investigation report

    Raises:
        HTTPException: If the address is invalid (400) or the CSV is missing (404)
    """
    if not is_valid_ethereum_address(request.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    report = intelligence_engine.generate_report(
        current_graph.graph, request.csv_path, request.wallet, request.chain
    )

    return sanitize_for_json(report)