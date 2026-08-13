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

    def combine_scores_missing_aware(self, rule_score: float, embedding_score: float,
                                        relationship_score: float | None, risk_score: float) -> dict:
        """
        Sprint 14 Day 4 — EXPERIMENTAL "Version B" fusion.

        Identical to combine_scores() (Version A / Baseline), EXCEPT: if
        relationship_score is None (i.e. graph-based signal genuinely
        unavailable — e.g. cross-chain pair where the graph was built
        from only one chain), that signal is excluded entirely rather
        than treated as 0. Its weight is redistributed proportionally
        across the remaining available signals, so their relative
        importance stays the same.

        This does NOT change behavior when relationship_score is a real
        number (including a real 0) — only when it is None.

        Args:
            rule_score, embedding_score, risk_score: same as combine_scores()
            relationship_score: float (0-100) if available, or None if the
                                 graph signal genuinely could not be computed

        Returns:
            dict: same shape as combine_scores(), plus "signal_excluded"
                  flag so callers/reports can see when this path was used
        """
        self.weights = self._load_weights()

        if relationship_score is None:
            w_rule = self.weights.get("rule", 0.40)
            w_embedding = self.weights.get("embedding", 0.35)
            w_relationship = self.weights.get("relationship", 0.15)
            w_risk = self.weights.get("risk", 0.10)

            remaining_total = w_rule + w_embedding + w_risk
            if remaining_total == 0:
                w_rule = w_embedding = w_risk = 1 / 3
            else:
                scale = (w_rule + w_embedding + w_risk + w_relationship) / remaining_total
                w_rule *= scale
                w_embedding *= scale
                w_risk *= scale

            final_confidence = (
                rule_score * w_rule +
                embedding_score * w_embedding +
                risk_score * w_risk
            )

            return {
                "rule_score": round(rule_score, 2),
                "embedding_score": round(embedding_score, 2),
                "relationship_score": None,
                "risk_score": round(risk_score, 2),
                "weights_used": {
                    "rule": round(w_rule, 4),
                    "embedding": round(w_embedding, 4),
                    "relationship": 0.0,
                    "risk": round(w_risk, 4),
                },
                "final_confidence": round(final_confidence, 2),
                "signal_excluded": "relationship",
            }

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
            "signal_excluded": None,
        }

    def combine_scores_with_entity_agreement(self, rule_score: float, embedding_score: float,
                                                relationship_score: float, risk_score: float,
                                                entity_agreement_score: float | None) -> dict:
        """
        Sprint 15 Day 3 — EXPERIMENTAL fusion, adds the entity agreement
        signal (attribution/entity_agreement.py) as a fifth input.

        This is NOT the production fusion — combine_scores() remains
        the baseline/current version, completely unchanged. This method
        exists purely to run a controlled Current vs Experimental
        comparison (see evaluation/run_entity_agreement_fusion_experiment.py).

        entity_agreement_score of None means the signal was UNKNOWN
        (see entity_agreement.py) — it is excluded from the weighted
        sum entirely (not treated as 0), and its weight is NOT
        redistributed here; the comparison script computes both a
        "weight excluded" and reports the raw config weight so the
        effect is fully visible, not hidden by renormalization.

        Args:
            rule_score, embedding_score, relationship_score, risk_score: same as combine_scores()
            entity_agreement_score: float (0-100) if MATCH/NO_MATCH, or None if UNKNOWN

        Returns:
            dict: same shape as combine_scores(), plus entity_agreement fields
        """
        self.weights = self._load_weights()
        w_entity = self.weights.get("entity_agreement", 0.0)

        if entity_agreement_score is None:
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
                "entity_agreement_score": None,
                "entity_agreement_weight_used": 0.0,
                "weights_used": self.weights,
                "final_confidence": round(final_confidence, 2),
            }

        final_confidence = (
            rule_score * self.weights.get("rule", 0.40) +
            embedding_score * self.weights.get("embedding", 0.35) +
            relationship_score * self.weights.get("relationship", 0.15) +
            risk_score * self.weights.get("risk", 0.10) +
            entity_agreement_score * w_entity
        )

        return {
            "rule_score": round(rule_score, 2),
            "embedding_score": round(embedding_score, 2),
            "relationship_score": round(relationship_score, 2),
            "risk_score": round(risk_score, 2),
            "entity_agreement_score": round(entity_agreement_score, 2),
            "entity_agreement_weight_used": w_entity,
            "weights_used": self.weights,
            "final_confidence": round(final_confidence, 2),
        }


# Ek single instance banate hain jo poore project mein import hoga
fusion_engine = FusionEngine()