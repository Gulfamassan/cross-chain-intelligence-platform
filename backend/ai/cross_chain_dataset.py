"""
Sprint 19, Day 2 — Chain-Aware Node Features

Sprint 18 ka 8-feature logic (`ai/pyg_dataset.py`) reuse karta hai,
lekin Sprint 17 Day 6 ke unified cross-chain graph
(`graph/cross_chain_graph.py` — composite `chain:address` nodes,
`MultiDiGraph`, multiple edge-categories) ke liye adapt kiya hai:

    1. Transaction-based features (transaction_count, total_sent, ...)
       SIRF `edge_category == "transaction"` edges se compute hote
       hain — evidence edges (same_address, bridge, known_exchange,
       transfer_linkage) mein `value_eth` nahi hota, unhe "transactions"
       ginna galat hoga.
    2. Message-passing (GraphSAGE ke liye edge_index) mein SAARI
       edge-categories shamil hoti hain — kyunki cross-chain evidence
       edges (jaise same_address) khud important signal hain jo model
       ko dikhna chahiye.
    3. 3-dim one-hot chain encoding add hota hai — final vector
       8 + 3 = 11 dimensions.
"""

import numpy as np
import networkx as nx
import torch
from torch_geometric.data import Data
from torch_geometric.utils import to_undirected

from ai.gnn_dataset import _active_days_for_node

CHAIN_ORDER = ["ethereum", "polygon", "arbitrum"]


def _one_hot_chain(chain: str) -> list:
    """
    Chain naam ko 3-dim one-hot vector mein convert karta hai.
    Na-pehchana chain ke liye saare zeros (koi crash nahi).
    """
    vector = [0.0, 0.0, 0.0]
    chain_lower = (chain or "").lower()
    if chain_lower in CHAIN_ORDER:
        vector[CHAIN_ORDER.index(chain_lower)] = 1.0
    return vector


def build_node_feature_matrix(graph: nx.MultiDiGraph, nodes: list) -> np.ndarray:
    """
    Har node ka 11-dimensional feature vector banata hai:
    8 transaction-based features + 3-dim one-hot chain.

    Args:
        graph: NetworkX MultiDiGraph (unified cross-chain graph)
        nodes: Node order (feature matrix isi order mein banegi)

    Returns:
        np.ndarray: shape (num_nodes, 11)
    """
    feature_rows = []

    for node in nodes:
        # SIRF "transaction" category edges — evidence edges (jinme
        # value_eth nahi hota) ko transaction-stats mein shamil nahi karte
        out_edges = [
            (u, v, d) for u, v, d in graph.out_edges(node, data=True)
            if d.get("edge_category") == "transaction"
        ]
        in_edges = [
            (u, v, d) for u, v, d in graph.in_edges(node, data=True)
            if d.get("edge_category") == "transaction"
        ]

        outgoing_count = len(out_edges)
        incoming_count = len(in_edges)
        transaction_count = outgoing_count + incoming_count

        sent_values = [d.get("value_eth", 0) or 0 for _, _, d in out_edges]
        received_values = [d.get("value_eth", 0) or 0 for _, _, d in in_edges]

        total_sent = float(sum(sent_values))
        total_received = float(sum(received_values))

        all_values = sent_values + received_values
        avg_transaction_value = float(np.mean(all_values)) if all_values else 0.0

        # Counterparties SIRF transaction edges se (evidence edges
        # "counterparty" ka matlab nahi rakhte yahan)
        counterparties = set()
        for u, v, d in out_edges:
            counterparties.add(v)
        for u, v, d in in_edges:
            counterparties.add(u)
        unique_counterparties = len(counterparties)

        active_days = _active_days_for_node(graph, node)
        transaction_frequency = (transaction_count / active_days) if active_days > 0 else 0.0

        # Node ka apna chain attribute (cross_chain_graph.py mein
        # already set hota hai — seedha wahi use karte hain)
        chain = graph.nodes[node].get("chain", "")
        one_hot = _one_hot_chain(chain)

        feature_rows.append([
            transaction_count,
            total_sent,
            total_received,
            avg_transaction_value,
            incoming_count,
            outgoing_count,
            unique_counterparties,
            transaction_frequency,
            *one_hot,
        ])

    return np.array(feature_rows, dtype=np.float32)


def normalize_feature_matrix(x: torch.Tensor) -> torch.Tensor:
    """
    Sprint 18 Day 4 jaisa hi normalization — lekin sirf pehle 8
    columns (transaction-based) par log1p+standardize lagate hain.
    Aakhri 3 columns (one-hot chain) already 0/1 hain — unhe
    normalize karna unka meaning hi kharab kar dega (0/1 encoding
    "categorical identity" hai, "magnitude" nahi).
    """
    matrix = x.numpy().copy()

    transaction_cols = matrix[:, :8]
    chain_cols = matrix[:, 8:]

    transaction_cols = np.log1p(transaction_cols)
    mean = transaction_cols.mean(axis=0)
    std = transaction_cols.std(axis=0)
    std[std == 0] = 1.0
    transaction_cols = (transaction_cols - mean) / std

    matrix = np.concatenate([transaction_cols, chain_cols], axis=1)
    return torch.tensor(matrix, dtype=torch.float32)


def build_pyg_dataset(graph: nx.MultiDiGraph, normalize: bool = True):
    """
    Poora pipeline: unified cross-chain graph -> torch_geometric.data.Data

    Message-passing edges mein SAARI categories shamil hain
    (transaction + same_address + bridge + known_exchange +
    transfer_linkage) — cross-chain evidence khud signal hai.

    Args:
        graph: NetworkX MultiDiGraph (unified cross-chain graph)
        normalize (bool): Features normalize karni hain ya nahi

    Returns:
        (Data, list, dict): PyG Data object, node_list, node_to_idx
    """
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    x_matrix = build_node_feature_matrix(graph, nodes)
    x = torch.tensor(x_matrix, dtype=torch.float32)

    if normalize:
        x = normalize_feature_matrix(x)

    sources, targets = [], []
    for u, v in graph.edges():  # MultiDiGraph.edges() -> saari categories
        if u in node_to_idx and v in node_to_idx:
            sources.append(node_to_idx[u])
            targets.append(node_to_idx[v])

    if sources:
        edge_index = torch.tensor([sources, targets], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    # Sprint 18 Day 3 ka undirected-fix yahan bhi zaroori hai —
    # warna wallets jo sirf "sender" hain unko neighbor info nahi milegi
    edge_index = to_undirected(edge_index, num_nodes=x.shape[0])

    data = Data(x=x, edge_index=edge_index)

    return data, nodes, node_to_idx


if __name__ == "__main__":
    """
    Day 2 sanity check.
    Run: python -m ai.cross_chain_dataset
    """
    import os
    from graph.cross_chain_graph import build_unified_graph

    wallet_chain_csvs = []
    for chain in ["ethereum", "polygon", "arbitrum"]:
        chain_folder = os.path.join("datasets", chain)
        if not os.path.isdir(chain_folder):
            continue
        for filename in os.listdir(chain_folder):
            if filename.endswith(".csv"):
                wallet_chain_csvs.append((os.path.join(chain_folder, filename), chain))

    unified_graph = build_unified_graph(wallet_chain_csvs)
    data, nodes, node_to_idx = build_pyg_dataset(unified_graph)

    print("Chain-aware node features generated\n")
    print("Nodes:", data.num_nodes)
    print("Edges (undirected, message-passing):", data.num_edges)
    print("Features per node:", data.num_node_features)
    print()

    sample_node = nodes[0]
    print(f"Sample node: {sample_node}")
    print(f"Feature vector: {data.x[0].tolist()}")
    print("(last 3 dims = one-hot [ethereum, polygon, arbitrum])")