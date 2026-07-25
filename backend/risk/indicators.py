"""
Risk Indicators

Ye module individual risk signals detect karta hai — high transaction
frequency, large transactions, rapid activity, waghera. Har function
sirf ek specific pattern check karta hai.
"""

import pandas as pd


class RiskIndicators:
    """
    Ye class raw transaction data se individual risk signals nikalti hai.
    """

    LARGE_TRANSACTION_THRESHOLD_ETH = 10.0
    HIGH_FREQUENCY_THRESHOLD_PER_DAY = 20
    RAPID_HOPPING_MINUTES = 10

    def detect_large_transactions(self, transactions: list) -> int:
        """
        Kitni transactions "large" (threshold se zyada) hain, count karta hai.

        Args:
            transactions (list): Transactions ki list

        Returns:
            int: Large transactions ka count
        """
        count = 0
        for tx in transactions:
            value = tx.get("value_eth", 0)
            if not pd.isna(value) and value >= self.LARGE_TRANSACTION_THRESHOLD_ETH:
                count += 1
        return count

    def detect_high_frequency(self, transactions: list, active_days: int) -> bool:
        """
        Check karta hai ke wallet ki transaction frequency "high" hai ya nahi
        (matlab ye wallet bot jaisa ya automated behavior dikha rahi hai).

        Args:
            transactions (list): Transactions ki list
            active_days (int): Kitne din active raha

        Returns:
            bool: True agar high frequency hai
        """
        if active_days == 0:
            return False

        avg_per_day = len(transactions) / active_days
        return avg_per_day >= self.HIGH_FREQUENCY_THRESHOLD_PER_DAY

    def detect_rapid_transfers(self, transactions: list) -> int:
        """
        Kitni baar transactions ek dusre ke bahut kareeb (few minutes ke
        andar) hui hain — jo "rapid chain hopping" ka signal ho sakta hai.

        Args:
            transactions (list): Transactions ki list

        Returns:
            int: Rapid transfer pairs ka count
        """
        timestamps = sorted([
            tx.get("timestamp") for tx in transactions
            if tx.get("timestamp") and not pd.isna(tx.get("timestamp"))
        ])

        rapid_count = 0
        for i in range(len(timestamps) - 1):
            diff_seconds = timestamps[i + 1] - timestamps[i]
            diff_minutes = diff_seconds / 60
            if diff_minutes <= self.RAPID_HOPPING_MINUTES:
                rapid_count += 1

        return rapid_count

    def calculate_transaction_velocity(self, transactions: list, active_days: int) -> float:
        """
        Average transactions per day calculate karta hai.

        Args:
            transactions (list): Transactions ki list
            active_days (int): Kitne din active raha

        Returns:
            float: Average transactions per day
        """
        if active_days == 0:
            return 0.0
        return round(len(transactions) / active_days, 2)


# Ek single instance banate hain jo poore project mein import hoga
risk_indicators = RiskIndicators()