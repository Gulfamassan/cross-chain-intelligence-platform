"""
backend/entity_labeling/feature_mapper.py

Converts a WalletProfile.to_dict() output into the flat feature dict
that wallet_classifier.classify_wallet() expects.

Field names below are verified against features/wallet_profile.py
(WalletProfile.to_dict()) — not guessed.

⚠️ NOTE: WalletProfile.bridge_usage and .smart_contract_usage are
currently hardcoded placeholders (always False) in wallet_profile.py's
__init__. Bridge-based classification will not trigger until that
module is completed with real detection logic.
"""


def map_profile_to_classifier_features(wallet_profile_dict: dict, is_contract: bool = False) -> dict:
    """
    Args:
        wallet_profile_dict: Output of WalletProfile.to_dict()
        is_contract: Whether address is a deployed contract

    Returns:
        dict with keys expected by wallet_classifier.classify_wallet()
    """
    tx_count = wallet_profile_dict.get("total_transactions", 0)
    avg_amount = wallet_profile_dict.get("average_transaction_value", 0)
    unique_contacts = wallet_profile_dict.get("total_unique_contacts", 0)
    active_days = wallet_profile_dict.get("active_days", 0)

    total_sent = wallet_profile_dict.get("total_sent_eth", 0)
    total_received = wallet_profile_dict.get("total_received_eth", 0)
    in_out_ratio = (total_received / total_sent) if total_sent > 0 else 1.0

    # NOTE: bridge_usage is a boolean placeholder in WalletProfile
    # (always False currently) — not yet a real usage count.
    bridge_usage_flag = wallet_profile_dict.get("bridge_usage", False)
    bridge_usage_count = 3 if bridge_usage_flag else 0  # maps bool -> the classifier's count-based rule

    contract_calls = 1 if wallet_profile_dict.get("smart_contract_usage", False) else 0

    return {
        "tx_count": tx_count,
        "unique_counterparties": unique_contacts,
        "avg_tx_value": avg_amount,
        "active_days": active_days,
        "in_out_ratio": in_out_ratio,
        "bridge_usage": bridge_usage_count,
        "contract_calls": contract_calls,
    }, is_contract