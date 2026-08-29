"""
Sprint 18, Day 5 — Wallet Embeddings

Best trained model (Day 4 ka `models/pyg_graphsage_best.pt`) se har
wallet ka embedding generate karta hai, aur 2 wallets compare karne ke
3 tareeqe demonstrate karta hai:

    1. Cosine similarity     -> ek single number (0-1 jaisa score)
    2. |Embedding_A - Embedding_B|  -> element-wise absolute difference
       (vector) — pair classifier ke liye richer input
    3. Embedding_A * Embedding_B    -> element-wise product (vector) —
       pair classifier ke liye richer input

(2) aur (3) sirf ek number nahi dete, balki poora vector — jo agar
future mein ek proper pair-classifier (MLP/Logistic Regression) train
karna ho, to cosine similarity se zyada information carry karte hain
(model khud seekh sakta hai KAUN SI dimensions important hain).
"""

import os
import pickle

import torch
import torch.nn.functional as F

from ai.pyg_graphsage_model import PyGGraphSAGE, classify_pair


MODELS_FOLDER = "models"
EMBEDDINGS_PATH = os.path.join(MODELS_FOLDER, "pyg_wallet_embeddings.pkl")


def load_best_model() -> PyGGraphSAGE:
    """
    Day 4 ka best (early-stopped) checkpoint load karta hai.
    """
    checkpoint = torch.load(
        os.path.join(MODELS_FOLDER, "pyg_graphsage_best.pt"),
        weights_only=False,
    )
    model = PyGGraphSAGE(
        in_dim=checkpoint["in_dim"],
        hidden_dim=checkpoint["hidden_dim"],
        out_dim=checkpoint["out_dim"],
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint


def generate_wallet_embeddings(model: PyGGraphSAGE, x: torch.Tensor,
                                edge_index: torch.Tensor, node_list: list) -> dict:
    """
    Har wallet ka final (L2-normalized) embedding generate karta hai.

    Returns:
        dict: {wallet_address: np.ndarray(embedding_dim,)}
    """
    model.eval()
    with torch.no_grad():
        embeddings = model(x, edge_index, normalize=True)

    return {node: embeddings[i].numpy() for i, node in enumerate(node_list)}


def build_pair_vector(embedding_a: torch.Tensor, embedding_b: torch.Tensor) -> dict:
    """
    Do wallets ke embeddings ko 3 tareeqon se compare karta hai.

    Returns:
        dict: {
            "cosine_similarity": float,
            "abs_diff": np.ndarray (embedding_dim,),
            "elementwise_product": np.ndarray (embedding_dim,),
        }
    """
    cosine_similarity = F.cosine_similarity(
        embedding_a.unsqueeze(0), embedding_b.unsqueeze(0)
    ).item()

    abs_diff = torch.abs(embedding_a - embedding_b)
    elementwise_product = embedding_a * embedding_b

    return {
        "cosine_similarity": round(cosine_similarity, 4),
        "abs_diff": abs_diff.numpy(),
        "elementwise_product": elementwise_product.numpy(),
    }


def save_embeddings(embeddings: dict):
    os.makedirs(MODELS_FOLDER, exist_ok=True)
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(embeddings, f)


def load_embeddings() -> dict:
    with open(EMBEDDINGS_PATH, "rb") as f:
        return pickle.load(f)


def classify_wallet_pair(wallet_1: str, wallet_2: str, threshold: float = 0.5) -> dict:
    """
    Sprint 18 Day 6 — Wallet Pair Classification.

    Do wallets ke saved embeddings (Day 5 se) le kar unhe compare
    karta hai, aur "Related"/"Unrelated" classify karta hai.

    Threshold 0.5 rakha hai (Sprint 17 ke `classify_relation()` jaisa
    hi convention) — taake pichle experiments (Rule, Node2Vec, XGBoost,
    custom GraphSAGE) ke saath comparison consistent rahe.

    Args:
        wallet_1, wallet_2 (str): Wallet addresses
        threshold (float): Is se upar "Related" (default 0.5)

    Returns:
        dict: {"wallet_1": ..., "wallet_2": ..., "score": ..., "classification": ...}

    Raises:
        KeyError: Agar wallet ka embedding maujood nahi (graph mein nahi tha)
    """
    embeddings = load_embeddings()

    wallet_1_lower = wallet_1.lower()
    wallet_2_lower = wallet_2.lower()

    if wallet_1_lower not in embeddings:
        raise KeyError(f"Wallet not found in trained embeddings: {wallet_1}")
    if wallet_2_lower not in embeddings:
        raise KeyError(f"Wallet not found in trained embeddings: {wallet_2}")

    embedding_a = torch.tensor(embeddings[wallet_1_lower])
    embedding_b = torch.tensor(embeddings[wallet_2_lower])

    score = F.cosine_similarity(embedding_a.unsqueeze(0), embedding_b.unsqueeze(0)).item()
    classification = "Related" if score >= threshold else "Unrelated"

    return {
        "wallet_1": wallet_1,
        "wallet_2": wallet_2,
        "score": round(score, 4),
        "classification": classification,
    }


if __name__ == "__main__":
    """
    Run: python -m ai.wallet_embeddings
    """
    from evaluation.ground_truth import get_dataset
    from evaluation.run_graphsage_comparison import build_combined_graph
    from ai.pyg_dataset import build_pyg_dataset
    from torch_geometric.utils import to_undirected

    print("Rebuilding the same combined graph used for training...")
    ground_truth_cases = get_dataset()
    combined_graph_obj = build_combined_graph(ground_truth_cases)

    pyg_data, node_list, node_to_idx = build_pyg_dataset(combined_graph_obj.graph)
    pyg_data.edge_index = to_undirected(pyg_data.edge_index, num_nodes=pyg_data.num_nodes)

    print("Loading best trained model (Day 4 checkpoint)...")
    model, checkpoint = load_best_model()
    print(f"  -> Loaded from epoch {checkpoint['best_epoch']} "
          f"(val loss = {checkpoint['best_val_loss']:.4f})\n")

    embeddings = generate_wallet_embeddings(model, pyg_data.x, pyg_data.edge_index, node_list)
    save_embeddings(embeddings)

    sample_wallet = node_list[0]
    print(f"Wallet: {sample_wallet}")
    print(f"Embedding (first 8 of {len(embeddings[sample_wallet])} dims): "
          f"{embeddings[sample_wallet][:8]}")
    print()

    # --- Pair comparison demo ---
    wallet_a, wallet_b = node_list[0], node_list[1]
    embedding_a = torch.tensor(embeddings[wallet_a])
    embedding_b = torch.tensor(embeddings[wallet_b])

    pair_result = build_pair_vector(embedding_a, embedding_b)

    print(f"Comparing {wallet_a[:12]}... vs {wallet_b[:12]}...")
    print(f"  Cosine similarity: {pair_result['cosine_similarity']}")
    print(f"  |A-B| (first 8 dims): {pair_result['abs_diff'][:8]}")
    print(f"  A*B (first 8 dims):   {pair_result['elementwise_product'][:8]}")
    print()

    print(f"Saved {len(embeddings)} wallet embeddings to {EMBEDDINGS_PATH}")

    # --- Day 6: Wallet Pair Classification demo ---
    print("\n" + "=" * 50)
    print("Day 6 — Wallet Pair Classification")
    print("=" * 50)
    import json

    result = classify_wallet_pair(wallet_a, wallet_b)
    print(json.dumps(result, indent=2))