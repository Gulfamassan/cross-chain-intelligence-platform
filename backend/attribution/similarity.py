"""
Similarity Engine

Ye module do wallets ke behavior features compare karta hai aur
ek similarity score deta hai — jitna zyada score, utna zyada ye
dono wallets "similar" hain apne transaction patterns mein.
"""


class SimilarityEngine:
    """
    Ye class do WalletProfile objects (ya unke dictionaries) ke
    beech similarity calculate karti hai.
    """

    def _normalize_difference(self, value1: float, value2: float) -> float:
        """
        Do numbers ke beech ka farq nikal kar 0-1 ke beech normalize karta hai.
        0 = bilkul alag, 1 = bilkul same.

        Args:
            value1 (float): Pehli value
            value2 (float): Dusri value

        Returns:
            float: Similarity score (0 se 1 ke beech)
        """
        if value1 == 0 and value2 == 0:
            return 1.0

        max_value = max(abs(value1), abs(value2))
        if max_value == 0:
            return 1.0

        difference = abs(value1 - value2)
        similarity = 1 - (difference / max_value)

        return max(0.0, similarity)

    def compare_average_value(self, profile1: dict, profile2: dict) -> float:
        """
        Average transaction value compare karta hai.
        """
        value1 = profile1.get("average_transaction_value", 0)
        value2 = profile2.get("average_transaction_value", 0)
        return self._normalize_difference(value1, value2)

    def compare_transaction_frequency(self, profile1: dict, profile2: dict) -> float:
        """
        Average transactions per day compare karta hai.
        """
        value1 = profile1.get("average_transactions_per_day", 0)
        value2 = profile2.get("average_transactions_per_day", 0)
        return self._normalize_difference(value1, value2)

    def compare_unique_contacts(self, profile1: dict, profile2: dict) -> float:
        """
        Unique contacts count compare karta hai.
        """
        value1 = profile1.get("total_unique_contacts", 0)
        value2 = profile2.get("total_unique_contacts", 0)
        return self._normalize_difference(value1, value2)

    def compare_total_transactions(self, profile1: dict, profile2: dict) -> float:
        """
        Total transactions count compare karta hai.
        """
        value1 = profile1.get("total_transactions", 0)
        value2 = profile2.get("total_transactions", 0)
        return self._normalize_difference(value1, value2)

    def calculate_similarity_score(self, profile1: dict, profile2: dict) -> dict:
        """
        Do wallet profiles ke beech overall similarity score calculate karta hai,
        kai features ko combine karke.

        Args:
            profile1 (dict): Pehli wallet ka feature profile
            profile2 (dict): Dusri wallet ka feature profile

        Returns:
            dict: Har feature ka individual score, aur ek overall similarity score
        """
        avg_value_similarity = self.compare_average_value(profile1, profile2)
        frequency_similarity = self.compare_transaction_frequency(profile1, profile2)
        contacts_similarity = self.compare_unique_contacts(profile1, profile2)
        total_tx_similarity = self.compare_total_transactions(profile1, profile2)

        # Har feature ko equal weight de rahe hain abhi (0.25 each) — future mein
        # in weights ko tune kiya ja sakta hai jaise koi feature zyada important ho
        overall_score = (
            avg_value_similarity * 0.25 +
            frequency_similarity * 0.25 +
            contacts_similarity * 0.25 +
            total_tx_similarity * 0.25
        )

        return {
            "wallet_a": profile1.get("wallet_address"),
            "wallet_b": profile2.get("wallet_address"),
            "average_value_similarity": round(avg_value_similarity, 4),
            "frequency_similarity": round(frequency_similarity, 4),
            "contacts_similarity": round(contacts_similarity, 4),
            "total_transactions_similarity": round(total_tx_similarity, 4),
            "overall_similarity_score": round(overall_score, 4),
        }


# Ek single instance banate hain jo poore project mein import hoga
similarity_engine = SimilarityEngine()