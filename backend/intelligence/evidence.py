"""
Evidence Builder

Ye module wallet ke liye "evidence points" banata hai — matlab
concrete proof jo investigator ko dikhaya ja sake, jaise bridge
detection, timing correlation, waghera.
"""

from attribution.bridge_detector import bridge_detector
from attribution.confidence import confidence_calculator


class EvidenceBuilder:
    """
    Ye class raw data se readable "evidence" entries banati hai.
    """

    def build_bridge_evidence(self, transactions: list, chain: str, related_wallet: str = None,
                                time_difference_seconds: int = None, combined_score: float = None) -> list:
        """
        Bridge activity se evidence entries banata hai.

        Args:
            transactions (list): Wallet ki transactions
            chain (str): Blockchain ka naam
            related_wallet (str): Agar kisi doosri wallet se link mila ho
            time_difference_seconds (int): Bridge aur receive ke beech time farq
            combined_score (float): Attribution ka combined score (confidence ke liye)

        Returns:
            list: Evidence entries ki list
        """
        bridge_txs = bridge_detector.detect_bridge_transactions(transactions, chain)

        evidence_list = []

        for index, tx in enumerate(bridge_txs, start=1):
            evidence = {
                "evidence_id": f"Evidence #{index}",
                "type": "Bridge Detected",
                "chain": chain,
                "bridge_name": tx.get("bridge_name"),
                "tx_hash": tx.get("tx_hash"),
            }

            if related_wallet:
                evidence["related_wallet"] = related_wallet

            if time_difference_seconds is not None:
                evidence["time_difference_seconds"] = time_difference_seconds

            if combined_score is not None:
                confidence_label = confidence_calculator.get_confidence_label(combined_score)
                evidence["confidence"] = confidence_label

            evidence_list.append(evidence)

        return evidence_list

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