"""
Risk Rules

Ye module har risk indicator ko ek score (weight) deta hai.
Saare rules combine hoke final risk score banate hain.
"""


class RiskRules:
    """
    Ye class har risk signal ke liye points define karti hai.
    """

    def score_bridge_usage(self, bridge_detected: bool) -> int:
        """Bridge use karna thoda risky ho sakta hai (fund obfuscation)."""
        return 15 if bridge_detected else 0

    def score_mixer_interaction(self, mixer_interactions: int) -> int:
        """Mixer se interaction bahut bara red flag hai."""
        return 30 if mixer_interactions > 0 else 0

    def score_high_frequency(self, is_high_frequency: bool) -> int:
        """High frequency (bot-jaisa) behavior thoda suspicious hai."""
        return 10 if is_high_frequency else 0

    def score_known_scam(self, scam_interactions: int) -> int:
        """Known scam address se interaction sabse bara red flag hai."""
        return 40 if scam_interactions > 0 else 0

    def score_known_exchange(self, exchange_interactions: int) -> int:
        """
        Exchange se interaction risk nahi badhata (normal activity hai),
        lekin isay track karna zaroori hai (KYC correlation ke liye).
        """
        return 0

    def score_rapid_chain_hopping(self, rapid_transfers: int) -> int:
        """Bohot tezi se paisa move karna (rapid hops) suspicious hai."""
        if rapid_transfers >= 5:
            return 20
        elif rapid_transfers >= 2:
            return 10
        return 0

    def score_large_transactions(self, large_tx_count: int) -> int:
        """Bare transactions thoda risk add karte hain (money laundering ka signal ho sakta hai)."""
        if large_tx_count >= 5:
            return 15
        elif large_tx_count >= 1:
            return 5
        return 0

    def score_darknet_labels(self, has_darknet_label: bool) -> int:
        """Darknet se koi labeled connection hona bahut bara red flag hai."""
        return 35 if has_darknet_label else 0


# Ek single instance banate hain jo poore project mein import hoga
risk_rules = RiskRules()