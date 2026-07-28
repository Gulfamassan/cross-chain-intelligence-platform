"""
Report Builder

Ye module ek wallet ki poori investigation ka data collect karta hai —
saare engines (Intelligence, Risk, AI, Hybrid) se — taake PDF report
banane ke liye ek single, organized data structure mil sake.
"""

from intelligence.intelligence_engine import intelligence_engine
from risk.risk_engine import risk_engine
from ai.node2vec_model import node2vec_trainer


class ReportBuilder:
    """
    Ye class ek wallet ki poori report ke liye zaroori saara data
    collect karti hai, ek jagah organize karke.
    """

    def build_report_data(self, graph, csv_path: str, wallet_address: str, chain: str) -> dict:
        """
        PDF report ke liye zaroori saara data collect karta hai.

        Args:
            graph: NetworkX graph object
            csv_path (str): Wallet transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            dict: Report ke liye poora organized data
        """
        # Joint Intelligence Report (Wallet Summary, Timeline, Recommendation sab isi mein hai)
        intelligence_report = intelligence_engine.generate_report(
            graph, csv_path, wallet_address, chain
        )

        # Risk Analysis
        risk_report = risk_engine.analyze(csv_path, wallet_address, chain)

        # AI Embedding Availability
        embeddings = node2vec_trainer.load_embeddings()
        wallet_key = wallet_address.lower()
        has_embedding = wallet_key in embeddings

        return {
            "wallet_address": wallet_address,
            "chain": chain,
            "wallet_summary": intelligence_report["wallet_summary"],
            "connected_wallets_count": intelligence_report["wallet_summary"]["graph_connections"],
            "risk_analysis": risk_report,
            "has_ai_embedding": has_embedding,
            "summary": intelligence_report["summary"],
            "recommendation": intelligence_report["recommendation"],
            "timeline": intelligence_report["timeline"],
        }


# Ek single instance banate hain jo poore project mein import hoga
report_builder = ReportBuilder()