"""
Sprint 18, Day 1 — Real PyTorch Geometric Setup

Ye module asal `torch_geometric` library use karke ek GraphSAGE model
banata hai (Sprint 17 ke `ai/graphsage_model.py` se alag — wo hamari
apni khud ki, PyG-independent implementation thi; ye asal PyG library
use karta hai).

Feature engineering dobara nahi likhi — Sprint 17 Day 2 ka
`ai/gnn_dataset.py` (`build_gnn_dataset()`) reuse hota hai, sirf uske
output ko asal `torch_geometric.data.Data` object mein wrap karte hain.
"""

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv

from ai.gnn_dataset import build_gnn_dataset, GraphData


def to_pyg_data(dataset: GraphData) -> Data:
    """
    Hamari Sprint 17 `GraphData` (x, edge_index, edge_attr — humne
    khud banayi thi, PyG jaisi naming ke saath) ko asal
    `torch_geometric.data.Data` object mein convert karta hai.

    Args:
        dataset (GraphData): `build_gnn_dataset()` ka output

    Returns:
        torch_geometric.data.Data: Asal PyG object, GraphSAGE ke
            forward pass ke liye ready
    """
    return Data(x=dataset.x, edge_index=dataset.edge_index, edge_attr=dataset.edge_attr)


class PyGGraphSAGE(torch.nn.Module):
    """
    2-layer GraphSAGE, asal `torch_geometric.nn.SAGEConv` use karke
    (Sprint 17 ke haath-se-likhe SAGELayer ki jagah — ab library khud
    neighbor sampling/aggregation handle karti hai).
    """

    def __init__(self, in_dim: int, hidden_dim: int = 32, out_dim: int = 64):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.leaky_relu(h, negative_slope=0.1)
        h = self.conv2(h, edge_index)
        h = F.normalize(h, p=2, dim=1)
        return h


if __name__ == "__main__":
    """
    Day 1 sanity check — SIRF forward pass, koi training nahi.
    Run: python -m ai.pyg_graphsage_model
    """
    import torch_geometric
    import networkx
    import sklearn
    import pandas
    import numpy

    print("PyTorch version:", torch.__version__)
    print("PyG version:", torch_geometric.__version__)
    print("NetworkX version:", networkx.__version__)
    print("scikit-learn version:", sklearn.__version__)
    print("pandas version:", pandas.__version__)
    print("numpy version:", numpy.__version__)
    print()

    from graph.builder import TransactionGraph

    graph_obj = TransactionGraph()
    graph_obj.load_csv("datasets/polygon/0x71660c4005ba85c37ccec55d0c4493e66fe775d3.csv")
    graph_obj.build_graph()

    print("Graph created successfully")
    print("Nodes:", graph_obj.graph.number_of_nodes())
    print("Edges:", graph_obj.graph.number_of_edges())
    print()

    dataset = build_gnn_dataset(graph_obj.graph)
    pyg_data = to_pyg_data(dataset)

    in_dim = pyg_data.x.shape[1]
    model = PyGGraphSAGE(in_dim=in_dim, hidden_dim=32, out_dim=64)

    with torch.no_grad():
        embeddings = model(pyg_data.x, pyg_data.edge_index)

    print("GraphSAGE forward pass successful")
    print("Embeddings shape:", tuple(embeddings.shape))