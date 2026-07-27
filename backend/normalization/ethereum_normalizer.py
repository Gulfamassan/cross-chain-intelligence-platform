"""
Ethereum Normalizer

Ethereum ka raw data Etherscan V2 API se aata hai, jo already
standard format mein hota hai. Ye central TransactionNormalizer
ko reuse karta hai.
"""

from normalization.normalizer import transaction_normalizer


def normalize_ethereum_transactions(transactions: list) -> list:
    return transaction_normalizer.normalize(transactions, "Ethereum")