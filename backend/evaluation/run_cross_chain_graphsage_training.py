"""
backend/evaluation/run_cross_chain_graphsage_training.py

Sprint 19, Day 4 — GraphSAGE on Unified Cross-Chain Graph

Sprint 18 ka training methodology (leakage-free `RandomLinkSplit`,
early stopping) HUBAHU preserve kiya hai — sirf data source badla hai:

    Sprint 18: build_combined_graph() -> address-only nodes,
               8-dim features, sirf transaction edges
    Sprint 19: build_unified_graph() -> chain:address composite nodes,
               11-dim chain-aware features, transaction + same_address +
               known_exchange edges sab message-passing mein shamil

Sprint 18 ka trained model (`models/pyg_graphsage_best.pt`) is se
BILKUL UNTOUCHED hai — naya checkpoint alag naam se save hota hai
(`models/cross_chain_graphsage_best.pt`).

Run from `backend/`: python -m evaluation.run_cross_chain_graphsage_training
"""

import os

import torch
import torch.nn.functional as F
from torch_geometric.transforms import RandomLinkSplit

from graph.cross_chain_graph import build_unified_graph
from ai.cross_chain_dataset import build_pyg_dataset
from ai.pyg_graphsage_model import PyGGraphSAGE


def compute_loss_and_accuracy(embeddings: torch.Tensor, edge_label_index: torch.Tensor,
                               edge_label: torch.Tensor):
    src, dst = edge_label_index
    logits = (embeddings[src] * embeddings[dst]).sum(dim=1)
    loss = F.binary_cross_entropy_with_logits(logits, edge_label)
    predictions = (torch.sigmoid(logits) >= 0.5).float()
    accuracy = (predictions == edge_label).float().mean().item()
    return loss, accuracy


def build_wallet_chain_csvs() -> list:
    wallet_chain_csvs = []
    for chain in ["ethereum", "polygon", "arbitrum"]:
        folder = os.path.join("datasets", chain)
        if not os.path.isdir(folder):
            continue
        for filename in os.listdir(folder):
            if filename.endswith(".csv"):
                wallet_chain_csvs.append((os.path.join(folder, filename), chain))
    return wallet_chain_csvs


if __name__ == "__main__":
    print("Building unified cross-chain graph...")
    wallet_chain_csvs = build_wallet_chain_csvs()
    unified_graph = build_unified_graph(wallet_chain_csvs)
    print(f"  -> Nodes: {unified_graph.number_of_nodes()}, "
          f"Edges: {unified_graph.number_of_edges()}\n")

    pyg_data, node_list, node_to_idx = build_pyg_dataset(unified_graph)
    print(f"Chain-aware features: {pyg_data.num_node_features} dims per node")
    print(f"Message-passing edges (undirected, all evidence types): {pyg_data.num_edges}\n")

    splitter = RandomLinkSplit(
        num_val=0.2,
        num_test=0.0,
        is_undirected=True,
        add_negative_train_samples=True,
        neg_sampling_ratio=1.0,
    )
    train_data, val_data, _ = splitter(pyg_data)

    print(f"Train supervision edges: {train_data.edge_label_index.shape[1]}")
    print(f"Val supervision edges:   {val_data.edge_label_index.shape[1]}\n")

    in_dim = pyg_data.x.shape[1]
    torch.manual_seed(42)
    model = PyGGraphSAGE(in_dim=in_dim, hidden_dim=32, out_dim=64, dropout=0.3)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    NUM_EPOCHS = 50
    PATIENCE = 10

    best_val_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    best_model_state = None

    for epoch in range(1, NUM_EPOCHS + 1):
        model.train()
        optimizer.zero_grad()

        embeddings = model(train_data.x, train_data.edge_index, normalize=False)
        train_loss, train_acc = compute_loss_and_accuracy(
            embeddings, train_data.edge_label_index, train_data.edge_label
        )
        train_loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            val_embeddings = model(val_data.x, val_data.edge_index, normalize=False)
            val_loss, val_acc = compute_loss_and_accuracy(
                val_embeddings, val_data.edge_label_index, val_data.edge_label
            )

        if val_loss.item() < best_val_loss:
            best_val_loss = val_loss.item()
            best_epoch = epoch
            epochs_without_improvement = 0
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            epochs_without_improvement += 1

        if epoch == 1 or epoch % 10 == 0:
            marker = " <- best so far" if epoch == best_epoch else ""
            print(f"Epoch {epoch:<4} Train Loss: {train_loss.item():.4f}  "
                  f"Val Loss: {val_loss.item():.4f}  "
                  f"Train Acc: {train_acc:.4f}  Val Acc: {val_acc:.4f}{marker}")

        if epochs_without_improvement >= PATIENCE:
            print(f"\nEarly stopping at epoch {epoch} — val loss "
                  f"{PATIENCE} epochs se improve nahi hui.")
            break

    print(f"\nTraining complete. Best epoch: {best_epoch} (val loss = {best_val_loss:.4f})")

    model.load_state_dict(best_model_state)
    os.makedirs("models", exist_ok=True)
    torch.save({
        "state_dict": best_model_state,
        "in_dim": in_dim,
        "hidden_dim": 32,
        "out_dim": 64,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
    }, "models/cross_chain_graphsage_best.pt")
    print("Best model saved to models/cross_chain_graphsage_best.pt")
    print("(Sprint 18's models/pyg_graphsage_best.pt is untouched.)")