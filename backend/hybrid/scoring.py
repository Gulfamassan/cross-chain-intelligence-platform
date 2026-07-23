"""
Scoring Orchestrator

Ye module saare 4 scores (rule-based, embedding, relationship, risk)
nikalta hai aur unhe Fusion Engine ko pass karta hai final confidence
nikalne ke liye.
"""

import pandas as pd

from features.extractor import feature_extractor
from attribution.similarity import similarity_engine
from attribution.bridge_detector import bridge_detector
from analytics.relationship_engine import relationship_engine
from analytics.centrality import centrality_analyzer
from ai.node2vec_model import node2vec_trainer
from ai.similarity_model import embedding_similarity


class HybridScorer:
    """
    Ye class saare individual scores nikalti hai jo Hybrid Engine ko chahiye.
    """

    # Risk Engine abhi implement nahi hua — neutral placeholder score
    DEFAULT_RISK_SCORE = 50.0

    def calculate_rule_score(self, wallet_1_csv: str, wallet_2_csv: str,
                              wallet_1: str, wallet_2: str, chain: str) -> dict:
        """
        Rule-based score nikalta hai — behavior similarity + bridge detection.

        Returns:
            dict: rule_score (0-100), bridge_detected, bridge_name
        """
        profile_1 = feature_extractor.get_wallet_summary(wallet_1_csv, wallet_1, chain)
        profile_2 = feature_extractor.get_wallet_summary(wallet_2_csv, wallet_2, chain)

        similarity_result = similarity_engine.calculate_similarity_score(
            profile_1.to_dict(), profile_2.to_dict()
        )
        base_score = similarity_result["overall_similarity_score"] * 100

        df_2 = pd.read_csv(wallet_2_csv)
        transactions_2 = df_2.to_dict("records")
        bridge_txs = bridge_detector.detect_bridge_transactions(transactions_2, chain)
        bridge_detected = len(bridge_txs) > 0
        bridge_name = bridge_txs[0]["bridge_name"] if bridge_detected else None

        rule_score = base_score
        if bridge_detected:
            rule_score = min(100, rule_score + 20)

        return {
            "rule_score": round(rule_score, 2),
            "bridge_detected": bridge_detected,
            "bridge_name": bridge_name,
        }

    def calculate_embedding_score(self, wallet_1: str, wallet_2: str) -> float:
        """
        AI-based embedding similarity score nikalta hai (0-100 scale mein).

        Returns:
            float: Embedding score (0-100)
        """
        embeddings = node2vec_trainer.load_embeddings()

        if not embeddings:
            return 0.0

        wallet_1_key = wallet_1.lower()
        wallet_2_key = wallet_2.lower()

        if wallet_1_key not in embeddings or wallet_2_key not in embeddings:
            return 0.0

        result = embedding_similarity.compare_wallets(embeddings, wallet_1, wallet_2)

        # Cosine similarity -1 se 1 tak ho sakti hai, ise 0-100 scale mein convert karte hain
        score_0_to_1 = (result["ai_similarity"] + 1) / 2
        return round(score_0_to_1 * 100, 2)

    def calculate_relationship_score(self, graph, wallet_1: str, wallet_2: str) -> dict:
        """
        Graph relationship score nikalta hai — direct connection, common
        neighbors, aur centrality ko combine karke.

        Returns:
            dict: relationship_score (0-100), common_neighbors_count
        """
        wallet_1_key = wallet_1.lower()
        wallet_2_key = wallet_2.lower()

        if wallet_1_key not in graph or wallet_2_key not in graph:
            return {"relationship_score": 0.0, "common_neighbors_count": 0}

        common = relationship_engine.common_neighbors(graph, wallet_1_key, wallet_2_key)

        all_centrality = centrality_analyzer.analyze_all(graph)
        centrality_1 = all_centrality.get(wallet_1_key, {}).get("degree", 0.0)
        centrality_2 = all_centrality.get(wallet_2_key, {}).get("degree", 0.0)

        # Average centrality ko 0-100 scale mein convert karte hain, max 100 tak cap karte hain
        avg_centrality = (centrality_1 + centrality_2) / 2
        relationship_score = min(100, avg_centrality * 100)

        return {
            "relationship_score": round(relationship_score, 2),
            "common_neighbors_count": len(common),
        }

    def get_risk_score(self) -> float:
        """
        Risk score deta hai — abhi Risk Engine nahi bana, isliye
        neutral placeholder return karta hai.

        Returns:
            float: Default/placeholder risk score
        """
        return self.DEFAULT_RISK_SCORE


# Ek single instance banate hain jo poore project mein import hoga
hybrid_scorer = HybridScorer()