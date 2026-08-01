"""
Export API Routes

Handles exporting wallet investigation data in PDF, CSV, or
JSON format.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.graph import current_graph
from export.pdf_export import pdf_exporter
from export.csv_export import csv_exporter
from export.json_export import json_exporter
from utils.validators import is_valid_ethereum_address

router = APIRouter()


def _validate_request(wallet: str, csv_path: str):
    """
    Shared validation used by all three export endpoints.
    """
    if not is_valid_ethereum_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")


@router.get("/export/pdf")
def export_pdf(wallet: str, csv_path: str, chain: str = "ethereum"):
    """
    Exports a wallet's investigation report in PDF format.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Path to the transactions CSV (query parameter)
        chain (str): Blockchain name (query parameter, default "ethereum")

    Returns:
        FileResponse: PDF file
    """
    _validate_request(wallet, csv_path)

    file_path = pdf_exporter.export(current_graph.graph, csv_path, wallet, chain)

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{wallet}_report.pdf",
    )


@router.get("/export/csv")
def export_csv(wallet: str, csv_path: str, chain: str = "ethereum"):
    """
    Exports a wallet's summary data in CSV format.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Path to the transactions CSV (query parameter)
        chain (str): Blockchain name (query parameter, default "ethereum")

    Returns:
        FileResponse: CSV file
    """
    _validate_request(wallet, csv_path)

    file_path = csv_exporter.export(current_graph.graph, csv_path, wallet, chain)

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=f"{wallet}_summary.csv",
    )


@router.get("/export/json")
def export_json(wallet: str, csv_path: str, chain: str = "ethereum"):
    """
    Exports a wallet's complete report in JSON format.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Path to the transactions CSV (query parameter)
        chain (str): Blockchain name (query parameter, default "ethereum")

    Returns:
        FileResponse: JSON file
    """
    _validate_request(wallet, csv_path)

    file_path = json_exporter.export(current_graph.graph, csv_path, wallet, chain)

    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=f"{wallet}_report.json",
    )