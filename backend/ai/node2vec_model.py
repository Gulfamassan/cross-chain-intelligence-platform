"""
Node2Vec Model

Ye module NetworkX graph se Node2Vec algorithm use karke
har wallet ke liye ek numeric vector (embedding) train karta hai.
"""

import os
import pickle
from node2vec import Node2Vec
from performance.timer import performance_timer


class Node2VecTrainer:
    """
    Ye class graph se Node2Vec embeddings train karti hai aur save karti hai.
    """

    MODELS_FOLDER = "models"
    @performance_timer.timed("embedding_training")
    def train(self, graph, dimensions: int = 64, walk_length: int = 30,
              num_walks: int = 200, workers: int = 2) -> dict:
        """
        Diye gaye graph se Node2Vec embeddings train karta hai.

        Args:
            graph: NetworkX graph object
            dimensions (int): Har embedding vector ki length (default 64)
            walk_length (int): Har random walk kitni lambi ho (default 30 steps)
            num_walks (int): Har node se kitni walks ki jayein (default 200)
            workers (int): Kitne parallel processes use karein (default 2)

        Returns:
            dict: {wallet_address: embedding_vector}
        """
        # Node2Vec object banate hain — ye pehle random walks generate karta hai
        node2vec = Node2Vec(
            graph,
            dimensions=dimensions,
            walk_length=walk_length,
            num_walks=num_walks,
            workers=workers,
        )

        # SkipGram model train karte hain walks par
        model = node2vec.fit(window=10, min_count=1, batch_words=4)

        # Har wallet ka embedding vector nikalte hain
        embeddings = {}
        for node in graph.nodes():
            embeddings[node] = model.wv[node]

        # Model aur embeddings dono save karte hain
        self._save_model(model)
        self._save_embeddings(embeddings)

        return embeddings

    def _save_model(self, model):
        """
        Trained Node2Vec/SkipGram model ko file mein save karta hai.
        """
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        model_path = os.path.join(self.MODELS_FOLDER, "node2vec.model")
        model.save(model_path)

    def _save_embeddings(self, embeddings: dict):
        """
        Wallet embeddings ko pickle file mein save karta hai.
        """
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        embeddings_path = os.path.join(self.MODELS_FOLDER, "wallet_embeddings.pkl")

        with open(embeddings_path, "wb") as f:
            pickle.dump(embeddings, f)

    def load_embeddings(self) -> dict:
        from performance.cache import simple_cache

        cached = simple_cache.get("wallet_embeddings")
        if cached is not None:
           return cached

        embeddings_path = os.path.join(self.MODELS_FOLDER, "wallet_embeddings.pkl")

        if not os.path.exists(embeddings_path):
            return {}

        with open(embeddings_path, "rb") as f:
            embeddings = pickle.load(f)

        simple_cache.set("wallet_embeddings", embeddings, ttl_seconds=120)
        return embeddings


# Ek single instance banate hain jo poore project mein import hoga
node2vec_trainer = Node2VecTrainer()