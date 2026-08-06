"""
Recommendation Engine

Ye module aggregated wallet data dekh kar ek actionable recommendation
deta hai — investigator ko batata hai kya karna chahiye.
"""


class RecommendationEngine:
    """
    Ye class combined intelligence data se recommendation banati hai.
    """

    def generate_recommendation(self, aggregated_data: dict) -> dict:
        """
        Aggregated wallet data dekh kar ek recommendation deta hai.

        Args:
            aggregated_data (dict): IntelligenceAggregator se aaya combined data

        Returns:
            dict: Recommendation label aur reasoning
        """
        connections = aggregated_data.get("graph_connections", 0)
        centrality = aggregated_data.get("centrality_score", 0.0)
        risk_score = aggregated_data.get("risk_score")
        has_ai_embedding = aggregated_data.get("has_ai_embedding", False)

        reasons = []
        priority = "Low Priority"
        
        # Entity classification (Sprint 12/13 addition)
        entity_label = aggregated_data.get("entity_label")
        entity_confidence = aggregated_data.get("entity_confidence", 0)
        if entity_label and entity_label != "Unknown":
            reasons.append(f"Entity classified as {entity_label} ({round(entity_confidence * 100)}% confidence)")
            if entity_label == "Exchange Wallet":
                reasons.append("Exchange wallets carry inherent KYC correlation value")
        # High connectivity ek strong signal hai
        if connections >= 10:
            reasons.append(f"High connectivity detected ({connections} direct connections)")
            priority = "Investigate Further"

        # High centrality matlab ye wallet network ka "hub" hai
        if centrality >= 0.5:
            reasons.append("Wallet appears to be a network hub (high centrality)")
            priority = "Investigate Further"

        # Risk score available hone par (jab Risk Engine banega)
        if risk_score is not None:
            if risk_score >= 70:
                reasons.append(f"High risk score ({risk_score}/100)")
                priority = "High Priority - Investigate Immediately"
            elif risk_score >= 40:
                reasons.append(f"Moderate risk score ({risk_score}/100)")
                if priority == "Low Priority":
                    priority = "Investigate Further"
        else:
            reasons.append("Risk analysis pending (Risk Engine not yet implemented)")

        # AI analysis availability
        if has_ai_embedding:
            reasons.append("AI-based structural analysis available for this wallet")
        else:
            reasons.append("AI embeddings not yet generated for this wallet")

        if not reasons:
            reasons.append("No significant signals detected")

        return {
            "priority": priority,
            "reasons": reasons,
        }


# Ek single instance banate hain jo poore project mein import hoga
recommendation_engine = RecommendationEngine()