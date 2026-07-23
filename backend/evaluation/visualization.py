"""
Evaluation Visualization

Ye module matplotlib use kar ke evaluation ke liye charts banata hai —
similarity distribution, confidence histogram, rule vs AI comparison,
aur embeddings ka PCA scatter plot.
"""

import os
import matplotlib
matplotlib.use("Agg")  # GUI ke bina bhi chart bana sake (server environment ke liye)
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np


class EvaluationVisualizer:
    """
    Ye class evaluation results se charts (images) banati hai.
    """

    CHARTS_FOLDER = "evaluation_charts"

    def __init__(self):
        os.makedirs(self.CHARTS_FOLDER, exist_ok=True)

    def plot_similarity_distribution(self, similarity_scores: list, filename: str = "similarity_distribution.png") -> str:
        """
        Similarity scores ki distribution (histogram) plot karta hai.

        Args:
            similarity_scores (list): Similarity scores ki list
            filename (str): Save karne wali file ka naam

        Returns:
            str: Saved chart ka path
        """
        plt.figure(figsize=(8, 5))
        plt.hist(similarity_scores, bins=10, color="steelblue", edgecolor="black")
        plt.title("Similarity Score Distribution")
        plt.xlabel("Similarity Score")
        plt.ylabel("Frequency")

        path = os.path.join(self.CHARTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()

        return path

    def plot_confidence_histogram(self, confidence_scores: list, filename: str = "confidence_histogram.png") -> str:
        """
        Confidence scores ki histogram plot karta hai.

        Args:
            confidence_scores (list): Confidence scores ki list
            filename (str): Save karne wali file ka naam

        Returns:
            str: Saved chart ka path
        """
        plt.figure(figsize=(8, 5))
        plt.hist(confidence_scores, bins=10, color="seagreen", edgecolor="black")
        plt.title("Confidence Score Distribution")
        plt.xlabel("Confidence (%)")
        plt.ylabel("Frequency")

        path = os.path.join(self.CHARTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()

        return path

    def plot_rule_vs_ai_comparison(self, comparison_data: list, filename: str = "rule_vs_ai_comparison.png") -> str:
        """
        Rule vs Node2Vec vs Hybrid ka bar chart banata hai.

        Args:
            comparison_data (list): [{"model": "Rule", "similarity": 0.72}, ...]
            filename (str): Save karne wali file ka naam

        Returns:
            str: Saved chart ka path
        """
        models = [item["model"] for item in comparison_data]
        scores = [item["similarity"] for item in comparison_data]

        plt.figure(figsize=(8, 5))
        plt.bar(models, scores, color=["#e07a5f", "#3d5a80", "#81b29a"])
        plt.title("Rule-Based vs AI vs Hybrid Comparison")
        plt.xlabel("Model")
        plt.ylabel("Similarity Score")
        plt.ylim(0, 1)

        path = os.path.join(self.CHARTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()

        return path

    def plot_embedding_scatter(self, embeddings: dict, filename: str = "embedding_scatter.png") -> str:
        """
        Node2Vec embeddings ko PCA se 2D mein convert karke scatter plot banata hai.

        Args:
            embeddings (dict): {wallet_address: embedding_vector}
            filename (str): Save karne wali file ka naam

        Returns:
            str: Saved chart ka path
        """
        wallets = list(embeddings.keys())
        vectors = np.array([embeddings[w] for w in wallets])

        # PCA se high-dimensional vectors (jaise 64D) ko 2D mein convert karte hain
        pca = PCA(n_components=2)
        reduced_vectors = pca.fit_transform(vectors)

        plt.figure(figsize=(8, 6))
        plt.scatter(reduced_vectors[:, 0], reduced_vectors[:, 1], color="darkorange", edgecolor="black")
        plt.title("Wallet Embeddings (PCA 2D Projection)")
        plt.xlabel("Component 1")
        plt.ylabel("Component 2")

        path = os.path.join(self.CHARTS_FOLDER, filename)
        plt.savefig(path)
        plt.close()

        return path


# Ek single instance banate hain jo poore project mein import hoga
evaluation_visualizer = EvaluationVisualizer()