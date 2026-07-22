"""
Intelligence Engine

Ye main module hai jo Aggregator, Evidence Builder, aur Summary
Engine — teeno ko combine karke ek complete investigation report
banata hai.
"""

from intelligence.aggregator import intelligence_aggregator
from intelligence.summary import summary_engine


class IntelligenceEngine:
    """
    Ye class ek wallet ki poori investigation report generate karti hai.
    """

    def generate_report(self, graph, csv_path: str, wallet_address: str, chain: str) -> dict:
        """
        Diye gaye wallet ke liye ek complete intelligence report banata hai.

        Args:
            graph: NetworkX graph object
            csv_path (str): Wallet transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            dict: Complete investigation report
        """
        # Step 1: Saare engines se data combine karte hain
        aggregated_data = intelligence_aggregator.aggregate_wallet_data(
            graph, csv_path, wallet_address, chain
        )

        # Step 2: Summary banate hain
        summary = summary_engine.generate_summary(aggregated_data)

        # Step 3: Final report banate hain
        return {
            "wallet": wallet_address,
            "chain": chain,
            "wallet_summary": aggregated_data,
            "summary": summary,
        }


# Ek single instance banate hain jo poore project mein import hoga
intelligence_engine = IntelligenceEngine()