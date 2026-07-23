"""
Evaluation Metrics

Ye module system ki basic performance metrics collect karta hai —
kitne wallets, edges, average similarity, confidence, aur processing time.
"""

import time


class EvaluationMetrics:
    """
    Ye class saare high-level metrics calculate karti hai.
    """

    def calculate_graph_metrics(self, graph) -> dict:
        """
        Graph ke basic stats deta hai.

        Args:
            graph: NetworkX graph object

        Returns:
            dict: wallets (nodes) aur edges ka count
        """
        return {
            "wallets": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
        }

    def calculate_embedding_metrics(self, embeddings: dict) -> dict:
        """
        Embeddings ke stats deta hai.

        Args:
            embeddings (dict): {wallet_address: embedding_vector}

        Returns:
            dict: Embedding dimension aur kitne wallets ke embeddings hain
        """
        if not embeddings:
            return {"embedding_dimension": 0, "wallets_with_embeddings": 0}

        first_embedding = next(iter(embeddings.values()))

        return {
            "embedding_dimension": len(first_embedding),
            "wallets_with_embeddings": len(embeddings),
        }

    def calculate_average_similarity(self, similarity_scores: list) -> float:
        """
        Diye gaye similarity scores ka average nikalta hai.

        Args:
            similarity_scores (list): Similarity scores ki list (0-1 ya 0-100 scale)

        Returns:
            float: Average similarity
        """
        if not similarity_scores:
            return 0.0

        return round(sum(similarity_scores) / len(similarity_scores), 4)

    def calculate_average_confidence(self, confidence_scores: list) -> float:
        """
        Diye gaye confidence scores ka average nikalta hai.

        Args:
            confidence_scores (list): Confidence scores ki list

        Returns:
            float: Average confidence
        """
        if not confidence_scores:
            return 0.0

        return round(sum(confidence_scores) / len(confidence_scores), 2)

    def measure_processing_time(self, func, *args, **kwargs):
        """
        Diye gaye function ko chala kar uska processing time measure karta hai.

        Args:
            func: Jo function time measure karna hai
            *args, **kwargs: Us function ke parameters

        Returns:
            tuple: (function ka result, processing time seconds mein)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        processing_time = round(end_time - start_time, 2)

        return result, processing_time

    def generate_full_report(self, graph, embeddings: dict, similarity_scores: list = None,
                              confidence_scores: list = None, processing_time: float = None) -> dict:
        """
        Saare metrics ko ek combined report mein deta hai.

        Args:
            graph: NetworkX graph object
            embeddings (dict): Wallet embeddings
            similarity_scores (list): Similarity scores (optional)
            confidence_scores (list): Confidence scores (optional)
            processing_time (float): Processing time seconds mein (optional)

        Returns:
            dict: Complete metrics report
        """
        graph_metrics = self.calculate_graph_metrics(graph)
        embedding_metrics = self.calculate_embedding_metrics(embeddings)

        avg_similarity = self.calculate_average_similarity(similarity_scores or [])
        avg_confidence = self.calculate_average_confidence(confidence_scores or [])

        return {
            "wallets": graph_metrics["wallets"],
            "edges": graph_metrics["edges"],
            "embedding_dimension": embedding_metrics["embedding_dimension"],
            "avg_similarity": avg_similarity,
            "avg_confidence": avg_confidence,
            "processing_time": f"{processing_time} sec" if processing_time is not None else "N/A",
        }


# Ek single instance banate hain jo poore project mein import hoga
evaluation_metrics = EvaluationMetrics()