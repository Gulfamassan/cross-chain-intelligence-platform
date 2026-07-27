"""
Arbitrum Normalizer

Arbitrum ka raw data bhi Etherscan V2 API se aata hai, isliye
ye bhi central normalizer ko reuse karta hai.
"""

from normalization.normalizer import transaction_normalizer


def normalize_arbitrum_transactions(transactions: list) -> list:
    return transaction_normalizer.normalize(transactions, "Arbitrum")