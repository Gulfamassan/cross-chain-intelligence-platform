"""
backend/entity_labeling/wallet_classifier.py

Rule-based heuristic classifier for wallet entity type.
Mirrors the Risk Engine pattern: deterministic thresholds with
stated reasons — explainable, not a black box.

Feature pipeline: Wallet -> tx_count -> avg_amount -> interaction_count
                   -> contract_calls -> bridge_usage -> Classification
"""

from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    label: str
    confidence: float
    reasons: list = field(default_factory=list)


def classify_wallet(features: dict, is_contract: bool = False) -> ClassificationResult:
    reasons = []

    tx_count = features.get("tx_count", 0)
    unique_cp = features.get("unique_counterparties", 0)
    avg_value = features.get("avg_tx_value", 0)
    active_days = features.get("active_days", 0)
    in_out_ratio = features.get("in_out_ratio", 1.0)
    bridge_usage = features.get("bridge_usage", 0)
    contract_calls = features.get("contract_calls", 0)

    # --- Rule 1: Smart Contract (deterministic, highest priority) ---
    if is_contract:
        reasons.append("Address has deployed contract bytecode")
        return ClassificationResult(label="Smart Contract", confidence=0.95, reasons=reasons)

    # --- Rule 2: Bridge Wallet — direct signal first ---
    if bridge_usage >= 3:
        reasons.append(f"Interacted with bridge contracts {bridge_usage} times")
        confidence = min(0.70 + (bridge_usage * 0.02), 0.93)
        reasons.append(f"Balanced in/out ratio ({in_out_ratio:.2f}) suggests pass-through activity")
        return ClassificationResult(label="Bridge Wallet", confidence=round(confidence, 2), reasons=reasons)

    # --- Rule 3: Exchange Wallet ---
    if unique_cp >= 500 and tx_count >= 1000:
        reasons.append(f"Very high counterparty diversity ({unique_cp} unique addresses)")
        reasons.append(f"High transaction volume ({tx_count} transactions)")
        confidence = min(0.75 + (unique_cp / 10000), 0.95)
        return ClassificationResult(label="Exchange Wallet", confidence=round(confidence, 2), reasons=reasons)

    # --- Rule 4: Bridge Wallet — indirect signal fallback ---
    if 0.85 <= in_out_ratio <= 1.15 and avg_value > 1.0 and unique_cp >= 50:
        reasons.append(f"Balanced in/out ratio ({in_out_ratio:.2f}) suggests pass-through activity")
        reasons.append(f"High average transaction value ({avg_value:.4f})")
        return ClassificationResult(label="Bridge Wallet", confidence=0.65, reasons=reasons)

    # --- Rule 5: Personal Wallet ---
    if unique_cp <= 30 and tx_count <= 200 and active_days >= 1:
        reasons.append(f"Low counterparty count ({unique_cp}) typical of individual use")
        reasons.append(f"Moderate transaction volume ({tx_count} transactions)")
        if contract_calls > 0:
            reasons.append(f"Some contract interactions detected ({contract_calls})")
        return ClassificationResult(label="Personal Wallet", confidence=0.60, reasons=reasons)

    # --- Fallback ---
    reasons.append("No heuristic rule met the confidence threshold")
    return ClassificationResult(label="Unknown", confidence=0.30, reasons=reasons)