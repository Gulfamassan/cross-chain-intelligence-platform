"""
Sprint 19, Day 5 — Cross-Chain Wallet Embeddings

Day 4 ka trained model (`models/cross_chain_graphsage_best.pt`) se
har (wallet, chain) ka embedding generate karta hai, aur do wallets
(chahe alag chains pe hon) ke embeddings compare karta hai.

⚠️ IMPORTANT (jaisa Day 5 instructions mein kaha gaya): Embedding
similarity SIRF model ka signal hai — automatically "ye 2 wallets
same entity hain" (ground truth attribution) NAHI hai. High similarity
matlab "model ko structural/behavioral resemblance dikha", isay hamesha
doosre evidence (rule-based, entity-labels, bridge-evidence) ke saath
milakar dekhna chahiye — akele decision nahi lena chahiye.
"""

import os
import pickle

import torch
import torch.nn.functional as F

from ai.pyg_graphsage_model import PyGGraphSAGE
from graph.cross_chain_graph import _node_id


MODELS_FOLDER = "models"
EMBEDDINGS_PATH = os.path.join(MODELS_FOLDER, "cross_chain_wallet_embeddings.pkl")


def load_best_model():
    checkpoint = torch.load(
        os.path.join(MODELS_FOLDER, "cross_chain_graphsage_best.pt"),
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


def generate_cross_chain_embeddings(model: PyGGraphSAGE, x: torch.Tensor,
                                     edge_index: torch.Tensor, node_list: list) -> dict:
    """
    Har (wallet, chain) node ka final embedding generate karta hai.

    Returns:
        dict: {"chain:address": np.ndarray(embedding_dim,)}
    """
    model.eval()
    with torch.no_grad():
        embeddings = model(x, edge_index, normalize=True)

    return {node: embeddings[i].numpy() for i, node in enumerate(node_list)}


def compare_cross_chain_wallets(wallet_1: str, chain_1: str, wallet_2: str, chain_2: str,
                                 embeddings: dict = None) -> dict:
    """
    Do wallets (chahe alag chains pe hon) ke embeddings compare karta hai.

    ⚠️ Return value ka "score" sirf MODEL SIGNAL hai — automatically
    "ye same entity hain" prove nahi karta. Isay doosre evidence
    (rule/entity/bridge) ke saath combine karke dekhna chahiye.

    Args:
        wallet_1, chain_1, wallet_2, chain_2: Wallet addresses aur unke chains
        embeddings (dict, optional): Agar diya na jaye, disk se load hoga

    Returns:
        dict: {"wallet_1", "chain_1", "wallet_2", "chain_2", "cosine_similarity", "note"}

    Raises:
        KeyError: Agar wallet ka embedding maujood nahi
    """
    if embeddings is None:
        embeddings = load_embeddings()

    node_1 = _node_id(wallet_1, chain_1)
    node_2 = _node_id(wallet_2, chain_2)

    if node_1 not in embeddings:
        raise KeyError(f"No embedding found for {node_1}")
    if node_2 not in embeddings:
        raise KeyError(f"No embedding found for {node_2}")

    embedding_a = torch.tensor(embeddings[node_1])
    embedding_b = torch.tensor(embeddings[node_2])

    cosine_similarity = F.cosine_similarity(
        embedding_a.unsqueeze(0), embedding_b.unsqueeze(0)
    ).item()

    return {
        "wallet_1": wallet_1, "chain_1": chain_1,
        "wallet_2": wallet_2, "chain_2": chain_2,
        "cosine_similarity": round(cosine_similarity, 4),
        "note": "Ye sirf model signal hai, ground-truth attribution nahi — "
                "doosre evidence ke saath combine karke interpret karein.",
    }


def save_embeddings(embeddings: dict):
    os.makedirs(MODELS_FOLDER, exist_ok=True)
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(embeddings, f)


def load_embeddings() -> dict:
    with open(EMBEDDINGS_PATH, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    """
    Run: python -m ai.cross_chain_wallet_embeddings
    """
    from graph.cross_chain_graph import build_unified_graph
    from ai.cross_chain_dataset import build_pyg_dataset
    from evaluation.run_cross_chain_graphsage_training import build_wallet_chain_csvs

    print("Rebuilding the same unified graph used for training...")
    wallet_chain_csvs = build_wallet_chain_csvs()
    unified_graph = build_unified_graph(wallet_chain_csvs)

    pyg_data, node_list, node_to_idx = build_pyg_dataset(unified_graph)

    print("Loading best trained cross-chain model (Day 4 checkpoint)...")
    model, checkpoint = load_best_model()
    print(f"  -> Loaded from epoch {checkpoint['best_epoch']} "
          f"(val loss = {checkpoint['best_val_loss']:.4f})\n")

    embeddings = generate_cross_chain_embeddings(model, pyg_data.x, pyg_data.edge_index, node_list)
    save_embeddings(embeddings)
    print(f"Saved {len(embeddings)} cross-chain wallet embeddings to {EMBEDDINGS_PATH}\n")

    # --- Example: Ethereum Wallet A vs Polygon Wallet B ---
    sample_ethereum_node = next((n for n in node_list if n.startswith("ethereum:")), None)
    sample_polygon_node = next((n for n in node_list if n.startswith("polygon:")), None)

    if sample_ethereum_node and sample_polygon_node:
        _, wallet_a = sample_ethereum_node.split(":", 1)
        _, wallet_b = sample_polygon_node.split(":", 1)

        result = compare_cross_chain_wallets(wallet_a, "ethereum", wallet_b, "polygon", embeddings)

        print("Example comparison:")
        print(f"  Ethereum Wallet: {wallet_a}")
        print(f"  Polygon Wallet:  {wallet_b}")
        print(f"  Cosine similarity: {result['cosine_similarity']}")
        print(f"  Note: {result['note']}")