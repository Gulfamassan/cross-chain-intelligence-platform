"""
backend/entity_labeling/wallet_classifier.py

Rule-based heuristic classifier for wallet entity type.
Mirrors the Risk Engine pattern: deterministic thresholds with
stated reasons — explainable, not a black box.
"""

from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    label: str
    confidence: float
    reasons: list = field(default_factory=list)


def classify_wallet(features: dict, is_contract: bool = False) -> ClassificationResult:
    """
    features expected keys (match your existing feature_engineering
    module's output — adjust names if different):
      tx_count, unique_counterparties, avg_tx_value,
      active_days, in_out_ratio
    """
    reasons = []

    if is_contract:
        reasons.append("Address has deployed contract bytecode")
        return ClassificationResult(label="Smart Contract", confidence=0.95, reasons=reasons)

    tx_count = features.get("tx_count", 0)
    unique_cp = features.get("unique_counterparties", 0)
    avg_value = features.get("avg_tx_value", 0)
    active_days = features.get("active_days", 0)
    in_out_ratio = features.get("in_out_ratio", 1.0)

    if unique_cp >= 500 and tx_count >= 1000:
        reasons.append(f"Very high counterparty diversity ({unique_cp} unique addresses)")
        reasons.append(f"High transaction volume ({tx_count} transactions)")
        return ClassificationResult(label="Exchange Wallet", confidence=0.80, reasons=reasons)

    if 0.85 <= in_out_ratio <= 1.15 and avg_value > 1.0 and unique_cp >= 50:
        reasons.append(f"Balanced in/out ratio ({in_out_ratio:.2f}) suggests pass-through activity")
        reasons.append(f"High average transaction value ({avg_value:.4f})")
        return ClassificationResult(label="Bridge Wallet", confidence=0.65, reasons=reasons)

    if unique_cp <= 30 and tx_count <= 200 and active_days >= 1:
        reasons.append(f"Low counterparty count ({unique_cp}) typical of individual use")
        reasons.append(f"Moderate transaction volume ({tx_count} transactions)")
        return ClassificationResult(label="Personal Wallet", confidence=0.60, reasons=reasons)

    reasons.append("No heuristic rule met the confidence threshold")
    return ClassificationResult(label="Unknown", confidence=0.30, reasons=reasons)