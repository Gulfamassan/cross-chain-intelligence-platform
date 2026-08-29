"""
Sprint 18, Day 2 — Graph Dataset Preparation (PyG format)
Sprint 18, Day 4 fix — Feature normalization added

Ye module NetworkX graph ko asal `torch_geometric.data.Data` object
mein convert karta hai, 8 node features ke saath:

    transaction_count, total_sent, total_received,
    avg_transaction_value, incoming_count, outgoing_count,
    unique_counterparties, transaction_frequency

Sprint 17 ka `_active_days_for_node()` helper reuse kiya hai
(`ai/gnn_dataset.py` se) — dobara nahi likha.

Day 4 fix: Training ke dauran loss astronomically high (~2977) aa raha
tha aur accuracy unstable thi — root cause ye tha ke raw features
(jaise total_sent, jo bade/unbounded numbers hote hain) bina normalize
kiye seedha model mein ja rahe the, jisse gradients explode ho rahe
the. Sprint 17 Day 7 mein humne yehi masla GraphSAGE ke custom
implementation mein fix kiya tha — ab yahan bhi same fix (log1p +
standardize) apply kar rahe hain. Saari 8 features non-negative hain
(Sprint 17 ke chain_id jaisa koi negative value nahi), isliye log1p
seedha sab columns par safely chal sakta hai.
"""

import numpy as np
import networkx as nx
import torch
from torch_geometric.data import Data

from ai.gnn_dataset import _active_days_for_node


def build_node_feature_matrix(graph: nx.DiGraph, nodes: list) -> np.ndarray:
    """
    Har node ka 8-dimensional feature vector banata hai.

    Args:
        graph: NetworkX DiGraph
        nodes: Node order (feature matrix isi order mein banegi)

    Returns:
        np.ndarray: shape (num_nodes, 8)
    """
    feature_rows = []

    for node in nodes:
        out_edges = list(graph.out_edges(node, data=True))
        in_edges = list(graph.in_edges(node, data=True))

        outgoing_count = len(out_edges)
        incoming_count = len(in_edges)
        transaction_count = outgoing_count + incoming_count

        sent_values = [d.get("value_eth", 0) or 0 for _, _, d in out_edges]
        received_values = [d.get("value_eth", 0) or 0 for _, _, d in in_edges]

        total_sent = float(sum(sent_values))
        total_received = float(sum(received_values))

        all_values = sent_values + received_values
        avg_transaction_value = float(np.mean(all_values)) if all_values else 0.0

        counterparties = set(graph.predecessors(node)) | set(graph.successors(node))
        unique_counterparties = len(counterparties)

        active_days = _active_days_for_node(graph, node)
        # Din ke hisaab se average kitni transactions hoti hain — agar
        # active_days 0 hai (koi timestamp nahi mila), 0 return karte hain
        transaction_frequency = (transaction_count / active_days) if active_days > 0 else 0.0

        feature_rows.append([
            transaction_count,
            total_sent,
            total_received,
            avg_transaction_value,
            incoming_count,
            outgoing_count,
            unique_counterparties,
            transaction_frequency,
        ])

    return np.array(feature_rows, dtype=np.float32)


def normalize_feature_matrix(x: torch.Tensor) -> torch.Tensor:
    """
    Feature matrix ko training ke liye normalize karta hai (log1p +
    standardize). Saari 8 features non-negative hain, isliye log1p
    seedha sab columns par safely lagta hai (Sprint 17 Day 7 jaisa
    chain_id ka negative-value special-case yahan zaroori nahi).

    Args:
        x (torch.Tensor): (num_nodes, 8) raw feature matrix

    Returns:
        torch.Tensor: (num_nodes, 8) normalized feature matrix
    """
    matrix = x.numpy().copy()
    matrix = np.log1p(matrix)

    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0  # divide-by-zero se bachne ke liye

    matrix = (matrix - mean) / std

    return torch.tensor(matrix, dtype=torch.float32)


def build_pyg_dataset(graph: nx.DiGraph, normalize: bool = True):
    """
    Poora pipeline: NetworkX graph -> torch_geometric.data.Data

    Args:
        graph: NetworkX DiGraph
        normalize (bool): Features normalize karni hain ya nahi
            (default True — training ke liye zaroori hai; False
            sirf raw-inspection/debugging ke liye useful hai)

    Returns:
        (Data, list, dict): PyG Data object, node_list (index -> address),
            node_to_idx (address -> index)
    """
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    x_matrix = build_node_feature_matrix(graph, nodes)
    x = torch.tensor(x_matrix, dtype=torch.float32)

    if normalize:
        x = normalize_feature_matrix(x)

    sources, targets = [], []
    for u, v in graph.edges():
        if u in node_to_idx and v in node_to_idx:
            sources.append(node_to_idx[u])
            targets.append(node_to_idx[v])

    if sources:
        edge_index = torch.tensor([sources, targets], dtype=torch.long)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    data = Data(x=x, edge_index=edge_index)

    return data, nodes, node_to_idx


if __name__ == "__main__":
    """
    Day 2 sanity check — bade combined dataset (Sprint 17 ke n=7 cases
    ke saare unique wallets) par chalate hain, taake realistic
    node/edge counts dikhein.

    Run: python -m ai.pyg_dataset
    """
    from evaluation.ground_truth import get_dataset
    from evaluation.run_graphsage_comparison import build_combined_graph

    ground_truth_cases = get_dataset()
    combined_graph_obj = build_combined_graph(ground_truth_cases)

    data, nodes, node_to_idx = build_pyg_dataset(combined_graph_obj.graph)

    print("Nodes:", data.num_nodes)
    print("Edges:", data.num_edges)
    print("Features per node:", data.num_node_features)