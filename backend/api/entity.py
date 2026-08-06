"""
Entity Resolution API Routes

Exposes the Sprint 12 entity_labeling module (label_engine.resolve_entity)
as a REST endpoint — classifies a wallet as Exchange/Bridge/Contract/
Personal/Unknown with confidence and evidence.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from features.extractor import feature_extractor
from entity_labeling.label_engine import resolve_entity
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class EntityResolveRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_address: str
    csv_path: str
    chain: str = "ethereum"


@router.post("/entity/resolve")
def resolve_entity_endpoint(request: EntityResolveRequest):
    """
    Classifies a wallet's entity type (Exchange/Bridge/Contract/Personal/
    Unknown) using the known-address list first, then the rule-based
    heuristic classifier as a fallback.

    Args:
        request (EntityResolveRequest): Wallet address, its transaction
                                          CSV path, and chain

    Returns:
        dict: wallet_address, label, confidence, evidence

    Raises:
        HTTPException: If the address is invalid (400) or the CSV file
                        is missing (404)
    """
    if not is_valid_ethereum_address(request.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="Transaction CSV file not found")

    profile = feature_extractor.get_wallet_summary(
        request.csv_path, request.wallet_address, request.chain
    )

    # NOTE: Contract-bytecode detection is not wired yet — defaulting to
    # False. If a contract-check function exists elsewhere in the
    # pipeline, this should be replaced rather than left as a guess.
    is_contract = False

    result = resolve_entity(request.wallet_address, profile.to_dict(), is_contract=is_contract)

    return {
        "wallet_address": result["address"],
        "label": result["label"],
        "confidence": result["confidence"],
        "confidence_percent": result.get("confidence_percent"),
        "source": result["source"],
        "evidence": result["reasons"],
    }