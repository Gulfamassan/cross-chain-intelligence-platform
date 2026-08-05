"""
backend/entity_labeling/feature_mapper.py

Converts a WalletProfile (from features/wallet_profile.py) into the
flat feature dict that wallet_classifier.classify_wallet() expects.

⚠️ IMPORTANT: The field names below (transaction_count, average_amount,
etc.) are ASSUMED based on the project's naming pattern. Verify against
the actual WalletProfile.to_dict() output — if names differ, update the
.get() keys on the left side of each line below.
"""


def map_profile_to_classifier_features(wallet_profile_dict: dict, is_contract: bool = False) -> dict:
    """
    Args:
        wallet_profile_dict: Output of WalletProfile.to_dict()
        is_contract: Whether address is a deployed contract (from bytecode check)

    Returns:
        dict with keys expected by wallet_classifier.classify_wallet()
    """
    tx_count = wallet_profile_dict.get("transaction_count", 0)
    avg_amount = wallet_profile_dict.get("average_amount", 0)
    interaction_count = wallet_profile_dict.get("interaction_count",
                                                  wallet_profile_dict.get("unique_counterparties", 0))
    active_days = wallet_profile_dict.get("active_days", 0)

    total_sent = wallet_profile_dict.get("total_sent", 0)
    total_received = wallet_profile_dict.get("total_received", 0)
    in_out_ratio = (total_received / total_sent) if total_sent > 0 else 1.0

    bridge_usage = wallet_profile_dict.get("bridge_usage_count", 0)
    contract_calls = wallet_profile_dict.get("contract_call_count", 0)

    return {
        "tx_count": tx_count,
        "unique_counterparties": interaction_count,
        "avg_tx_value": avg_amount,
        "active_days": active_days,
        "in_out_ratio": in_out_ratio,
        "bridge_usage": bridge_usage,
        "contract_calls": contract_calls,
    }, is_contract