"""
Report API Routes

Handles generating a wallet's PDF investigation report.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.graph import current_graph
from reports.pdf_generator import pdf_generator
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class ReportGenerateRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/report/generate")
def generate_report(request: ReportGenerateRequest):
    """
    Generates a PDF investigation report for the given wallet.

    Args:
        request (ReportGenerateRequest): Wallet, CSV path, chain

    Returns:
        FileResponse: The generated PDF file (downloadable)

    Raises:
        HTTPException: If the address is invalid (400) or the CSV is missing (404)
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