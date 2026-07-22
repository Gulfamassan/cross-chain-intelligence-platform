"""
Confidence Score

Ye module numeric scores ko human-readable confidence labels
mein convert karta hai, taake investigator ko turant samajh aaye
ke attribution kitni reliable hai.
"""


class ConfidenceCalculator:
    """
    Ye class scores ko confidence percentage aur labels mein convert karti hai.
    """

    def get_confidence_label(self, score: float) -> str:
        """
        Diye gaye score (0-100) ko ek confidence label deta hai.

        Args:
            score (float): Combined score (0 se 100 ke beech)

        Returns:
            str: "High", "Medium", ya "Low"
        """
        if score >= 75:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"

    def get_confidence_summary(self, score: float) -> dict:
        """
        Score ka poora summary deta hai — percentage aur label dono.

        Args:
            score (float): Combined score (0 se 100 ke beech)

        Returns:
            dict: Percentage aur confidence label
        """
        percentage = round(score, 2)
        label = self.get_confidence_label(score)

        return {
            "confidence_percentage": percentage,
            "confidence_label": label,
        }


# Ek single instance banate hain jo poore project mein import hoga
confidence_calculator = ConfidenceCalculator()