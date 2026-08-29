"""
Sprint 18, Day 1 — Real PyTorch Geometric Setup
Sprint 18, Day 3 — GraphSAGE Architecture (Dropout + Classification added)

Ye module asal `torch_geometric` library use karke ek GraphSAGE model
banata hai (Sprint 17 ke `ai/graphsage_model.py` se alag — wo hamari
apni khud ki, PyG-independent implementation thi; ye asal PyG library
use karta hai).

Feature engineering dobara nahi likhi — Sprint 17 Day 2 ka
`ai/gnn_dataset.py` (`build_gnn_dataset()`) reuse hota hai, sirf uske
output ko asal `torch_geometric.data.Data` object mein wrap karte hain.

Architecture (Day 3):
    Node Features -> SAGEConv -> ReLU -> Dropout -> SAGEConv -> Embedding

Dropout kyun: Sprint 17 mein humein chhote graphs par overfitting/
collapse ka masla mila tha (Day 5-7). Dropout training ke dauran
random neurons ko "band" kar deta hai — model ko chand specific
features par overly-dependent hone se rokta hai, generalization
thodi behtar hoti hai (chhote data ke liye poora fix nahi, lekin
helpful regularization hai).

Classification: `classify_pair()` — Sprint 17 ka `classify_relation()`
concept reuse karta hai (cosine similarity + threshold), do embeddings
ke beech "Related"/"Unrelated" decide karne ke liye.
"""

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from torch_geometric.utils import to_undirected

from ai.gnn_dataset import build_gnn_dataset, GraphData


def to_pyg_data(dataset: GraphData) -> Data:
    edge_index = to_undirected(dataset.edge_index, num_nodes=dataset.x.shape[0])
    return Data(x=dataset.x, edge_index=edge_index, edge_attr=dataset.edge_attr)


class PyGGraphSAGE(torch.nn.Module):
    """
    2-layer GraphSAGE, asal `torch_geometric.nn.SAGEConv` use karke
    (Sprint 17 ke haath-se-likhe SAGELayer ki jagah — ab library khud
    neighbor sampling/aggregation handle karti hai).

    Architecture: SAGEConv -> ReLU -> Dropout -> SAGEConv -> (L2 normalize)
    """

    def __init__(self, in_dim: int, hidden_dim: int = 32, out_dim: int = 64,
                 dropout: float = 0.3):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, out_dim)
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.conv1(x, edge_index)
        h = F.relu(h)
        # Dropout sirf training mode mein active hota hai (self.training flag) —
        # eval/inference ke waqt automatically off ho jata hai (PyTorch default)
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = self.conv2(h, edge_index)
        h = F.normalize(h, p=2, dim=1)
        return h


def classify_pair(embedding_a: torch.Tensor, embedding_b: torch.Tensor,
                   threshold: float = 0.5) -> dict:
    """
    Do wallet embeddings ke beech cosine similarity nikal kar
    "Related"/"Unrelated" classify karta hai (Sprint 17 ka
    `classify_relation()` concept, ab PyG embeddings ke saath).

    Args:
        embedding_a, embedding_b (torch.Tensor): (embedding_dim,) vectors
        threshold (float): Is se upar "Related" (default 0.5)

    Returns:
        dict: {"similarity": float, "relation": "Related"/"Unrelated"}
    """
    similarity = F.cosine_similarity(embedding_a.unsqueeze(0), embedding_b.unsqueeze(0)).item()
    relation = "Related" if similarity >= threshold else "Unrelated"
    return {"similarity": round(similarity, 4), "relation": relation}


if __name__ == "__main__":
    """
    Day 3 sanity check — architecture (Dropout ke saath) + classification.
    Bonus: demonstrate karta hai ke Wallet A ka embedding uske
    neighbors se influence hota hai (neighbor hata kar embedding
    compare karte hain).

    Run: python -m ai.pyg_graphsage_model
    """
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
    torch.manual_seed(42)  # Reproducible weights, taake dono runs comparable hon
    model = PyGGraphSAGE(in_dim=in_dim, hidden_dim=32, out_dim=64)
    model.eval()  # Eval mode -> dropout automatically off (deterministic comparison ke liye)

    with torch.no_grad():
        embeddings = model(pyg_data.x, pyg_data.edge_index)

    print("GraphSAGE forward pass successful")
    print("Embeddings shape:", tuple(embeddings.shape))
    print()

    # --- Classification demo: pehle 2 wallets ke beech ---
    wallet_a_id, wallet_b_id = 0, 1
    result = classify_pair(embeddings[wallet_a_id], embeddings[wallet_b_id])
    print(f"Classification demo — Node {wallet_a_id} vs Node {wallet_b_id}: {result}")
    print()

    # --- Neighbor-influence demo ---
    # Wallet A ka original embedding (poore graph ke saath) vs uska
    # embedding agar uske edges hata diye jayein (isolated node) —
    # farq dikhata hai ke neighbors se information aggregate ho rahi hai
    node_list = dataset.node_list
    wallet_a = node_list[wallet_a_id]
    neighbor_count = graph_obj.graph.degree(wallet_a)

    isolated_edge_index = torch.zeros((2, 0), dtype=torch.long)
    with torch.no_grad():
        embeddings_isolated = model(pyg_data.x, isolated_edge_index)

    diff = torch.norm(embeddings[wallet_a_id] - embeddings_isolated[wallet_a_id]).item()

    print(f"Wallet A ({wallet_a[:10]}...) has {neighbor_count} neighbor(s) in the graph.")
    print(f"Embedding difference (with neighbors vs isolated): {diff:.4f}")
    print("(Non-zero difference confirms: neighbor information IS being aggregated —")
    print(" Wallet A's representation is not based on its own features alone.)")