"""
GNN Dataset Builder (Sprint 17, Day 2)

Ye module NetworkX graph ko ek "PyTorch-Geometric-jaisi" Data structure
mein convert karta hai (x, edge_index, edge_attr) — lekin torch_geometric
library install kiye bina. Hum apni khud ki halki GraphData class use
karte hain, kyunki:

1. Hamara graph chhota hai — PyG ke advanced batching/sampling features
   ki zaroorat nahi.
2. torch_geometric ka Windows install (CUDA/CPU build match) mushkil aur
   fragile hota hai — plain PyTorch tensors se hum wahi cheez khud bana
   sakte hain.

Naming convention PyG jaisi hi rakhi hai (x, edge_index, edge_attr) taake
future mein agar zaroorat pade to real torch_geometric.data.Data mein
switch karna easy ho.
"""

from dataclasses import dataclass, field

import numpy as np
import networkx as nx
import torch
import pandas as pd


# Chain naam ko integer id mein map karte hain (categorical encoding)
CHAIN_ID_MAP = {
    "ethereum": 0,
    "polygon": 1,
    "arbitrum": 2,
}


def _encode_chain(chain_name) -> int:
    """
    Chain ka naam (string) ko integer id mein convert karta hai.
    Na-pehchana/missing chain ke liye -1 deta hai.
    """
    if chain_name is None or (isinstance(chain_name, float) and np.isnan(chain_name)):
        return -1
    return CHAIN_ID_MAP.get(str(chain_name).lower(), -1)


@dataclass
class GraphData:
    """
    PyTorch-Geometric ke Data object jaisi halki class.

    Attributes:
        x (torch.Tensor): (num_nodes, num_node_features) — har node ka feature vector
        edge_index (torch.Tensor): (2, num_edges) — [source_indices, target_indices]
        edge_attr (torch.Tensor): (num_edges, num_edge_features) — har edge ka feature vector
        node_list (list): Index -> wallet_address mapping (order x/adjacency ke saath match karta hai)
        node_to_idx (dict): wallet_address -> index mapping (reverse lookup)
    """
    x: torch.Tensor
    edge_index: torch.Tensor
    edge_attr: torch.Tensor
    node_list: list = field(default_factory=list)
    node_to_idx: dict = field(default_factory=dict)


def _active_days_for_node(graph: nx.DiGraph, node) -> int:
    """
    Node se touch hone wale saare edges (in + out) ke timestamps se,
    kitne alag (unique) calendar days pe activity hui — wo count karta hai.
    """
    timestamps = []
    for _, _, data in graph.out_edges(node, data=True):
        timestamps.append(data.get("timestamp"))
    for _, _, data in graph.in_edges(node, data=True):
        timestamps.append(data.get("timestamp"))

    timestamps = [t for t in timestamps if t is not None and not pd.isna(t)]
    if not timestamps:
        return 0

    # Unix timestamps (seconds) ko dates mein convert karke unique count lete hain
    dates = pd.to_datetime(pd.Series(timestamps), unit="s", errors="coerce").dt.date
    return dates.nunique()


def _dominant_chain_for_node(graph: nx.DiGraph, node) -> int:
    """
    Node ka chain determine karta hai.

    Day 7 update: cross-chain unified graph (`graph/cross_chain_graph.py`)
    mein node par pehle se hi ek authoritative `chain` attribute hota hai
    (kyunki node identity khud `(address, chain)` hai) — agar wo maujood
    hai, seedha wahi use karte hain (zyada reliable, kyunki edges mein
    se infer karne ki zaroorat nahi). Warna (purane single-chain graphs
    ke liye, jahan node par chain attribute nahi hota), purani
    edge-se-infer-karne wali approach fallback ke taur par chalti hai.
    """
    node_attrs = graph.nodes[node]
    if "chain" in node_attrs and node_attrs["chain"] is not None:
        return _encode_chain(node_attrs["chain"])

    chains = []
    for _, _, data in graph.out_edges(node, data=True):
        chains.append(data.get("chain"))
    for _, _, data in graph.in_edges(node, data=True):
        chains.append(data.get("chain"))

    chains = [c for c in chains if c is not None and not (isinstance(c, float) and np.isnan(c))]
    if not chains:
        return -1

    most_common = pd.Series(chains).mode()
    return _encode_chain(most_common[0]) if len(most_common) > 0 else -1


def build_node_feature_matrix(graph: nx.DiGraph, nodes: list) -> np.ndarray:
    """
    Har node ka 7-dimensional feature vector banata hai:
    [transaction_count, total_inflow, total_outflow, average_transaction,
     unique_counterparties, active_days, chain_id]

    Sirf wahi features use kiye hain jo graph se reliably nikalte hain —
    bridge_count aur contract_interactions abhi exclude hain kyunki wo
    poore system mein hardcoded placeholders hain (Day 1 audit mein
    confirm kiya gaya), real data nahi.

    Args:
        graph: NetworkX DiGraph
        nodes: Node order (feature matrix isi order mein banegi)

    Returns:
        np.ndarray: shape (num_nodes, 7)
    """
    feature_rows = []

    for node in nodes:
        out_edges = list(graph.out_edges(node, data=True))
        in_edges = list(graph.in_edges(node, data=True))

        transaction_count = len(out_edges) + len(in_edges)

        outflow_values = [d.get("value_eth", 0) or 0 for _, _, d in out_edges]
        inflow_values = [d.get("value_eth", 0) or 0 for _, _, d in in_edges]

        total_outflow = float(sum(outflow_values))
        total_inflow = float(sum(inflow_values))

        all_values = outflow_values + inflow_values
        average_transaction = float(np.mean(all_values)) if all_values else 0.0

        counterparties = set(graph.predecessors(node)) | set(graph.successors(node))
        unique_counterparties = len(counterparties)

        active_days = _active_days_for_node(graph, node)
        chain_id = _dominant_chain_for_node(graph, node)

        feature_rows.append([
            transaction_count,
            total_inflow,
            total_outflow,
            average_transaction,
            unique_counterparties,
            active_days,
            chain_id,
        ])

    return np.array(feature_rows, dtype=np.float32)


def build_edge_index_and_attr(graph: nx.DiGraph, node_to_idx: dict):
    """
    Graph edges se PyG-style edge_index aur edge_attr banata hai.

    edge_index: (2, num_edges) — row 0 = source node indices, row 1 = target node indices
    edge_attr: (num_edges, 2) — [value_eth, chain_id]

    Args:
        graph: NetworkX DiGraph
        node_to_idx: wallet_address -> index mapping

    Returns:
        (torch.Tensor, torch.Tensor): edge_index, edge_attr
    """
    sources, targets, attrs = [], [], []

    for u, v, data in graph.edges(data=True):
        if u not in node_to_idx or v not in node_to_idx:
            continue
        sources.append(node_to_idx[u])
        targets.append(node_to_idx[v])
        attrs.append([
            float(data.get("value_eth", 0) or 0),
            float(_encode_chain(data.get("chain"))),
        ])

    if not sources:
        # Koi edge nahi — khaali tensors return karo (crash na ho)
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, 2), dtype=torch.float32)
        return edge_index, edge_attr

    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    edge_attr = torch.tensor(attrs, dtype=torch.float32)

    return edge_index, edge_attr


def build_gnn_dataset(graph: nx.DiGraph) -> GraphData:
    """
    Poora pipeline: NetworkX graph -> GraphData (x, edge_index, edge_attr).

    Args:
        graph: NetworkX DiGraph (TransactionGraph.graph)

    Returns:
        GraphData: PyG-jaisi structure, GNN training ke liye ready
    """
    nodes = list(graph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    x_matrix = build_node_feature_matrix(graph, nodes)
    x = torch.tensor(x_matrix, dtype=torch.float32)

    edge_index, edge_attr = build_edge_index_and_attr(graph, node_to_idx)

    return GraphData(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        node_list=nodes,
        node_to_idx=node_to_idx,
    )