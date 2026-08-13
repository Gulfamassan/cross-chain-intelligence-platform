"""
backend/attribution/entity_agreement.py

Sprint 15 — Entity Classification Agreement Signal.

Checks whether two wallets' independently-computed entity
classifications (from entity_labeling.resolve_entity(), Sprint 12)
agree with each other. This is NOT a new classifier — it reuses the
existing, already-tested classification engine and only compares
its outputs.

Three states (Sprint 15 Day 1 finding: True/False is insufficient —
UNKNOWN must be distinct from NO_MATCH):
  - MATCH       both wallets confidently classified as the SAME entity type
  - NO_MATCH    both wallets confidently classified as DIFFERENT entity types
  - UNKNOWN     either wallet's classification is "Unknown", OR either
                wallet's confidence is below the trust threshold —
                absence of evidence, not evidence of absence

Sprint 15 Day 1 finding: the original threshold (0.5) was too
permissive — a wallet classified "Personal Wallet" at only 60%
confidence (the heuristic classifier's default confidence for that
rule) was being treated as confidently known, when 60% is closer to
"weak guess" than "confident classification." Raised to 0.75 so that
only known-list matches (99%) and strong heuristic matches trigger
MATCH/NO_MATCH; everything else is honestly reported as UNKNOWN.

⚠️ This module still does NOT assign a fusion weight. See
evaluation/run_entity_agreement_experiment.py for validation against
ground truth before any fusion.py wiring is considered.
"""

from entity_labeling.label_engine import resolve_entity

# Sprint 15 Day 2: raised from 0.5 -> 0.75 based on Day 1 finding.
# Below this confidence, a classification is not trusted enough to
# use as agreement evidence — treated as UNKNOWN instead.
MIN_CONFIDENCE_FOR_AGREEMENT = 0.75


def calculate_entity_agreement(wallet_1: str, wallet_1_profile: dict, wallet_1_is_contract: bool,
                                 wallet_2: str, wallet_2_profile: dict, wallet_2_is_contract: bool) -> dict:
    """
    Args:
        wallet_1, wallet_2: addresses
        wallet_1_profile, wallet_2_profile: WalletProfile.to_dict() for each
        wallet_1_is_contract, wallet_2_is_contract: contract-check flags
                                                     (currently always False
                                                     pipeline-wide — known
                                                     limitation, see README)

    Returns:
        dict: {
            "wallet_1_label": str, "wallet_1_confidence": float,
            "wallet_2_label": str, "wallet_2_confidence": float,
            "state": "MATCH" | "NO_MATCH" | "UNKNOWN",
            "score": float (0-100) | None,
        }
        score is None when state == "UNKNOWN" — this is a MISSING
        signal, not a real 0, consistent with the Day 6 "available"
        pattern used for cross-chain evidence.
    """
    result_1 = resolve_entity(wallet_1, wallet_1_profile, is_contract=wallet_1_is_contract)
    result_2 = resolve_entity(wallet_2, wallet_2_profile, is_contract=wallet_2_is_contract)

    label_1, conf_1 = result_1["label"], result_1["confidence"]
    label_2, conf_2 = result_2["label"], result_2["confidence"]

    both_confident = conf_1 >= MIN_CONFIDENCE_FOR_AGREEMENT and conf_2 >= MIN_CONFIDENCE_FOR_AGREEMENT
    either_unknown = label_1 == "Unknown" or label_2 == "Unknown"

    if not both_confident or either_unknown:
        return {
            "wallet_1_label": label_1, "wallet_1_confidence": conf_1,
            "wallet_2_label": label_2, "wallet_2_confidence": conf_2,
            "state": "UNKNOWN",
            "score": None,
        }

    if label_1 == label_2:
        score = round(min(conf_1, conf_2) * 100, 2)
        return {
            "wallet_1_label": label_1, "wallet_1_confidence": conf_1,
            "wallet_2_label": label_2, "wallet_2_confidence": conf_2,
            "state": "MATCH",
            "score": score,
        }

    return {
        "wallet_1_label": label_1, "wallet_1_confidence": conf_1,
        "wallet_2_label": label_2, "wallet_2_confidence": conf_2,
        "state": "NO_MATCH",
        "score": 0.0,
    }