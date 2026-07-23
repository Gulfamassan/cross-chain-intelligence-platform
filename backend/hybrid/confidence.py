"""
Hybrid Confidence Classifier

Ye module Fusion Engine se aaye final confidence score ko
ek readable classification label mein convert karta hai.
"""


class HybridConfidenceClassifier:
    """
    Ye class final confidence score ko classification label deti hai.
    """

    def classify(self, final_confidence: float) -> str:
        """
        Diye gaye confidence score (0-100) ko classify karta hai.

        Args:
            final_confidence (float): Fusion Engine ka final score

        Returns:
            str: Classification label
        """
        if final_confidence >= 80:
            return "Likely Same Entity"
        elif final_confidence >= 60:
            return "Possible Same Entity"
        elif final_confidence >= 40:
            return "Uncertain"
        else:
            return "Likely Different Entities"


# Ek single instance banate hain jo poore project mein import hoga
hybrid_confidence_classifier = HybridConfidenceClassifier()