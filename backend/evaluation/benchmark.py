"""
Benchmark Engine

Ye module Rule-Based, Node2Vec (AI), aur Hybrid approaches ko
compare karta hai — taake evidence mile ke konsa approach behtar
result deta hai.
"""

from attribution.similarity import similarity_engine
from ai.node2vec_model import node2vec_trainer
from ai.similarity_model import embedding_similarity
from hybrid.scoring import hybrid_scorer
from hybrid.fusion import fusion_engine
from features.extractor import feature_extractor


class BenchmarkEngine:
    """
    Ye class teeno approaches ko run karke unke scores compare karti hai.
    """

    def compare_approaches(self, wallet_1: str, wallet_2: str, wallet_1_csv: str,
                            wallet_2_csv: str, graph, chain: str = "ethereum") -> dict:
        """
        Ek wallet pair par teeno approaches (Rule, Node2Vec, Hybrid) chalata hai
        aur unke scores compare karta hai.

        Args:
            wallet_1 (str): Pehli wallet
            wallet_2 (str): Dusri wallet
            wallet_1_csv (str): Pehli wallet ki transactions CSV
            wallet_2_csv (str): Dusri wallet ki transactions CSV
            graph: NetworkX graph object
            chain (str): Blockchain ka naam

        Returns:
            dict: Teeno approaches ke scores, comparison table format mein
        """
        # Rule-Based Score
        profile_1 = feature_extractor.get_wallet_summary(wallet_1_csv, wallet_1, chain)
        profile_2 = feature_extractor.get_wallet_summary(wallet_2_csv, wallet_2, chain)
        rule_similarity = similarity_engine.calculate_similarity_score(
            profile_1.to_dict(), profile_2.to_dict()
        )
        rule_score = rule_similarity["overall_similarity_score"]

        # Node2Vec (AI) Score
        embeddings = node2vec_trainer.load_embeddings()
        node2vec_score = 0.0
        if embeddings:
            wallet_1_key = wallet_1.lower()
            wallet_2_key = wallet_2.lower()
            if wallet_1_key in embeddings and wallet_2_key in embeddings:
                ai_result = embedding_similarity.compare_wallets(embeddings, wallet_1, wallet_2)
                # -1 se 1 range ko 0 se 1 mein convert karte hain, taake fair comparison ho
                node2vec_score = (ai_result["ai_similarity"] + 1) / 2

        # Hybrid Score
        rule_result = hybrid_scorer.calculate_rule_score(
            wallet_1_csv, wallet_2_csv, wallet_1, wallet_2, chain
        )
        embedding_score_100 = hybrid_scorer.calculate_embedding_score(wallet_1, wallet_2)
        relationship_result = hybrid_scorer.calculate_relationship_score(graph, wallet_1, wallet_2)
        risk_score = hybrid_scorer.get_risk_score()

        fusion_result = fusion_engine.combine_scores(
            rule_score=rule_result["rule_score"],
            embedding_score=embedding_score_100,
            relationship_score=relationship_result["relationship_score"],
            risk_score=risk_score,
        )
        hybrid_score = fusion_result["final_confidence"] / 100

        return {
            "wallet_1": wallet_1,
            "wallet_2": wallet_2,
            "comparison": [
                {"model": "Rule", "similarity": round(rule_score, 2)},
                {"model": "Node2Vec", "similarity": round(node2vec_score, 2)},
                {"model": "Hybrid", "similarity": round(hybrid_score, 2)},
            ],
        }


# Ek single instance banate hain jo poore project mein import hoga
benchmark_engine = BenchmarkEngine()