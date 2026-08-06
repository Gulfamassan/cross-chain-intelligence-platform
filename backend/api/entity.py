"""
Entity Resolution API Routes

Exposes the Sprint 12 entity_labeling module (label_engine.resolve_entity)
as REST endpoints — classifies a wallet as Exchange/Bridge/Contract/
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
    Defines the expected request body for the /entity/resolve endpoint.
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


# ============================================================
# Day 3 addition — simplified classification endpoint
# (auto-resolves CSV path by convention, no csv_path needed)
# ============================================================

class EntityClassifyRequest(BaseModel):
    """
    Defines the expected request body for the /entity/classify endpoint.
    """
    wallet_address: str
    chain: str = "ethereum"


def _resolve_csv_path(wallet_address: str, chain: str) -> str:
    """
    Resolves the transaction CSV path by convention:
    datasets/{chain}/{wallet_address}.csv

    NOTE: This assumes the dataset folder naming convention observed
    in the project (datasets/ethereum/0x....csv). If the actual
    convention differs, this function needs updating.
    """
    candidate = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if os.path.exists(candidate):
        return candidate

    # fallback: try lowercase address, in case files are saved lowercase
    candidate_lower = os.path.join("datasets", chain.lower(), f"{wallet_address.lower()}.csv")
    if os.path.exists(candidate_lower):
        return candidate_lower

    return None


@router.post("/entity/classify")
def classify_wallet_endpoint(request: EntityClassifyRequest):
    """
    Simplified classification endpoint — resolves the wallet's dataset
    CSV automatically by convention, then classifies it via the same
    entity_labeling engine used by /entity/resolve.

    Args:
        request (EntityClassifyRequest): Wallet address and chain

    Returns:
        dict: wallet_address, chain, classification, confidence

    Raises:
        HTTPException: If the address is invalid (400) or no dataset
                        CSV is found for this wallet/chain (404)
    """
    if not is_valid_ethereum_address(request.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    csv_path = _resolve_csv_path(request.wallet_address, request.chain)
    if csv_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No transaction dataset found for this wallet on {request.chain}"
        )

    profile = feature_extractor.get_wallet_summary(csv_path, request.wallet_address, request.chain)
    result = resolve_entity(request.wallet_address, profile.to_dict(), is_contract=False)

    return {
        "wallet_address": result["address"],
        "chain": request.chain,
        "classification": result["label"],
        "confidence": result["confidence"],
    }