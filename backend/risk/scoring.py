"""
Risk Scoring

Ye module saare risk rules ke scores combine karta hai aur ek
final risk score (0-100) banata hai.
"""

from risk.risk_rules import risk_rules


class RiskScorer:
    """
    Ye class saare individual risk scores ko combine karti hai.
    """

    MAX_SCORE = 100

    def calculate_risk_score(
        self,
        bridge_detected: bool = False,
        mixer_interactions: int = 0,
        is_high_frequency: bool = False,
        scam_interactions: int = 0,
        exchange_interactions: int = 0,
        rapid_transfers: int = 0,
        large_tx_count: int = 0,
        has_darknet_label: bool = False,
    ) -> dict:
        """
        Saare risk indicators ke scores combine karke final risk score deta hai.

        Returns:
            dict: Har rule ka score, aur final total risk score (0-100 tak capped)
        """
        scores = {
            "bridge_usage": risk_rules.score_bridge_usage(bridge_detected),
            "mixer_interaction": risk_rules.score_mixer_interaction(mixer_interactions),
            "high_frequency": risk_rules.score_high_frequency(is_high_frequency),
            "known_scam": risk_rules.score_known_scam(scam_interactions),
            "known_exchange": risk_rules.score_known_exchange(exchange_interactions),
            "rapid_chain_hopping": risk_rules.score_rapid_chain_hopping(rapid_transfers),
            "large_transactions": risk_rules.score_large_transactions(large_tx_count),
            "darknet_labels": risk_rules.score_darknet_labels(has_darknet_label),
        }

        total_score = sum(scores.values())
        # Score ko 0-100 ke beech "cap" karte hain (kabhi 100 se zyada na jaye)
        total_score = min(total_score, self.MAX_SCORE)

        return {
            "breakdown": scores,
            "total_risk_score": total_score,
        }


# Ek single instance banate hain jo poore project mein import hoga
risk_scorer = RiskScorer()