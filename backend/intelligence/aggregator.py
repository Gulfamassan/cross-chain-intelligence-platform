"""
Intelligence Aggregator

Ye module har alag engine (Features, Graph, Relationships, AI/Node2Vec,
Risk, Entity Resolution) ka output collect karta hai aur ek single
wallet ke liye saara data ek jagah jama karta hai.
"""

from features.extractor import feature_extractor
from analytics.relationship_engine import relationship_engine
from analytics.clustering import cluster_analyzer
from analytics.centrality import centrality_analyzer
from ai.node2vec_model import node2vec_trainer
from risk.risk_engine import risk_engine
from entity_labeling.label_engine import resolve_entity


class IntelligenceAggregator:
    """
    Ye class saare engines ko call karke ek wallet ka combined
    data snapshot banati hai.
    """

    def aggregate_wallet_data(self, graph, csv_path: str, wallet_address: str, chain: str) -> dict:
        """
        Diye gaye wallet ke liye saare engines se data collect karta hai.

        Args:
            graph: NetworkX graph object (current built graph)
            csv_path (str): Wallet transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            dict: Combined data — transactions, graph connections,
                  cluster, centrality, AI embedding info, risk score,
                  aur ab entity classification bhi
        """
        wallet = wallet_address.lower()

        # Feature Engine se transaction data nikalte hain
        profile = feature_extractor.get_wallet_summary(csv_path, wallet_address, chain)
        profile_data = profile.to_dict()

        # Graph Engine se connections nikalte hain (agar wallet graph mein ho)
        graph_connections = 0
        cluster = None
        centrality_score = 0.0

        if wallet in graph:
            direct = relationship_engine.find_direct_neighbors(graph, wallet)
            graph_connections = len(direct)

            cluster = cluster_analyzer.get_wallet_cluster(graph, wallet)

            all_centrality = centrality_analyzer.analyze_all(graph)
            centrality_score = all_centrality.get(wallet, {}).get("degree", 0.0)

        # AI Engine se embedding availability check karte hain
        embeddings = node2vec_trainer.load_embeddings()
        has_ai_embedding = wallet in embeddings
        embedding_dimension = len(embeddings[wallet]) if has_ai_embedding else 0

        # Risk Engine se score nikalte hain
        risk_result = risk_engine.analyze(csv_path, wallet_address, chain)
        risk_score = risk_result["risk_score"]
        risk_level = risk_result["risk_level"]

        # Sprint 12/13 addition: Entity Resolution — same profile_data
        # reused, no duplicate feature extraction.
        # NOTE: contract-bytecode detection not wired yet, defaults to False.
        entity_result = resolve_entity(wallet_address, profile_data, is_contract=False)

        return {
            "wallet": wallet_address,
            "chain": chain,
            "transactions": profile_data.get("total_transactions", 0),
            "graph_connections": graph_connections,
            "cluster": cluster,
            "centrality_score": centrality_score,
            "has_ai_embedding": has_ai_embedding,
            "embedding_dimension": embedding_dimension,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_sent_eth": profile_data.get("total_sent_eth", 0),
            "total_received_eth": profile_data.get("total_received_eth", 0),
            "unique_contacts": profile_data.get("total_unique_contacts", 0),
            "active_days": profile_data.get("active_days", 0),
            # New fields (Sprint 12/13):
            "entity_label": entity_result["label"],
            "entity_confidence": entity_result["confidence"],
            "entity_evidence": entity_result["reasons"],
            "entity_source": entity_result["source"],
        }


# Ek single instance banate hain jo poore project mein import hoga
intelligence_aggregator = IntelligenceAggregator()