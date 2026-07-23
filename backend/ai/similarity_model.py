"""
Similarity Model (AI-Based)

Ye module do wallet embeddings ke beech Cosine Similarity
calculate karta hai — jitna zyada score, utna zyada ye
dono wallets behavior/graph-position mein similar hain.
"""

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class EmbeddingSimilarity:
    """
    Ye class Node2Vec embeddings ke beech AI-based similarity
    calculate karti hai.
    """

    def calculate_similarity(self, embedding1, embedding2) -> float:
        """
        Do embeddings ke beech cosine similarity nikalta hai.

        Args:
            embedding1: Pehli wallet ka embedding vector
            embedding2: Dusri wallet ka embedding vector

        Returns:
            float: Similarity score (-1 se 1 ke beech, jitna zyada utna similar)
        """
        # sklearn ko 2D array chahiye hota hai, isliye reshape karte hain
        vec1 = np.array(embedding1).reshape(1, -1)
        vec2 = np.array(embedding2).reshape(1, -1)

        similarity = cosine_similarity(vec1, vec2)[0][0]

        return round(float(similarity), 4)

    def compare_wallets(self, embeddings: dict, wallet1: str, wallet2: str) -> dict:
        """
        Do wallets ke embeddings dhoond kar unki similarity nikalta hai.

        Args:
            embeddings (dict): {wallet_address: embedding_vector}
            wallet1 (str): Pehli wallet ka address
            wallet2 (str): Dusri wallet ka address

        Returns:
            dict: Similarity score aur dono wallets ke naam

        Raises:
            ValueError: Agar koi wallet embeddings mein na mile
        """
        wallet1_key = wallet1.lower()
        wallet2_key = wallet2.lower()

        if wallet1_key not in embeddings:
            raise ValueError(f"Wallet {wallet1} not found in embeddings")

        if wallet2_key not in embeddings:
            raise ValueError(f"Wallet {wallet2} not found in embeddings")

        score = self.calculate_similarity(embeddings[wallet1_key], embeddings[wallet2_key])

        return {
            "wallet_1": wallet1,
            "wallet_2": wallet2,
            "ai_similarity": score,
        }

    def find_most_similar(self, embeddings: dict, wallet: str, top_n: int = 5) -> list:
        """
        Diye gaye wallet ke sabse "similar" wallets dhoondta hai
        (embedding space mein sabse close).

        Args:
            embeddings (dict): {wallet_address: embedding_vector}
            wallet (str): Jis wallet ke similar wallets chahiye
            top_n (int): Kitni top wallets chahiye

        Returns:
            list: [(wallet_address, similarity_score), ...] sorted, sabse zyada similar pehle
        """
        wallet_key = wallet.lower()

        if wallet_key not in embeddings:
            raise ValueError(f"Wallet {wallet} not found in embeddings")

        target_embedding = embeddings[wallet_key]
        scores = []

        for other_wallet, other_embedding in embeddings.items():
            if other_wallet == wallet_key:
                continue

            score = self.calculate_similarity(target_embedding, other_embedding)
            scores.append((other_wallet, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_n]


# Ek single instance banate hain jo poore project mein import hoga
embedding_similarity = EmbeddingSimilarity()