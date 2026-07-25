"""
Evidence Builder

Ye module attribution ke liye "evidence points" banata hai — matlab
concrete proof jo investigator ko dikhaya ja sake, taake wo samajh
sake final confidence score kyun aaya.
"""

from attribution.bridge_detector import bridge_detector
from attribution.confidence import confidence_calculator


class EvidenceBuilder:
    """
    Ye class raw data se readable "evidence" entries banati hai.
    """

    def build_attribution_evidence(
        self,
        bridge_detected: bool = False,
        bridge_name: str = None,
        amount_match: bool = False,
        timing_match: bool = False,
        rule_score: float = 0,
        embedding_score: float = 0,
        relationship_score: float = 0,
        common_neighbors_count: int = 0,
        final_confidence: float = 0,
    ) -> list:
        """
        Do wallets ke attribution ke liye evidence chain banata hai —
        step by step, jaisa investigator dekhna chahta hai.

        Args:
            bridge_detected (bool): Kya bridge activity mili
            bridge_name (str): Konsa bridge use hua
            amount_match (bool): Kya transaction amount match karta hai
            timing_match (bool): Kya timing match karti hai
            rule_score (float): Rule-based score
            embedding_score (float): AI embedding score
            relationship_score (float): Graph relationship score
            common_neighbors_count (int): Kitne common neighbors hain
            final_confidence (float): Final combined confidence score

        Returns:
            list: Evidence chain, har entry ek step hai
        """
        evidence_chain = []

        if bridge_detected:
            label = f"Bridge detected ({bridge_name})" if bridge_name else "Bridge detected"
            evidence_chain.append({"step": "Bridge Detection", "finding": label})

        if amount_match:
            evidence_chain.append({"step": "Amount Analysis", "finding": "Same/similar transaction amount"})

        if timing_match:
            evidence_chain.append({"step": "Timing Analysis", "finding": "Same/similar transaction timing"})

        if embedding_score >= 70:
            evidence_chain.append({
                "step": "Graph Similarity",
                "finding": f"High graph similarity (embedding score: {embedding_score})"
            })
        elif embedding_score >= 40:
            evidence_chain.append({
                "step": "Graph Similarity",
                "finding": f"Moderate graph similarity (embedding score: {embedding_score})"
            })

        if common_neighbors_count > 0:
            evidence_chain.append({
                "step": "Network Overlap",
                "finding": f"{common_neighbors_count} common neighbors found"
            })

        if rule_score >= 70:
            evidence_chain.append({
                "step": "Rule-Based Signals",
                "finding": f"Strong rule-based evidence (score: {rule_score})"
            })

        confidence_label = confidence_calculator.get_confidence_label(final_confidence)
        evidence_chain.append({
            "step": "Final Confidence",
            "finding": f"{final_confidence}% ({confidence_label} confidence)"
        })

        return evidence_chain

    def build_relationship_evidence(self, direct_connections: int, cluster: str) -> dict:
        """
        Graph relationships se ek evidence entry banata hai.

        Args:
            direct_connections (int): Kitne direct connections hain
            cluster (str): Wallet ka cluster naam

        Returns:
            dict: Ek evidence entry
        """
        return {
            "type": "Network Analysis",
            "detail": f"Wallet has {direct_connections} direct connections and belongs to {cluster}",
        }


# Ek single instance banate hain jo poore project mein import hoga
evidence_builder = EvidenceBuilder()