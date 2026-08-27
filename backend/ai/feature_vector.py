"""
Pairwise Feature Vector Builder (Sprint 17 — XGBoost step, per Day 5
feedback: "Add XGBoost before going too deep into GNN")

Ye module do wallets ke beech ek 8-dimensional feature vector banata
hai — XGBoost (ya kisi bhi classical ML classifier) ke liye. Jahan
possible, EXISTING already-tested modules reuse kiye hain (dobara
nahi likhe):

    1. amount_similarity       -> attribution/similarity.py (existing)
    2. timing_similarity       -> naya (active-hours Jaccard overlap)
    3. counterparty_similarity -> naya (counterparty-set Jaccard overlap)
    4. frequency_similarity    -> attribution/similarity.py (existing)
    5. bridge_evidence         -> attribution/cross_chain_evidence.py (existing)
    6. contract_interaction    -> naya (label_database ke known
                                   contracts se count, phir similarity)
    7. entity_evidence         -> attribution/entity_agreement.py (existing)
    8. same_chain              -> naya (simple binary flag)

Sab features 0-1 range mein normalize kiye gaye hain.
"""

import pandas as pd

from features.extractor import feature_extractor
from attribution.similarity import similarity_engine
from attribution.cross_chain_evidence import calculate_cross_chain_evidence
from attribution.entity_agreement import calculate_entity_agreement
from entity_labeling.label_database import lookup_known_address

FEATURE_NAMES = [
    "amount_similarity",
    "timing_similarity",
    "counterparty_similarity",
    "frequency_similarity",
    "bridge_evidence",
    "contract_interaction_similarity",
    "entity_evidence",
    "same_chain",
]


def _active_hours(df: pd.DataFrame, wallet: str) -> set:
    """
    Wallet ke transactions se, din ke kaunse ghanton (0-23) mein wo
    active tha — set of hours return karta hai.
    """
    mask = (df["from_address"].str.lower() == wallet.lower()) | \
           (df["to_address"].str.lower() == wallet.lower())
    timestamps = df.loc[mask, "timestamp"].dropna()

    if len(timestamps) == 0:
        return set()

    hours = pd.to_datetime(timestamps, unit="s", errors="coerce").dt.hour.dropna()
    return set(hours.tolist())


def _counterparties(df: pd.DataFrame, wallet: str) -> set:
    """
    Wallet ne kis-kis address ke saath transact kiya — us set ko
    return karta hai (sender ya receiver, dono directions).
    """
    wallet_lower = wallet.lower()
    sent_to = df.loc[df["from_address"].str.lower() == wallet_lower, "to_address"]
    received_from = df.loc[df["to_address"].str.lower() == wallet_lower, "from_address"]
    return set(sent_to.str.lower()) | set(received_from.str.lower())


def _contract_interaction_count(df: pd.DataFrame, wallet: str) -> int:
    """
    Wallet ne kitni baar kisi KNOWN smart contract address ke saath
    interact kiya (entity_labeling/label_database.py se). Ye
    Day 1 audit mein flag ki gayi "hardcoded False placeholder"
    (WalletProfile.smart_contract_usage) ko bypass karta hai — seedha
    known-address table se count nikalta hai.
    """
    wallet_lower = wallet.lower()
    mask = (df["from_address"].str.lower() == wallet_lower) | \
           (df["to_address"].str.lower() == wallet_lower)
    counterparties = pd.concat([
        df.loc[mask, "from_address"],
        df.loc[mask, "to_address"],
    ]).str.lower()

    count = 0
    for address in counterparties.unique():
        if address == wallet_lower:
            continue
        match = lookup_known_address(address)
        if match and match["label"] == "Smart Contract":
            count += 1

    return count


def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 1.0
    return len(set_a & set_b) / len(union)


def build_pairwise_features(wallet_1: str, chain_1: str, csv_1: str,
                             wallet_2: str, chain_2: str, csv_2: str) -> dict:
    """
    Do wallets ke beech 8-dimensional feature vector banata hai.

    Returns:
        dict: {feature_name: float (0-1 range)}
    """
    df_1 = pd.read_csv(csv_1)
    df_2 = pd.read_csv(csv_2)

    profile_1 = feature_extractor.get_wallet_summary(csv_1, wallet_1, chain_1).to_dict()
    profile_2 = feature_extractor.get_wallet_summary(csv_2, wallet_2, chain_2).to_dict()

    # 1. Amount similarity (existing module reuse)
    amount_similarity = similarity_engine.compare_average_value(profile_1, profile_2)

    # 2. Timing similarity (naya — active hours Jaccard overlap)
    hours_1 = _active_hours(df_1, wallet_1)
    hours_2 = _active_hours(df_2, wallet_2)
    timing_similarity = _jaccard(hours_1, hours_2)

    # 3. Counterparty similarity (naya — counterparty-set Jaccard overlap)
    counterparties_1 = _counterparties(df_1, wallet_1)
    counterparties_2 = _counterparties(df_2, wallet_2)
    counterparty_similarity = _jaccard(counterparties_1, counterparties_2)

    # 4. Frequency similarity (existing module reuse)
    frequency_similarity = similarity_engine.compare_transaction_frequency(profile_1, profile_2)

    # 5. Bridge evidence (existing module reuse)
    if chain_1.lower() != chain_2.lower():
        evidence = calculate_cross_chain_evidence(csv_1, wallet_1, chain_1, csv_2, wallet_2, chain_2)
        bridge_evidence = evidence["score"] / 100.0
    else:
        bridge_evidence = 0.0  # Same-chain pairs ke liye ye signal relevant nahi

    # 6. Contract interaction similarity (naya)
    contract_count_1 = _contract_interaction_count(df_1, wallet_1)
    contract_count_2 = _contract_interaction_count(df_2, wallet_2)
    contract_interaction_similarity = similarity_engine._normalize_difference(
        contract_count_1, contract_count_2
    )

    # 7. Entity evidence (existing module reuse)
    entity_result = calculate_entity_agreement(
        wallet_1, profile_1, False, wallet_2, profile_2, False
    )
    # UNKNOWN state -> score is None. Simplification (disclosed): "no
    # evidence" aur "confirmed different" dono ko 0.0 collapse karte
    # hain, kyunki fixed-length feature vector ke liye ek numeric
    # value chahiye. Isay 9th feature ke taur par "evidence available"
    # flag se improve kiya ja sakta hai (future work).
    entity_evidence = (entity_result["score"] or 0.0) / 100.0

    # 8. Same chain (naya — simple binary flag)
    same_chain = 1.0 if chain_1.lower() == chain_2.lower() else 0.0

    return {
        "amount_similarity": round(amount_similarity, 4),
        "timing_similarity": round(timing_similarity, 4),
        "counterparty_similarity": round(counterparty_similarity, 4),
        "frequency_similarity": round(frequency_similarity, 4),
        "bridge_evidence": round(bridge_evidence, 4),
        "contract_interaction_similarity": round(contract_interaction_similarity, 4),
        "entity_evidence": round(entity_evidence, 4),
        "same_chain": same_chain,
    }


def build_feature_matrix(cases: list, csv_resolver) -> tuple:
    """
    Ground truth cases ki list se (X, y) banata hai — XGBoost training
    ke liye ready format.

    Args:
        cases (list): evaluation/ground_truth.py jaisi cases list
        csv_resolver: function(wallet, chain) -> csv_path

    Returns:
        (list[dict], list[int]): X (feature dicts), y (1=Related, 0=Unrelated)
    """
    X, y = [], []

    for case in cases:
        csv_1 = csv_resolver(case["wallet_a"], case["chain_a"])
        csv_2 = csv_resolver(case["wallet_b"], case["chain_b"])

        features = build_pairwise_features(
            case["wallet_a"], case["chain_a"], csv_1,
            case["wallet_b"], case["chain_b"], csv_2,
        )
        X.append(features)
        y.append(1 if case["ground_truth"] == "Related" else 0)

    return X, y