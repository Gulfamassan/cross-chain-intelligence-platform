"""
backend/evaluation/run_entity_agreement_experiment.py

Sprint 15 — validates the entity agreement signal against the ground
truth dataset BEFORE it is wired into fusion.py. This determines
whether the signal has real evidentiary value or not.

Run from backend/: python -m evaluation.run_entity_agreement_experiment
"""

import os
from evaluation.ground_truth import get_dataset
from attribution.entity_agreement import calculate_entity_agreement
from features.extractor import feature_extractor


def resolve_csv_path(wallet_address: str, chain: str) -> str:
    path = os.path.join("datasets", chain.lower(), f"{wallet_address}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return path


if __name__ == "__main__":
    dataset = get_dataset()

    print(f"{'Case':<6}{'Expected':<12}{'W1 Label':<18}{'W2 Label':<18}{'State':<12}{'Score'}")
    for case in dataset:
        csv_1 = resolve_csv_path(case["wallet_a"], case["chain_a"])
        csv_2 = resolve_csv_path(case["wallet_b"], case["chain_b"])

        profile_1 = feature_extractor.get_wallet_summary(csv_1, case["wallet_a"], case["chain_a"]).to_dict()
        profile_2 = feature_extractor.get_wallet_summary(csv_2, case["wallet_b"], case["chain_b"]).to_dict()

        result = calculate_entity_agreement(
            case["wallet_a"], profile_1, False,
            case["wallet_b"], profile_2, False,
        )

        print(
            f"{case['case_id']:<6}{case['ground_truth']:<12}"
            f"{result['wallet_1_label']:<18}{result['wallet_2_label']:<18}"
            f"{result['state']:<12}{result['score']}"
        )