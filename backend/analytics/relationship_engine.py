"""
Relationship Engine

Ye module wallets ke beech relationships analyze karta hai —
direct connections, indirect connections (multi-hop), common
neighbors, aur ek overall relationship score.
"""

import networkx as nx


class RelationshipEngine:
    """
    Ye class graph mein wallets ke beech relationships nikalti hai.
    """

    def find_direct_neighbors(self, graph: nx.DiGraph, wallet: str) -> list:
        """
        Diye gaye wallet ke direct connections (1 step door) deta hai —
        chahe wo wallet ne paisa bheja ho ya liya ho.
        """
        wallet = wallet.lower()

        if wallet not in graph:
            return []

        predecessors = set(graph.predecessors(wallet))
        successors = set(graph.successors(wallet))

        return list(predecessors.union(successors))

    def find_indirect_neighbors(self, graph: nx.DiGraph, wallet: str, depth: int = 2) -> list:
        """
        Diye gaye wallet ke indirect connections deta hai — matlab
        wo wallets jo 2 ya zyada steps door hain (direct neighbors
        ke ilawa).
        """
        wallet = wallet.lower()

        if wallet not in graph:
            return []

        undirected_graph = graph.to_undirected()
        reachable = nx.single_source_shortest_path_length(undirected_graph, wallet, cutoff=depth)

        direct = set(self.find_direct_neighbors(graph, wallet))
        indirect = set(reachable.keys()) - direct - {wallet}

        return list(indirect)

    def common_neighbors(self, graph: nx.DiGraph, wallet1: str, wallet2: str) -> list:
        """
        Do wallets ke common connections deta hai.
        """
        neighbors1 = set(self.find_direct_neighbors(graph, wallet1))
        neighbors2 = set(self.find_direct_neighbors(graph, wallet2))

        return list(neighbors1.intersection(neighbors2))

    def relationship_score(self, graph: nx.DiGraph, wallet1: str, wallet2: str) -> float:
        """
        Do wallets ke beech ek "relationship score" calculate karta hai.
        """
        wallet1 = wallet1.lower()
        wallet2 = wallet2.lower()

        if wallet1 not in graph or wallet2 not in graph:
            return 0.0

        score = 0.0

        direct_neighbors = self.find_direct_neighbors(graph, wallet1)
        if wallet2 in direct_neighbors:
            score += 1.0

        common = self.common_neighbors(graph, wallet1, wallet2)
        score += len(common) * 0.1

        return round(score, 4)


# Ek single instance banate hain jo poore project mein import hoga
relationship_engine = RelationshipEngine()