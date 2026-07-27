"""
Polygon Normalizer

Polygon ka raw data bhi Etherscan V2 API se aata hai (same format
jaisa Ethereum), isliye ye bhi central normalizer ko reuse karta hai.
"""

from normalization.normalizer import transaction_normalizer


def normalize_polygon_transactions(transactions: list) -> list:
    return transaction_normalizer.normalize(transactions, "Polygon")