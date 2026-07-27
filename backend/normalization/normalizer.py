"""
Unified Transaction Normalizer

Ye module raw blockchain transactions ko ek Unified Transaction Schema
mein convert karta hai, taake Hybrid Engine ko farq na pade data
kis blockchain se aaya hai.

Note: Humare architecture mein saare collectors (Ethereum, Polygon,
Arbitrum) Etherscan ke unified V2 API se data lete hain, isliye
raw format hamesha same hota hai (from, to, value, timeStamp, hash).
Isliye ek hi normalization logic saari chains ke liye kaam karta hai —
chain-specific normalizers (neeche) isi central logic ko reuse karte hain.
"""

from blockchain.dataset_service import dataset_service


class TransactionNormalizer:
    """
    Ye class raw transactions ko Unified Schema mein convert karti hai.
    """

    def normalize(self, transactions: list, chain: str) -> list:
        """
        Kisi bhi chain ke raw transactions ko unified schema mein convert karta hai.

        Args:
            transactions (list): Raw transactions (Etherscan V2 format)
            chain (str): Blockchain ka naam (jaise "Ethereum", "Polygon")

        Returns:
            list: Unified schema mein normalized transactions
        """
        return dataset_service.normalize_transactions(transactions, chain)


# Ek single instance banate hain jo poore project mein import hoga
transaction_normalizer = TransactionNormalizer()