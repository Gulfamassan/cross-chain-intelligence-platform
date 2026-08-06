"""
Explainability API Routes

Combines Sprint 12's entity classification and explainable risk
scoring into a single "why" response — instead of a bare score,
the dashboard gets the score PLUS the reasons behind it.

ASSUMPTION: "decision" in the response is the risk level (High/Medium/
Low), since the spec's example is "Risk = 82 -> Why?". Entity
classification is included alongside as supporting context, not as
the primary decision. If a different meaning was intended, this
should be adjusted.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from features.extractor import feature_extractor
from entity_labeling.label_engine import resolve_entity
from risk.risk_engine import risk_engine
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class EntityExplainRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_address: str
    chain: str = "ethereum"


def _resolve_csv_path(wallet_address: str, chain: str) -> str:
    """
    Same dataset-path convention as /entity/classify:
    datasets/{chain}/{wallet_address}.csv
    """
    candidate = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if os.path.exists(candidate):
        return candidate

    candidate_lower = os.path.join("datasets", chain.lower(), f"{wallet_address.lower()}.csv")
    if os.path.exists(candidate_lower):
        return candidate_lower

    return None


@router.post("/entity/explain")
def explain_wallet_endpoint(request: EntityExplainRequest):
    """
    Returns a full explainable-AI breakdown for a wallet: entity
    classification, risk level, combined evidence, raw features, and
    a human-readable narrative — so the dashboard can show "Why?"
    instead of just a number.

    Args:
        request (EntityExplainRequest): Wallet address and chain

    Returns:
        dict: wallet_address, decision, confidence, evidence,
              features, explanation

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

    # Entity classification (reuses Sprint 12 Day 1-2 logic)
    entity_result = resolve_entity(request.wallet_address, profile.to_dict(), is_contract=False)

    # Explainable risk (reuses Sprint 12 Day 4 logic)
    risk_result = risk_engine.get_explainable_risk(csv_path, request.wallet_address, request.chain)

    # Combine evidence from both engines into one list
    combined_evidence = [f"Entity: {reason}" for reason in entity_result["reasons"]]
    combined_evidence += [f"Risk: {reason}" for reason in risk_result["explanation"]]

    explanation_sentence = (
        f"This wallet is classified as {entity_result['label']} "
        f"({entity_result['confidence_percent']} confidence) and carries "
        f"{risk_result['risk_level']} risk (score {risk_result['risk_score']}/100), "
        f"based on {len(combined_evidence)} supporting signal(s)."
    )

    return {
        "wallet_address": request.wallet_address,
        "decision": risk_result["risk_level"],
        "confidence": entity_result["confidence"],
        "evidence": combined_evidence,
        "features": profile.to_dict(),
        "explanation": explanation_sentence,
        "entity_classification": entity_result["label"],
        "risk_score": risk_result["risk_score"],
    }