"""
Transaction Graph Builder

Ye module CSV se transaction data padh ke ek graph banata hai,
jisme har wallet ek node hai aur har transaction ek edge hai.
"""

import networkx as nx
import pandas as pd


class TransactionGraph:
    """
    Ye class CSV transaction data se ek graph banati hai,
    jisme wallets nodes hain aur transactions edges hain.
    """

    def __init__(self):
        """
        Ek khaali directed graph banate hain.
        """
        self.graph = nx.DiGraph()
        self.data = None

    def load_csv(self, file_path: str):
        """
        CSV file se transaction data padhta hai.

        Args:
            file_path (str): CSV file ka path
        """
        self.data = pd.read_csv(file_path)

    def build_graph(self):
        """
        Loaded data se graph banata hai — nodes aur edges add karta hai.

        Raises:
            ValueError: Agar CSV pehle load nahi hui
        """
        if self.data is None:
            raise ValueError("Pehle load_csv() call karo, phir build_graph() call karo")

        for _, row in self.data.iterrows():
            sender = row.get("from_address")
            receiver = row.get("to_address")

            # Agar sender ya receiver missing hai, is row ko skip karo
            if pd.isna(sender) or pd.isna(receiver):
                continue

            # Edge add karo, saath mein transaction ka data bhi attach karo
            self.graph.add_edge(
                sender,
                receiver,
                tx_hash=row.get("tx_hash"),
                value_eth=row.get("value_eth"),
                timestamp=row.get("timestamp"),
                chain=row.get("chain"),
            )

    def get_nodes(self) -> list:
        """
        Graph ke saare nodes (wallets) return karta hai.

        Returns:
            list: Nodes ki list
        """
        return list(self.graph.nodes())

    def get_edges(self) -> list:
        """
        Graph ke saare edges (transactions) return karta hai.

        Returns:
            list: Edges ki list (har edge ek tuple hai: sender, receiver, data)
        """
        return list(self.graph.edges(data=True))

    def save_graph(self, file_path: str):
        """
        Graph ko GraphML file mein save karta hai (future use ke liye,
        jaise Neo4j mein import karna).

        Args:
            file_path (str): Save karne ka path
        """
        nx.write_graphml(self.graph, file_path)

    def graph_statistics(self) -> dict:
        """
        Graph ki statistics calculate karta hai.

        Returns:
            dict: Statistics (nodes, edges, density, etc.)
        """
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()

        if num_nodes == 0:
            return {
                "num_wallets": 0,
                "num_transactions": 0,
                "average_degree": 0,
                "density": 0,
                "connected_components": 0,
            }

        # Average degree = kitne edges average per node hain
        average_degree = sum(dict(self.graph.degree()).values()) / num_nodes

        # Density = graph kitna "bhara hua" hai (0 se 1 ke beech)
        density = nx.density(self.graph)

        # Connected components = graph ke alag-alag "islands" (undirected version mein check karte hain)
        undirected_graph = self.graph.to_undirected()
        connected_components = nx.number_connected_components(undirected_graph)

        return {
            "num_wallets": num_nodes,
            "num_transactions": num_edges,
            "average_degree": round(average_degree, 2),
            "density": round(density, 6),
            "connected_components": connected_components,
        }