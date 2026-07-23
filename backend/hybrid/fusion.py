"""
Fusion Engine

Ye module Rule-Based score, AI Embedding score, Relationship score,
aur Risk score ko combine karke ek final confidence score deta hai.
Weights configurable hain (config/weights.json se aate hain), taake
code change kiye bina importance adjust ki ja sake.
"""

import json
import os


class FusionEngine:
    """
    Ye class alag-alag scores ko weighted average se combine karti hai.
    """

    WEIGHTS_PATH = os.path.join("config", "weights.json")

    def __init__(self):
        """
        Weights configuration load karte hain jab class banti hai.
        """
        self.weights = self._load_weights()

    def _load_weights(self) -> dict:
        """
        weights.json file se saare weights padhta hai.

        Returns:
            dict: Weights configuration, ya default weights agar file na mile
        """
        default_weights = {
            "rule": 0.40,
            "embedding": 0.35,
            "relationship": 0.15,
            "risk": 0.10,
        }

        if not os.path.exists(self.WEIGHTS_PATH):
            return default_weights

        with open(self.WEIGHTS_PATH, "r") as f:
            return json.load(f)

    def combine_scores(self, rule_score: float, embedding_score: float,
                        relationship_score: float, risk_score: float) -> dict:
        """
        Saare scores ko configurable weights ke saath combine karta hai.

        Args:
            rule_score (float): Rule-based attribution score (0-100)
            embedding_score (float): AI embedding similarity score (0-100)
            relationship_score (float): Graph relationship score (0-100)
            risk_score (float): Risk engine ka score (0-100)

        Returns:
            dict: Har score, weights, aur final combined confidence
        """
        # Har baar taaza weights padhte hain, taake agar file change ho
        # (jaise Team Lead ne edit ki) to naye weights turant use hon
        self.weights = self._load_weights()

        final_confidence = (
            rule_score * self.weights.get("rule", 0.40) +
            embedding_score * self.weights.get("embedding", 0.35) +
            relationship_score * self.weights.get("relationship", 0.15) +
            risk_score * self.weights.get("risk", 0.10)
        )

        return {
            "rule_score": round(rule_score, 2),
            "embedding_score": round(embedding_score, 2),
            "relationship_score": round(relationship_score, 2),
            "risk_score": round(risk_score, 2),
            "weights_used": self.weights,
            "final_confidence": round(final_confidence, 2),
        }


# Ek single instance banate hain jo poore project mein import hoga
fusion_engine = FusionEngine()