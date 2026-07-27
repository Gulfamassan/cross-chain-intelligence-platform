"""
BNB Normalizer

BNB Chain abhi active nahi hai (Etherscan free tier restriction),
lekin jab activate hoga to ye bhi same unified format follow karega.
"""

from normalization.normalizer import transaction_normalizer


def normalize_bnb_transactions(transactions: list) -> list:
    return transaction_normalizer.normalize(transactions, "BNB Chain")