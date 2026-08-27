"""
GraphSAGE Model (Sprint 17)

Ye module NetworkX graph se GraphSAGE algorithm use karke
har wallet ke liye ek numeric vector (embedding) train karta hai.

Node2Vec sirf random walks (graph structure) use karta hai, lekin
GraphSAGE har node ke initial "features" ko uske neighbors ke
features ke saath aggregate karta hai — isliye ye inductive hai
(naye, pehle na dekhe gaye nodes pe bhi kaam kar sakta hai).
"""

import os
import pickle

import numpy as np
import networkx as nx
import torch
import torch.nn as nn
import torch.nn.functional as F

from performance.timer import performance_timer
from ai.gnn_dataset import build_gnn_dataset


def normalize_feature_matrix(x: torch.Tensor) -> torch.Tensor:
    """
    Feature matrix ko training ke liye normalize karta hai.

    Node features (`ai/gnn_dataset.py` se aate hain) mein `chain_id`
    jaisa ek column hai jo **negative bhi ho sakta hai** (-1 = unknown
    chain), isliye purani `log1p`-based approach yahan nahi chal sakti
    (log1p negative numbers pe crash karta hai). Isliye:

    - Columns 0-5 (transaction_count, inflow, outflow, avg_transaction,
      unique_counterparties, active_days) — sab non-negative hain,
      unhe log1p (skew kam karne ke liye) + standardize karte hain.
    - Column 6 (chain_id) — sirf standardize karte hain (log1p nahi,
      kyunki -1/0/1/2 already chhoti range mein hai).

    Args:
        x (torch.Tensor): (num_nodes, 7) raw feature matrix

    Returns:
        torch.Tensor: (num_nodes, 7) normalized feature matrix
    """
    matrix = x.numpy().copy()

    # Columns 0-5: non-negative, skewed values -> log1p
    matrix[:, :6] = np.log1p(matrix[:, :6])

    # Sab columns standardize karo: (x - mean) / std
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0  # divide-by-zero se bachne ke liye

    matrix = (matrix - mean) / std

    return torch.tensor(matrix, dtype=torch.float32)


def classify_relation(similarity_score: float, threshold: float = 0.5) -> str:
    """
    Day 3 baseline classification: similarity score ko "Related" /
    "Unrelated" label mein convert karta hai.

    Ye ek simple, adjustable threshold hai (baseline ke liye) — future
    sprints mein isay data-driven (ROC curve se optimal threshold nikal
    ke) improve kiya ja sakta hai.

    Args:
        similarity_score (float): Cosine similarity (-1 se 1 ke beech)
        threshold (float): Is se upar "Related" (default 0.5)

    Returns:
        str: "Related" ya "Unrelated"
    """
    return "Related" if similarity_score >= threshold else "Unrelated"


class SAGELayer(nn.Module):
    """
    Ek single GraphSAGE layer.

    Har node apne "self" features ko apne neighbors ke (mean-aggregated)
    features ke saath concatenate karta hai, phir ek linear transform +
    non-linearity apply karta hai. Ye Node2Vec se bunyadi farq hai —
    Node2Vec sirf graph structure (random walks) dekhta hai, GraphSAGE
    actual node features ko neighbors ke saath "mix" karta hai.

    Day 7 fix (embedding collapse bug, Sprint 17 Day 5 finding):
    Pehle har layer `ReLU` + `L2-normalize` dono use karta tha. Chhote
    graphs par ReLU "dead neurons" bana deta tha (poora vector negative
    -> poora vector zero), aur har intermediate layer par normalize
    karne se ye zero-vectors aur bhi jaldi collapse ho jate the — jis
    se saare-ke-saare embeddings ya to identical (score=1.0) ya zero
    (score=0.0) ban rahe the. Fix:
      - `LeakyReLU` (ReLU ki jagah) — negative values ko poora zero
        nahi karta, sirf chhota kar deta hai, isliye "dead" nahi hota.
      - Normalize sirf FINAL layer par (`normalize=True` flag) —
        intermediate layers raw scale mein rehte hain, taake unka
        signal collapse na ho.
    """

    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.linear = nn.Linear(in_dim * 2, out_dim)
        self.activation = nn.LeakyReLU(negative_slope=0.1)

    def forward(self, self_feats: torch.Tensor, neigh_feats: torch.Tensor,
                normalize: bool = False) -> torch.Tensor:
        combined = torch.cat([self_feats, neigh_feats], dim=1)
        out = self.linear(combined)
        out = self.activation(out)

        if normalize:
            # Sirf final layer par L2 normalize karte hain — cosine
            # similarity comparison ke liye zaroori hai, lekin
            # intermediate layers ko is se bachate hain (collapse fix)
            out = F.normalize(out, p=2, dim=1)

        return out


class GraphSAGENet(nn.Module):
    """
    2-layer GraphSAGE encoder (jaisa original paper mein recommend hota hai).

    Layer 1: har node apne direct (1-hop) neighbors se info leta hai
    Layer 2: ab har node apne neighbors ki (already-aggregated) info se
             info leta hai — isliye effectively 2-hop neighborhood tak
             information pohanchti hai.
    """

    def __init__(self, in_dim: int, hidden_dim: int = 32, out_dim: int = 64):
        super().__init__()
        self.layer1 = SAGELayer(in_dim, hidden_dim)
        self.layer2 = SAGELayer(hidden_dim, out_dim)

    def forward(self, features: torch.Tensor, adjacency: list) -> torch.Tensor:
        """
        Args:
            features (torch.Tensor): (N, in_dim) — har node ka starting feature vector
            adjacency (list): har index i ke liye, uske neighbor indices ki list

        Returns:
            torch.Tensor: (N, out_dim) final wallet embeddings
        """
        h1 = self._propagate(self.layer1, features, adjacency, normalize=False)
        h2 = self._propagate(self.layer2, h1, adjacency, normalize=True)
        return h2

    def _propagate(self, layer: SAGELayer, h: torch.Tensor, adjacency: list,
                    normalize: bool = False) -> torch.Tensor:
        num_nodes = h.shape[0]
        neigh_agg = torch.zeros_like(h)

        for i in range(num_nodes):
            neighbors = adjacency[i]
            if len(neighbors) > 0:
                neigh_agg[i] = h[neighbors].mean(dim=0)
            else:
                # Koi neighbor nahi (isolated node) — apne hi features use karo
                neigh_agg[i] = h[i]

        return layer(h, neigh_agg, normalize=normalize)


class GraphSAGETrainer:
    """
    Ye class graph se GraphSAGE embeddings train karti hai aur save karti hai.
    Interface jaan-boojh kar Node2VecTrainer jaisa rakha hai, taake baaki
    system (API routes, hybrid engine) dono models ko easily switch/compare
    kar sakein.
    """

    MODELS_FOLDER = "models"

    @performance_timer.timed("graphsage_embedding_training")
    def train(self, graph, hidden_dim: int = 32, out_dim: int = 64,
              epochs: int = 100, lr: float = 0.01, negative_samples: int = 5) -> dict:
        """
        Diye gaye graph se GraphSAGE embeddings train karta hai
        (unsupervised — Node2Vec ki tarah, positive/negative sampling
        se, lekin random walks ki jagah neighborhood aggregation use
        karke).

        Args:
            graph: NetworkX graph object
            hidden_dim (int): Hidden layer ki size (default 32)
            out_dim (int): Final embedding ki length (default 64)
            epochs (int): Training iterations (default 100)
            lr (float): Learning rate (default 0.01)
            negative_samples (int): Har positive edge ke liye kitne negative samples (default 5)

        Returns:
            dict: {wallet_address: embedding_vector}
        """
        # Step 1: Day 2 ka GNN dataset builder use karte hain
        # (node features + edge_index + edge_attr — GraphData object)
        dataset = build_gnn_dataset(graph)
        nodes = dataset.node_list
        node_to_idx = dataset.node_to_idx

        if len(nodes) == 0:
            return {}

        feature_matrix = normalize_feature_matrix(dataset.x)
        in_dim = feature_matrix.shape[1]

        # Step 2: Adjacency list banao (in + out neighbors dono, undirected treat karte hain)
        adjacency = self._build_adjacency(graph, nodes, node_to_idx)

        # Step 3: Positive pairs (edges) nikalo, training ke liye
        # (dataset.edge_index already banaya hua hai — [source_indices, target_indices])
        if dataset.edge_index.shape[1] == 0:
            edge_list = []
        else:
            edge_list = list(zip(
                dataset.edge_index[0].tolist(),
                dataset.edge_index[1].tolist(),
            ))

        if len(edge_list) == 0:
            # Koi edge nahi hai (isolated nodes only) — random embeddings return karo
            model = GraphSAGENet(in_dim, hidden_dim, out_dim)
            with torch.no_grad():
                embeddings_tensor = model(feature_matrix, adjacency)
            embeddings = {node: embeddings_tensor[i].numpy() for i, node in enumerate(nodes)}
            self._save_model(model, in_dim, hidden_dim, out_dim)
            self._save_embeddings(embeddings)
            return embeddings

        # Step 4: Model + optimizer
        model = GraphSAGENet(in_dim, hidden_dim, out_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)

        num_nodes = len(nodes)

        for epoch in range(epochs):
            optimizer.zero_grad()

            embeddings_tensor = model(feature_matrix, adjacency)

            # Positive pairs: graph mein jo actual connections hain
            pos_u = torch.tensor([u for u, v in edge_list])
            pos_v = torch.tensor([v for u, v in edge_list])
            pos_score = (embeddings_tensor[pos_u] * embeddings_tensor[pos_v]).sum(dim=1)
            pos_loss = -F.logsigmoid(pos_score).mean()

            # Negative pairs: random nodes jo directly connected nahi (approx)
            neg_v = torch.randint(0, num_nodes, (len(edge_list) * negative_samples,))
            neg_u = pos_u.repeat_interleave(negative_samples)
            neg_score = (embeddings_tensor[neg_u] * embeddings_tensor[neg_v]).sum(dim=1)
            neg_loss = -F.logsigmoid(-neg_score).mean()

            loss = pos_loss + neg_loss
            loss.backward()
            optimizer.step()

        # Final embeddings nikalo (no grad needed ab)
        with torch.no_grad():
            embeddings_tensor = model(feature_matrix, adjacency)

        embeddings = {node: embeddings_tensor[i].numpy() for i, node in enumerate(nodes)}

        self._save_model(model, in_dim, hidden_dim, out_dim)
        self._save_embeddings(embeddings)

        return embeddings

    def _build_adjacency(self, graph, nodes: list, node_to_idx: dict) -> list:
        """
        Har node ke liye uske neighbors ki index-list banata hai
        (in-neighbors + out-neighbors dono, kyunki wallet transactions
        mein direction se zyada "kis se interact kiya" important hai).
        """
        adjacency = []
        for node in nodes:
            neighbors = set(graph.predecessors(node)) | set(graph.successors(node))
            neighbor_indices = [node_to_idx[n] for n in neighbors if n in node_to_idx]
            adjacency.append(neighbor_indices)
        return adjacency

    def _save_model(self, model, in_dim, hidden_dim, out_dim):
        """
        Trained GraphSAGE model ko file mein save karta hai
        (weights + architecture dimensions, taake dobara load ho sake).
        """
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        model_path = os.path.join(self.MODELS_FOLDER, "graphsage.pt")
        torch.save({
            "state_dict": model.state_dict(),
            "in_dim": in_dim,
            "hidden_dim": hidden_dim,
            "out_dim": out_dim,
        }, model_path)

    def _save_embeddings(self, embeddings: dict):
        """
        Wallet embeddings ko pickle file mein save karta hai
        (Node2Vec se alag filename, taake dono independently rahein).
        """
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        embeddings_path = os.path.join(self.MODELS_FOLDER, "wallet_embeddings_graphsage.pkl")

        with open(embeddings_path, "wb") as f:
            pickle.dump(embeddings, f)

    def load_embeddings(self) -> dict:
        from performance.cache import simple_cache

        cached = simple_cache.get("wallet_embeddings_graphsage")
        if cached is not None:
            return cached

        embeddings_path = os.path.join(self.MODELS_FOLDER, "wallet_embeddings_graphsage.pkl")

        if not os.path.exists(embeddings_path):
            return {}

        with open(embeddings_path, "rb") as f:
            embeddings = pickle.load(f)

        simple_cache.set("wallet_embeddings_graphsage", embeddings, ttl_seconds=120)
        return embeddings


# Ek single instance banate hain jo poore project mein import hoga
graphsage_trainer = GraphSAGETrainer()