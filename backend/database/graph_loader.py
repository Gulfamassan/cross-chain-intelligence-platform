"""
Graph Loader

Ye module humari existing NetworkX graph (jo CSV transactions se banti hai)
ko Neo4j database mein import karta hai — nodes aur relationships dono.
"""

from database.graph_repository import graph_repository


class GraphLoader:
    """
    Ye class NetworkX graph ko Neo4j mein load karti hai.
    """

    def load_graph_to_neo4j(self, graph, chain: str = "ethereum") -> dict:
        """
        Diye gaye NetworkX graph ke saare nodes aur edges Neo4j mein import karta hai.

        Args:
            graph: NetworkX graph object
            chain (str): Blockchain ka naam

        Returns:
            dict: Kitne nodes aur relationships import hue
        """
        # Step 1: Saare wallets (nodes) create karte hain
        for node in graph.nodes():
            graph_repository.create_wallet_node(node, chain)

        # Step 2: Saare transactions (relationships) create karte hain
        for from_address, to_address, data in graph.edges(data=True):
            graph_repository.create_transaction_relationship(
                from_address=from_address,
                to_address=to_address,
                tx_hash=data.get("tx_hash"),
                value_eth=data.get("value_eth"),
                timestamp=data.get("timestamp"),
            )

        return {
            "nodes_imported": graph.number_of_nodes(),
            "relationships_imported": graph.number_of_edges(),
        }


# Ek single instance banate hain jo poore project mein import hoga
graph_loader = GraphLoader()