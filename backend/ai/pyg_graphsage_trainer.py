"""
Sprint 20, Day 1 — Reusable PyG GraphSAGE Trainer

Sprint 18 ke `evaluation/run_pyg_graphsage_training.py` (leakage-free
`RandomLinkSplit` + early stopping) ka EXACT wahi training logic hai,
lekin ek reusable function mein — taake API endpoint isay kisi bhi
graph (`current_graph.graph`, jo `/build-graph` se banta hai) par call
kar sake, bina hardcoded ground-truth dataset ke.
"""

import os

import torch
import torch.nn.functional as F
from torch_geometric.transforms import RandomLinkSplit
from torch_geometric.utils import to_undirected

from ai.pyg_dataset import build_pyg_dataset
from ai.pyg_graphsage_model import PyGGraphSAGE


def _compute_loss_and_accuracy(embeddings, edge_label_index, edge_label):
    src, dst = edge_label_index
    logits = (embeddings[src] * embeddings[dst]).sum(dim=1)
    loss = F.binary_cross_entropy_with_logits(logits, edge_label)
    predictions = (torch.sigmoid(logits) >= 0.5).float()
    accuracy = (predictions == edge_label).float().mean().item()
    return loss, accuracy


def train_pyg_graphsage(graph, checkpoint_path: str = "models/pyg_graphsage_best.pt",
                         num_epochs: int = 50, patience: int = 10) -> dict:
    """
    Sprint 18 Day 4 ka poora training pipeline — kisi bhi NetworkX
    graph par chala sakte hain.

    Args:
        graph: NetworkX (Di)Graph, jisme kam-se-kam kuch edges hon
        checkpoint_path (str): Best model kahan save karna hai
        num_epochs, patience: Training hyperparameters (Sprint 18 defaults)

    Returns:
        dict: {"embeddings": {wallet: np.ndarray}, "best_epoch": int,
               "best_val_loss": float, "num_nodes": int, "num_edges": int}

    Raises:
        ValueError: Agar graph itna chhota hai ke train/val split possible nahi
    """
    pyg_data, node_list, node_to_idx = build_pyg_dataset(graph)

    if pyg_data.num_edges < 4:
        raise ValueError(
            "Graph mein itne kam edges hain (< 4) ke train/val split "
            "possible nahi — pehle bada graph build karein."
        )

    splitter = RandomLinkSplit(
        num_val=0.2, num_test=0.0, is_undirected=True,
        add_negative_train_samples=True, neg_sampling_ratio=1.0,
    )
    train_data, val_data, _ = splitter(pyg_data)

    in_dim = pyg_data.x.shape[1]
    torch.manual_seed(42)
    model = PyGGraphSAGE(in_dim=in_dim, hidden_dim=32, out_dim=64, dropout=0.3)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    best_val_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    best_model_state = None

    for epoch in range(1, num_epochs + 1):
        model.train()
        optimizer.zero_grad()
        embeddings = model(train_data.x, train_data.edge_index, normalize=False)
        train_loss, _ = _compute_loss_and_accuracy(
            embeddings, train_data.edge_label_index, train_data.edge_label
        )
        train_loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_embeddings = model(val_data.x, val_data.edge_index, normalize=False)
            val_loss, _ = _compute_loss_and_accuracy(
                val_embeddings, val_data.edge_label_index, val_data.edge_label
            )

        if val_loss.item() < best_val_loss:
            best_val_loss = val_loss.item()
            best_epoch = epoch
            epochs_without_improvement = 0
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= patience:
            break

    model.load_state_dict(best_model_state)

    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    torch.save({
        "state_dict": best_model_state, "in_dim": in_dim,
        "hidden_dim": 32, "out_dim": 64,
        "best_epoch": best_epoch, "best_val_loss": best_val_loss,
    }, checkpoint_path)

    model.eval()
    with torch.no_grad():
        # Poore (undirected) graph par final embeddings — RandomLinkSplit
        # ke train/val edges nahi, asal poore graph structure se
        full_edge_index = to_undirected(pyg_data.edge_index, num_nodes=pyg_data.num_nodes)
        final_embeddings = model(pyg_data.x, full_edge_index, normalize=True)

    embeddings_dict = {node: final_embeddings[i].numpy() for i, node in enumerate(node_list)}

    return {
        "embeddings": embeddings_dict,
        "best_epoch": best_epoch,
        "best_val_loss": round(best_val_loss, 4),
        "num_nodes": pyg_data.num_nodes,
        "num_edges": pyg_data.num_edges,
    }