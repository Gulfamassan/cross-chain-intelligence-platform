"""
Explanation Engine (Evaluator)

Ye module batata hai KYUN ek particular attribution score aaya —
sirf number nahi, balki concrete reasons deta hai, taake investigator
ko explainable AI mile.
"""


class ExplanationEngine:
    """
    Ye class scores aur raw evidence se human-readable explanations banati hai.
    """

    def generate_explanation(
        self,
        bridge_detected: bool = False,
        bridge_name: str = None,
        rule_score: float = 0,
        embedding_score: float = 0,
        relationship_score: float = 0,
        common_neighbors_count: int = 0,
        activity_timing_match: bool = False,
        exchange_match: bool = False,
    ) -> list:
        """
        Diye gaye evidence se explanation points ki list banata hai.

        Args:
            bridge_detected (bool): Kya bridge activity mili
            bridge_name (str): Konsa bridge use hua
            rule_score (float): Rule-based score
            embedding_score (float): AI embedding score
            relationship_score (float): Relationship/graph score
            common_neighbors_count (int): Kitne common neighbors hain
            activity_timing_match (bool): Kya activity timing match karti hai
            exchange_match (bool): Kya same exchange use hua

        Returns:
            list: Explanation points (readable strings)
        """
        explanations = []

        if bridge_detected:
            if bridge_name:
                explanations.append(f"Bridge activity detected ({bridge_name})")
            else:
                explanations.append("Bridge activity detected")

        if embedding_score >= 80:
            explanations.append("High embedding similarity (strong graph structural match)")
        elif embedding_score >= 60:
            explanations.append("Moderate embedding similarity")

        if rule_score >= 70:
            explanations.append("Strong rule-based evidence (timing, amount, and gas patterns align)")

        if common_neighbors_count > 0:
            explanations.append(f"Common neighbors found ({common_neighbors_count} shared connections)")

        if activity_timing_match:
            explanations.append("Same active hours detected")

        if exchange_match:
            explanations.append("Common exchange interaction detected")

        if relationship_score >= 70:
            explanations.append("High graph relationship score")

        # Agar koi bhi signal strong nahi mila
        if not explanations:
            explanations.append("Limited evidence found — no strong matching signals detected")

        return explanations


# Ek single instance banate hain jo poore project mein import hoga
explanation_engine = ExplanationEngine()