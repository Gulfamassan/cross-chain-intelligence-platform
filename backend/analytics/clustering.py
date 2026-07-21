"""
Community Detection (Clustering)

Ye module graph ko alag-alag "clusters" (communities) mein baantta hai —
matlab wo wallets jo aapas mein zyada connected hain, unhe ek group
mein daal deta hai. Louvain algorithm use karta hai.
"""

import networkx as nx
from networkx.algorithms import community


class ClusterAnalyzer:
    """
    Ye class graph mein wallets ko communities/clusters mein baantti hai.
    """

    def detect_communities(self, graph: nx.DiGraph) -> list:
        """
        Louvain algorithm use kar ke graph ko communities mein baantta hai.

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            list: Communities ki list, har community ek set hai wallets ka
                  jaise [{"0xA", "0xB", "0xC"}, {"0xX", "0xY"}]
        """
        # Louvain algorithm undirected graph par kaam karta hai
        undirected_graph = graph.to_undirected()

        if undirected_graph.number_of_nodes() == 0:
            return []

        communities = community.louvain_communities(undirected_graph, seed=42)
        return communities

    def get_wallet_cluster(self, graph: nx.DiGraph, wallet: str) -> str:
        """
        Diye gaye wallet ka cluster naam deta hai (jaise "Cluster-1").

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            wallet (str): Jis wallet ka cluster pata karna hai

        Returns:
            str: Cluster ka naam, ya None agar wallet graph mein na ho
        """
        wallet = wallet.lower()
        communities = self.detect_communities(graph)

        for index, cluster in enumerate(communities):
            if wallet in cluster:
                return f"Cluster-{index + 1}"

        return None

    def get_all_clusters(self, graph: nx.DiGraph) -> dict:
        """
        Saare clusters ek dictionary format mein deta hai, taake
        dekha ja sake har cluster mein kaunsi wallets hain.

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {"Cluster-1": ["0xA", "0xB"], "Cluster-2": [...]}
        """
        communities = self.detect_communities(graph)

        result = {}
        for index, cluster in enumerate(communities):
            cluster_name = f"Cluster-{index + 1}"
            result[cluster_name] = list(cluster)

        return result

    def cluster_statistics(self, graph: nx.DiGraph) -> dict:
        """
        Clusters ki basic statistics deta hai.

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: Total clusters, sabse bara cluster, average cluster size
        """
        communities = self.detect_communities(graph)

        if not communities:
            return {
                "total_clusters": 0,
                "largest_cluster_size": 0,
                "average_cluster_size": 0,
            }

        sizes = [len(cluster) for cluster in communities]

        return {
            "total_clusters": len(communities),
            "largest_cluster_size": max(sizes),
            "average_cluster_size": round(sum(sizes) / len(sizes), 2),
        }


# Ek single instance banate hain jo poore project mein import hoga
cluster_analyzer = ClusterAnalyzer()