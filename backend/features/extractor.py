"""
Feature Extractor

Ye main module hai jo wallet transactions CSV se features nikalta hai
aur unhe WalletProfile object mein organize karta hai.

Flow:
Wallet Transactions CSV -> Load -> Extract Features -> Save Features CSV
"""

import os
import pandas as pd

from features import metrics
from features.wallet_profile import WalletProfile


class FeatureExtractor:
    """
    Ye class transactions CSV se wallet features nikalti hai.
    """

    FEATURES_FOLDER = "datasets/features"

    def load_transactions(self, file_path: str) -> pd.DataFrame:
        """
        Transactions CSV file padhta hai.

        Args:
            file_path (str): CSV file ka path

        Returns:
            pd.DataFrame: Transactions ka table
        """
        return pd.read_csv(file_path)

    def extract_features(self, df: pd.DataFrame, wallet_address: str, chain: str) -> WalletProfile:
        """
        Diye gaye transactions data se ek wallet ki poori profile banata hai.

        Args:
            df (pd.DataFrame): Transactions ka data
            wallet_address (str): Jis wallet ki features nikalni hain
            chain (str): Blockchain ka naam

        Returns:
            WalletProfile: Bhara hua wallet profile object
        """
        profile = WalletProfile(wallet_address, chain)

        # Basic
        first_tx, last_tx = metrics.calculate_first_last_transaction(df)
        profile.first_transaction = first_tx
        profile.last_transaction = last_tx

        # Activity
        profile.total_transactions = metrics.calculate_total_transactions(df)
        profile.sent_transactions = metrics.calculate_sent_transactions(df, wallet_address)
        profile.received_transactions = metrics.calculate_received_transactions(df, wallet_address)

        # Financial
        profile.total_sent_eth = metrics.calculate_total_sent_value(df, wallet_address)
        profile.total_received_eth = metrics.calculate_total_received_value(df, wallet_address)
        profile.average_transaction_value = metrics.calculate_average_value(df)
        profile.max_transaction_value = metrics.calculate_max_value(df)
        profile.min_transaction_value = metrics.calculate_min_value(df)

        # Network
        profile.unique_senders = metrics.calculate_unique_senders(df, wallet_address)
        profile.unique_receivers = metrics.calculate_unique_receivers(df, wallet_address)
        profile.total_unique_contacts = metrics.calculate_total_unique_contacts(df, wallet_address)

        # Time
        profile.active_days = metrics.calculate_active_days(df)
        if profile.active_days > 0:
            profile.average_transactions_per_day = round(
                profile.total_transactions / profile.active_days, 2
            )

        return profile

    def save_features(self, profile: WalletProfile) -> str:
        """
        Wallet profile ko ek CSV file mein save karta hai.

        Args:
            profile (WalletProfile): Save karne wala profile

        Returns:
            str: Saved CSV file ka path
        """
        os.makedirs(self.FEATURES_FOLDER, exist_ok=True)

        file_path = os.path.join(self.FEATURES_FOLDER, f"{profile.wallet_address}_features.csv")

        # Ek row wali table banate hain (kyunki ek hi wallet ka data hai)
        df = pd.DataFrame([profile.to_dict()])
        df.to_csv(file_path, index=False)

        return file_path

    def get_wallet_summary(self, file_path: str, wallet_address: str, chain: str) -> WalletProfile:
        """
        Poora process ek hi function mein karta hai:
        CSV load karo -> Features nikalo.

        Args:
            file_path (str): Transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            WalletProfile: Wallet ka poora profile
        """
        df = self.load_transactions(file_path)
        return self.extract_features(df, wallet_address, chain)


# Ek single instance banate hain jo poore project mein import hoga
feature_extractor = FeatureExtractor()