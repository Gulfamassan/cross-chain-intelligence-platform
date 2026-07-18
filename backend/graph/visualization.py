"""
Graph Visualization

Ye module NetworkX graph ko PyVis ke zariye ek interactive
HTML file mein convert karta hai, jo browser mein khulti hai.
"""

from pyvis.network import Network
import networkx as nx


class GraphVisualizer:
    """
    Ye class NetworkX graph ko interactive HTML visualization mein convert karti hai.
    """

    def visualize(self, graph: nx.DiGraph, output_path: str = "wallet_graph.html"):
        """
        Diye gaye graph ko interactive HTML file mein save karta hai.

        Args:
            graph (nx.DiGraph): NetworkX graph jo visualize karna hai
            output_path (str): Output HTML file ka path

        Returns:
            str: Saved HTML file ka path
        """
        # PyVis network banate hain — directed graph, dark background, white text
        net = Network(
            height="800px",
            width="100%",
            directed=True,
            bgcolor="#222222",
            font_color="white",
        )

        # NetworkX graph ko PyVis network mein convert karte hain
        net.from_nx(graph)

        # Physics enable karte hain taake graph khud-ba-khud sahi tarike se arrange ho
        net.show_buttons(filter_=["physics"])

        # HTML file mein save karte hain
        net.write_html(output_path)

        return output_path


# Ek single instance banate hain jo poore project mein import hoga
graph_visualizer = GraphVisualizer()