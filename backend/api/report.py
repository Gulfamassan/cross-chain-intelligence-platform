"""
Report API Routes

Ye module wallet ki PDF investigation report generate karne
ka endpoint handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.graph import current_graph
from reports.pdf_generator import pdf_generator
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class ReportGenerateRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/report/generate")
def generate_report(request: ReportGenerateRequest):
    """
    Diye gaye wallet ki PDF investigation report generate karta hai.

    Args:
        request (ReportGenerateRequest): Wallet, CSV path, chain

    Returns:
        FileResponse: Generated PDF file (download hoga)

    Raises:
        HTTPException: Agar address invalid ho (400) ya CSV na mile (404)
    """
    if not is_valid_ethereum_address(request.wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")

    pdf_path = pdf_generator.generate_pdf_report(
        current_graph.graph, request.csv_path, request.wallet, request.chain
    )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{request.wallet}_investigation_report.pdf",
    )