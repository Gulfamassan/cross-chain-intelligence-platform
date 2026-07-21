"""
Centrality Analysis

Ye module graph mein har wallet ki "importance" calculate karta hai,
alag-alag centrality measures use karke.
"""

import networkx as nx


class CentralityAnalyzer:
    """
    Ye class NetworkX graph par centrality calculations karti hai.
    """

    def calculate_degree_centrality(self, graph: nx.DiGraph) -> dict:
        """
        Degree Centrality — kitne connections hain (normalized 0 se 1 ke beech).

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {wallet_address: score}
        """
        return nx.degree_centrality(graph)

    def calculate_betweenness_centrality(self, graph: nx.DiGraph) -> dict:
        """
        Betweenness Centrality — kitni baar ye wallet do dusri wallets
        ke beech ka shortest path banti hai (matlab "bridge" ka kaam karti hai).

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {wallet_address: score}
        """
        return nx.betweenness_centrality(graph)

    def calculate_closeness_centrality(self, graph: nx.DiGraph) -> dict:
        """
        Closeness Centrality — ye wallet baaki saari wallets se
        kitni "close" hai (kam steps mein pahunch sakti hai).

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {wallet_address: score}
        """
        return nx.closeness_centrality(graph)

    def calculate_eigenvector_centrality(self, graph: nx.DiGraph) -> dict:
        """
        Eigenvector Centrality — ye wallet kitni "important" wallets se
        connected hai (sirf count nahi, quality bhi matter karti hai).

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {wallet_address: score}
        """
        try:
            return nx.eigenvector_centrality(graph, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            # Agar graph bohot chhota ya disconnected ho to ye calculation fail ho sakti hai
            return {node: 0.0 for node in graph.nodes()}

    def analyze_all(self, graph: nx.DiGraph) -> dict:
        """
        Saari centrality measures ek saath calculate karta hai aur
        har wallet ke liye ek combined summary deta hai.

        Args:
            graph (nx.DiGraph): Wallet transaction graph

        Returns:
            dict: {wallet_address: {degree, betweenness, closeness, eigenvector}}
        """
        degree = self.calculate_degree_centrality(graph)
        betweenness = self.calculate_betweenness_centrality(graph)
        closeness = self.calculate_closeness_centrality(graph)
        eigenvector = self.calculate_eigenvector_centrality(graph)

        result = {}
        for node in graph.nodes():
            result[node] = {
                "degree": round(degree.get(node, 0), 4),
                "betweenness": round(betweenness.get(node, 0), 4),
                "closeness": round(closeness.get(node, 0), 4),
                "eigenvector": round(eigenvector.get(node, 0), 4),
            }

        return result

    def get_top_wallets(self, graph: nx.DiGraph, metric: str = "degree", top_n: int = 5) -> list:
        """
        Sabse "important" wallets ki list deta hai, diye gaye metric ke hisaab se.

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            metric (str): "degree", "betweenness", "closeness", ya "eigenvector"
            top_n (int): Kitni top wallets chahiye

        Returns:
            list: [(wallet_address, score), ...] — sorted, sabse zyada score pehle
        """
        all_scores = self.analyze_all(graph)

        sorted_wallets = sorted(
            all_scores.items(),
            key=lambda item: item[1].get(metric, 0),
            reverse=True
        )

        return sorted_wallets[:top_n]


# Ek single instance banate hain jo poore project mein import hoga
centrality_analyzer = CentralityAnalyzer()