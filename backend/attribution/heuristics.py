"""
Heuristic Rules

Ye module wallet pairs ke beech evidence-based rules apply karta hai,
taake pata chale ke kya do wallets same entity (user) ke ho sakte hain.
Har rule ek score deta hai, jo milakar ek total confidence score banata hai.
"""

from datetime import datetime


class HeuristicEngine:
    """
    Ye class har rule ko check karti hai aur unke scores combine karti hai.
    """

    def rule_bridge_timing(self, bridge_tx_timestamp, receive_tx_timestamp, max_minutes: int = 5) -> int:
        """
        Rule 1: Agar bridge transaction ke 5 minute ke andar dusri chain
        par paisa receive hua ho, to ye strong signal hai.

        Args:
            bridge_tx_timestamp: Bridge transaction ka Unix timestamp
            receive_tx_timestamp: Dusri chain par receive hone ka Unix timestamp
            max_minutes (int): Kitne minute ke andar hona chahiye (default 5)

        Returns:
            int: 25 agar match ho, warna 0
        """
        if bridge_tx_timestamp is None or receive_tx_timestamp is None:
            return 0

        time_difference_seconds = abs(receive_tx_timestamp - bridge_tx_timestamp)
        time_difference_minutes = time_difference_seconds / 60

        if time_difference_minutes <= max_minutes:
            return 25

        return 0

    def rule_amount_match(self, amount1: float, amount2: float, tolerance: float = 0.05) -> int:
        """
        Rule 2: Agar dono transactions ka amount almost same ho
        (bridge fee ke wajah se thoda farq ho sakta hai).

        Args:
            amount1 (float): Pehli transaction ka amount
            amount2 (float): Dusri transaction ka amount
            tolerance (float): Kitna percent farq allow hai (default 5%)

        Returns:
            int: 20 agar match ho, warna 0
        """
        if amount1 is None or amount2 is None or amount1 == 0:
            return 0

        difference_percent = abs(amount1 - amount2) / amount1

        if difference_percent <= tolerance:
            return 20

        return 0

    def rule_gas_pattern_similarity(self, gas_price1: float, gas_price2: float, tolerance: float = 0.2) -> int:
        """
        Rule 3: Agar dono wallets ka gas price pattern similar ho
        (kuch wallets consistently high/low gas use karti hain, jo ek
        "fingerprint" ki tarah kaam kar sakta hai).

        Args:
            gas_price1 (float): Pehli wallet ka average gas price
            gas_price2 (float): Dusri wallet ka average gas price
            tolerance (float): Kitna percent farq allow hai (default 20%)

        Returns:
            int: 10 agar match ho, warna 0
        """
        if gas_price1 is None or gas_price2 is None or gas_price1 == 0:
            return 0

        difference_percent = abs(gas_price1 - gas_price2) / gas_price1

        if difference_percent <= tolerance:
            return 10

        return 0

    def rule_activity_timing(self, active_hours1: list, active_hours2: list, overlap_threshold: float = 0.6) -> int:
        """
        Rule 4: Agar dono wallets ek jaisi timing par active rehti hain
        (jaise dono raat ko active hain), to ye ek behavioral signal hai.

        Args:
            active_hours1 (list): Pehli wallet ke active hours (0-23), jaise [22, 23, 0, 1]
            active_hours2 (list): Dusri wallet ke active hours
            overlap_threshold (float): Kitna overlap chahiye (default 60%)

        Returns:
            int: 15 agar match ho, warna 0
        """
        if not active_hours1 or not active_hours2:
            return 0

        set1 = set(active_hours1)
        set2 = set(active_hours2)

        overlap = len(set1.intersection(set2))
        smaller_set_size = min(len(set1), len(set2))

        if smaller_set_size == 0:
            return 0

        overlap_ratio = overlap / smaller_set_size

        if overlap_ratio >= overlap_threshold:
            return 15

        return 0

    def rule_same_exchange_deposit(self, exchange1: str, exchange2: str) -> int:
        """
        Rule 5: Agar dono wallets ne same exchange (jaise Binance, Coinbase)
        mein deposit kiya ho, to ye ek strong signal hai (exchange KYC ki wajah se).

        Note: Ye abhi ek placeholder hai — known exchange addresses ki list
        future mein banayi jayegi (bridges.json jaisi).

        Args:
            exchange1 (str): Pehli wallet ne jis exchange mein deposit kiya
            exchange2 (str): Dusri wallet ne jis exchange mein deposit kiya

        Returns:
            int: 30 agar same exchange ho, warna 0
        """
        if not exchange1 or not exchange2:
            return 0

        if exchange1.lower() == exchange2.lower():
            return 30

        return 0

    def calculate_total_score(
        self,
        bridge_tx_timestamp=None,
        receive_tx_timestamp=None,
        amount1=None,
        amount2=None,
        gas_price1=None,
        gas_price2=None,
        active_hours1=None,
        active_hours2=None,
        exchange1=None,
        exchange2=None,
    ) -> dict:
        """
        Saare rules apply karta hai aur ek total score deta hai,
        har rule ka individual breakdown ke saath.

        Returns:
            dict: Har rule ka score, total score, aur max possible score
        """
        score_bridge_timing = self.rule_bridge_timing(bridge_tx_timestamp, receive_tx_timestamp)
        score_amount_match = self.rule_amount_match(amount1, amount2)
        score_gas_pattern = self.rule_gas_pattern_similarity(gas_price1, gas_price2)
        score_activity_timing = self.rule_activity_timing(active_hours1, active_hours2)
        score_exchange_deposit = self.rule_same_exchange_deposit(exchange1, exchange2)

        total_score = (
            score_bridge_timing +
            score_amount_match +
            score_gas_pattern +
            score_activity_timing +
            score_exchange_deposit
        )

        return {
            "bridge_timing_score": score_bridge_timing,
            "amount_match_score": score_amount_match,
            "gas_pattern_score": score_gas_pattern,
            "activity_timing_score": score_activity_timing,
            "exchange_deposit_score": score_exchange_deposit,
            "total_score": total_score,
            "max_possible_score": 100,
        }


# Ek single instance banate hain jo poore project mein import hoga
heuristic_engine = HeuristicEngine()