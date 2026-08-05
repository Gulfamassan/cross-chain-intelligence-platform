"""
backend/entity_labeling/label_engine.py
Entry point: known-address lookup first, heuristic classifier fallback.
"""

from .label_database import lookup_known_address
from .wallet_classifier import classify_wallet, ClassificationResult
from .feature_mapper import map_profile_to_classifier_features


def resolve_entity(address: str, wallet_profile_dict: dict, is_contract: bool = False) -> dict:
    """
    Args:
        address: Wallet address string
        wallet_profile_dict: Output of WalletProfile.to_dict() (real pipeline data)
        is_contract: Whether address is a deployed contract
    """
    known = lookup_known_address(address)
    if known:
        return {
            "address": address,
            "label": known["label"],
            "confidence": 0.99,
            "reasons": [f"Matched known entity: {known['name']}"],
            "source": "known_list",
        }

    mapped_features, is_contract = map_profile_to_classifier_features(wallet_profile_dict, is_contract)
    result: ClassificationResult = classify_wallet(mapped_features, is_contract=is_contract)

    return {
        "address": address,
        "label": result.label,
        "confidence": result.confidence,
        "confidence_percent": f"{round(result.confidence * 100)}%",
        "reasons": result.reasons,
        "source": "heuristic",
    }