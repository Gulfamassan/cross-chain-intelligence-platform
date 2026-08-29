"""
backend/evaluation/run_pyg_graphsage_training.py

Sprint 18, Day 4 — GraphSAGE Training

Data leakage avoid karne ke liye `torch_geometric.transforms.RandomLinkSplit`
use kiya hai — ye exactly isi problem ke liye PyG ka built-in tool hai:

    - train_data.edge_index -> SIRF training edges (message passing ke liye)
    - val_data.edge_index   -> training edges hi (val ke liye message
                                passing structure same rehti hai — val
                                edges khud message-passing mein NAHI
                                aate, sirf "supervision" (loss/accuracy
                                check) ke liye alag rakhe jate hain)
    - val_data.edge_label_index / edge_label -> held-out positive +
      (auto-generated) negative edges, jo model ne training ke dauran
      KABHI nahi dekhi — isliye validation loss/accuracy genuine hai,
      leaked nahi.

Task: Unsupervised link prediction (kya ye do wallets connected hain?)
— GraphSAGE ka standard training objective, Node2Vec ke skip-gram
jaisa hi concept.

Run from `backend/`: python -m evaluation.run_pyg_graphsage_training
"""

import torch
import torch.nn.functional as F
from torch_geometric.transforms import RandomLinkSplit
from torch_geometric.utils import to_undirected

from ai.pyg_dataset import build_pyg_dataset
from ai.pyg_graphsage_model import PyGGraphSAGE
from evaluation.ground_truth import get_dataset
from evaluation.run_graphsage_comparison import build_combined_graph


def compute_loss_and_accuracy(embeddings: torch.Tensor, edge_label_index: torch.Tensor,
                               edge_label: torch.Tensor):
    """
    Edge (wallet-pair) supervision ke liye BCE loss aur accuracy nikalta hai.

    Args:
        embeddings: (num_nodes, embedding_dim) — model ka output (normalize=False)
        edge_label_index: (2, num_supervision_edges) — kaunse pairs check karne hain
        edge_label: (num_supervision_edges,) — 1 = real edge, 0 = negative sample

    Returns:
        (loss, accuracy)
    """
    src, dst = edge_label_index
    logits = (embeddings[src] * embeddings[dst]).sum(dim=1)  # raw dot-product

    loss = F.binary_cross_entropy_with_logits(logits, edge_label)

    predictions = (torch.sigmoid(logits) >= 0.5).float()
    accuracy = (predictions == edge_label).float().mean().item()

    return loss, accuracy


if __name__ == "__main__":
    print("Building combined graph (Sprint 17 n=7 cases' unique wallets)...")
    ground_truth_cases = get_dataset()
    combined_graph_obj = build_combined_graph(ground_truth_cases)

    pyg_data, node_list, node_to_idx = build_pyg_dataset(combined_graph_obj.graph)
    print(f"  -> Nodes: {pyg_data.num_nodes}, Edges (directed): {pyg_data.num_edges}\n")

    # Undirected banate hain (Day 3 ka fix) — taake har wallet apne
    # saare transaction-partners se info le, chahe sender ho ya receiver
    pyg_data.edge_index = to_undirected(pyg_data.edge_index, num_nodes=pyg_data.num_nodes)

    # --- Train/Val split (data leakage avoid karte hue) ---
    splitter = RandomLinkSplit(
        num_val=0.2,
        num_test=0.0,
        is_undirected=True,
        add_negative_train_samples=True,
        neg_sampling_ratio=1.0,
    )
    train_data, val_data, _ = splitter(pyg_data)

    print(f"Train supervision edges: {train_data.edge_label_index.shape[1]} "
          f"(message-passing edges: {train_data.edge_index.shape[1]})")
    print(f"Val supervision edges:   {val_data.edge_label_index.shape[1]} "
          f"(message-passing edges: {val_data.edge_index.shape[1]})\n")

    # --- Model + optimizer ---
    in_dim = pyg_data.x.shape[1]
    torch.manual_seed(42)
    model = PyGGraphSAGE(in_dim=in_dim, hidden_dim=32, out_dim=64, dropout=0.3)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    NUM_EPOCHS = 50
    PATIENCE = 10  # Itne epochs tak val loss improve na ho to training rok denge

    best_val_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    best_model_state = None

    for epoch in range(1, NUM_EPOCHS + 1):
        # --- Training step ---
        model.train()
        optimizer.zero_grad()

        # Sirf training edges se message passing (val edges kabhi
        # nahi dikhte model ko is step mein — leakage avoid)
        embeddings = model(train_data.x, train_data.edge_index, normalize=False)
        train_loss, train_acc = compute_loss_and_accuracy(
            embeddings, train_data.edge_label_index, train_data.edge_label
        )

        train_loss.backward()
        optimizer.step()

        # --- Validation step ---
        model.eval()
        with torch.no_grad():
            # Message passing structure training edges jaisi hi hai
            # (val edges message-passing mein shamil nahi) — sirf
            # supervision (loss check) held-out edges par hoti hai
            val_embeddings = model(val_data.x, val_data.edge_index, normalize=False)
            val_loss, val_acc = compute_loss_and_accuracy(
                val_embeddings, val_data.edge_label_index, val_data.edge_label
            )

        # --- Early stopping check ---
        if val_loss.item() < best_val_loss:
            best_val_loss = val_loss.item()
            best_epoch = epoch
            epochs_without_improvement = 0
            # Best-so-far model ka state save karte hain (deep copy,
            # taake baad ke epochs isay overwrite na karein)
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

    # Best checkpoint restore + save karte hain — final model wahi hai
    # jo overfitting se pehle tha, na ke jo training ke aakhir mein tha
    model.load_state_dict(best_model_state)
    import os
    os.makedirs("models", exist_ok=True)
    torch.save({
        "state_dict": best_model_state,
        "in_dim": in_dim,
        "hidden_dim": 32,
        "out_dim": 64,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
    }, "models/pyg_graphsage_best.pt")
    print("Best model saved to models/pyg_graphsage_best.pt")