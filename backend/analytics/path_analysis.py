"""
Shortest Path Analysis

Ye module do wallets ke beech connection ka raasta (path) dhoondta hai —
agar wo directly connected na bhi hon, to bhi dikhata hai ke paisa
kin-kin wallets se ho kar guzra.
"""

import networkx as nx


class PathAnalyzer:
    """
    Ye class graph mein do wallets ke beech paths dhoondti hai.
    """

    def find_shortest_path(self, graph: nx.DiGraph, source: str, target: str) -> list:
        """
        Do wallets ke beech sabse chota (shortest) path dhoondta hai.

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            source (str): Shuru wali wallet
            target (str): Aakhri wali wallet

        Returns:
            list: Path (wallets ki list, shuru se aakhir tak),
                  ya khaali list agar koi connection na ho
        """
        source = source.lower()
        target = target.lower()

        if source not in graph or target not in graph:
            return []

        try:
            path = nx.shortest_path(graph, source=source, target=target)
            return path
        except nx.NetworkXNoPath:
            # Koi path exist nahi karta in dono wallets ke beech
            return []

    def find_shortest_path_undirected(self, graph: nx.DiGraph, source: str, target: str) -> list:
        """
        Same jaisa upar wala function, lekin direction ignore karta hai —
        matlab agar A ne Z ko paisa na bheja ho, lekin Z ne A ko bheja ho
        (ulta direction), phir bhi path mil jayega.

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            source (str): Shuru wali wallet
            target (str): Aakhri wali wallet

        Returns:
            list: Path (wallets ki list)
        """
        source = source.lower()
        target = target.lower()

        undirected_graph = graph.to_undirected()

        if source not in undirected_graph or target not in undirected_graph:
            return []

        try:
            path = nx.shortest_path(undirected_graph, source=source, target=target)
            return path
        except nx.NetworkXNoPath:
            return []

    def are_connected(self, graph: nx.DiGraph, wallet1: str, wallet2: str) -> bool:
        """
        Check karta hai ke do wallets ka koi bhi connection hai ya nahi
        (chahe kitne bhi steps door ho, direction ignore karke).

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            wallet1 (str): Pehli wallet
            wallet2 (str): Dusri wallet

        Returns:
            bool: True agar connected hain, warna False
        """
        path = self.find_shortest_path_undirected(graph, wallet1, wallet2)
        return len(path) > 0

    def get_path_details(self, graph: nx.DiGraph, source: str, target: str) -> dict:
        """
        Path ke saath extra details bhi deta hai — kitne "hops" (steps)
        hain, aur har transaction ka data.

        Args:
            graph (nx.DiGraph): Wallet transaction graph
            source (str): Shuru wali wallet
            target (str): Aakhri wali wallet

        Returns:
            dict: Path, hops count, aur transaction details har step ki
        """
        path = self.find_shortest_path_undirected(graph, source, target)

        if not path:
            return {
                "connected": False,
                "path": [],
                "hops": 0,
                "transactions": [],
            }

        # Har consecutive pair ke beech transaction data nikalte hain
        transactions = []
        for i in range(len(path) - 1):
            wallet_a = path[i]
            wallet_b = path[i + 1]

            # Edge data check karte hain dono directions mein
            if graph.has_edge(wallet_a, wallet_b):
                edge_data = graph.get_edge_data(wallet_a, wallet_b)
            elif graph.has_edge(wallet_b, wallet_a):
                edge_data = graph.get_edge_data(wallet_b, wallet_a)
            else:
                edge_data = {}

            transactions.append({
                "from": wallet_a,
                "to": wallet_b,
                "tx_hash": edge_data.get("tx_hash"),
                "value_eth": edge_data.get("value_eth"),
            })

        return {
            "connected": True,
            "path": path,
            "hops": len(path) - 1,
            "transactions": transactions,
        }


# Ek single instance banate hain jo poore project mein import hoga
path_analyzer = PathAnalyzer()