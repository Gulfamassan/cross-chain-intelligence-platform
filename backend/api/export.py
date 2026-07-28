"""
Export API Routes

Ye module wallet investigation data ko PDF, CSV, ya JSON
format mein export karne ke endpoints handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.graph import current_graph
from export.pdf_export import pdf_exporter
from export.csv_export import csv_exporter
from export.json_export import json_exporter
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


def _validate_request(wallet: str, csv_path: str):
    """
    Common validation jo teeno export endpoints use karte hain.
    """
    if not is_valid_ethereum_address(wallet):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Transactions CSV file not found")


@router.get("/export/pdf")
def export_pdf(wallet: str, csv_path: str, chain: str = "ethereum"):
    """
    Wallet ki investigation report PDF format mein export karta hai.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Transactions CSV ka path (query parameter)
        chain (str): Blockchain ka naam (query parameter, default "ethereum")

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
    Wallet ki summary data CSV format mein export karta hai.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Transactions CSV ka path (query parameter)
        chain (str): Blockchain ka naam (query parameter, default "ethereum")

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
    Wallet ki poori report JSON format mein export karta hai.

    Args:
        wallet (str): Wallet address (query parameter)
        csv_path (str): Transactions CSV ka path (query parameter)
        chain (str): Blockchain ka naam (query parameter, default "ethereum")

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