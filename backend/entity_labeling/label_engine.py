"""
backend/entity_labeling/label_engine.py
Entry point: known-address lookup first, heuristic classifier fallback.
"""

from .label_database import lookup_known_address
from .wallet_classifier import classify_wallet, ClassificationResult


def resolve_entity(address: str, features: dict, is_contract: bool = False) -> dict:
    known = lookup_known_address(address)
    if known:
        return {
            "address": address,
            "label": known["label"],
            "confidence": 0.99,
            "reasons": [f"Matched known entity: {known['name']}"],
            "source": "known_list",
        }

    result: ClassificationResult = classify_wallet(features, is_contract=is_contract)
    return {
        "address": address,
        "label": result.label,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "source": "heuristic",
    }