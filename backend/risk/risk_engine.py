"""
Risk Engine

Ye main module hai jo raw transaction data se saare risk indicators
nikalta hai, unhe score karta hai, aur ek final risk level deta hai.
"""

import pandas as pd

from risk.indicators import risk_indicators
from risk.blacklist import blacklist
from risk.scoring import risk_scorer
from attribution.bridge_detector import bridge_detector
from features.extractor import feature_extractor


class RiskEngine:
    """
    Ye class ek wallet ki poori risk analysis karti hai.
    """

    def analyze(self, csv_path: str, wallet_address: str, chain: str) -> dict:
        """
        Diye gaye wallet ki poori risk analysis karta hai.

        Args:
            csv_path (str): Transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            dict: Risk score, risk level, aur poora breakdown
        """
        df = pd.read_csv(csv_path)
        transactions = df.to_dict("records")

        # Feature profile nikalte hain (active_days ke liye chahiye)
        profile = feature_extractor.get_wallet_summary(csv_path, wallet_address, chain)
        active_days = profile.active_days

        # Indicators nikalte hain
        large_tx_count = risk_indicators.detect_large_transactions(transactions)
        is_high_frequency = risk_indicators.detect_high_frequency(transactions, active_days)
        rapid_transfers = risk_indicators.detect_rapid_transfers(transactions)

        # Bridge detection
        bridge_txs = bridge_detector.detect_bridge_transactions(transactions, chain)
        bridge_detected = len(bridge_txs) > 0

        # Blacklist checks
        flags = blacklist.check_transactions_for_flags(transactions)

        # Darknet label — abhi placeholder (future mein real darknet list se check hoga)
        has_darknet_label = False

        # Final score calculate karte hain
        scoring_result = risk_scorer.calculate_risk_score(
            bridge_detected=bridge_detected,
            mixer_interactions=flags["mixer_interactions"],
            is_high_frequency=is_high_frequency,
            scam_interactions=flags["scam_interactions"],
            exchange_interactions=flags["exchange_interactions"],
            rapid_transfers=rapid_transfers,
            large_tx_count=large_tx_count,
            has_darknet_label=has_darknet_label,
        )

        risk_level = self._get_risk_level(scoring_result["total_risk_score"])

        return {
            "wallet": wallet_address,
            "chain": chain,
            "risk_score": scoring_result["total_risk_score"],
            "risk_level": risk_level,
            "breakdown": scoring_result["breakdown"],
            "indicators": {
                "bridge_detected": bridge_detected,
                "mixer_interactions": flags["mixer_interactions"],
                "scam_interactions": flags["scam_interactions"],
                "exchange_interactions": flags["exchange_interactions"],
                "high_frequency": is_high_frequency,
                "rapid_transfers": rapid_transfers,
                "large_transactions": large_tx_count,
            },
        }

    def _get_risk_level(self, score: float) -> str:
        """
        Numeric score ko readable risk level mein convert karta hai.
        """
        if score >= 70:
            return "High"
        elif score >= 40:
            return "Medium"
        else:
            return "Low"


# Ek single instance banate hain jo poore project mein import hoga
risk_engine = RiskEngine()