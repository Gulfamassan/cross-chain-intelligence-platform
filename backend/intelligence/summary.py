"""
Summary Engine

Ye module wallet ke poore data se ek readable, human-friendly
summary banata hai — rule-based templates use karke (future mein
LLM se bhi generate ho sakta hai).
"""


class SummaryEngine:
    """
    Ye class combined wallet data se ek text summary generate karti hai.
    """

    def generate_summary(self, aggregated_data: dict) -> dict:
        """
        Aggregated wallet data se ek readable summary banata hai.

        Args:
            aggregated_data (dict): IntelligenceAggregator se aaya combined data

        Returns:
            dict: Summary points ki list, aur ek combined text summary
        """
        wallet = aggregated_data.get("wallet")
        connections = aggregated_data.get("graph_connections", 0)
        cluster = aggregated_data.get("cluster")
        risk_score = aggregated_data.get("risk_score")

        points = []

        # Connections ke baare mein
        if connections > 0:
            points.append(f"Wallet has interacted with {connections} wallets.")
        else:
            points.append("Wallet has no detected connections in the current graph.")

        # Cluster ke baare mein
        if cluster:
            points.append(f"Likely belongs to {cluster}.")

        # Risk score ke baare mein (agar available ho)
        if risk_score is not None:
            points.append(f"Risk Score: {risk_score}/100")
        else:
            points.append("Risk Score: Not yet calculated (Risk Engine pending).")

        # Activity ke baare mein
        active_days = aggregated_data.get("active_days", 0)
        transactions = aggregated_data.get("transactions", 0)
        if active_days > 0:
            points.append(f"Active across {active_days} days with {transactions} total transactions.")

        text_summary = " ".join(points)

        return {
            "wallet": wallet,
            "summary_points": points,
            "text_summary": text_summary,
        }


# Ek single instance banate hain jo poore project mein import hoga
summary_engine = SummaryEngine()