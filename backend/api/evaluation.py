"""
Evaluation API Routes

Handles system performance metrics, benchmark comparisons, and
the complete evaluation report.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from evaluation.metrics import evaluation_metrics
from evaluation.benchmark import benchmark_engine
from ai.node2vec_model import node2vec_trainer

router = APIRouter()


@router.get("/evaluation/metrics")
def get_evaluation_metrics():
    """
    Returns the system's basic performance metrics — wallets, edges,
    embedding dimension, etc.

    Returns:
        dict: Metrics report

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    embeddings = node2vec_trainer.load_embeddings()

    report = evaluation_metrics.generate_full_report(
        current_graph.graph, embeddings
    )

    return report


class BenchmarkRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_1: str
    wallet_2: str
    wallet_1_csv: str
    wallet_2_csv: str
    chain: str = "ethereum"


@router.post("/evaluation/benchmark")
def get_benchmark_comparison(request: BenchmarkRequest):
    """
    Compares the Rule-Based, Node2Vec, and Hybrid approaches for a
    given wallet pair.

    Args:
        request (BenchmarkRequest): Both wallets, CSV paths, chain

    Returns:
        dict: Comparison across all three models

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    result = benchmark_engine.compare_approaches(
        request.wallet_1, request.wallet_2,
        request.wallet_1_csv, request.wallet_2_csv,
        current_graph.graph, request.chain
    )

    return result


@router.get("/evaluation/report")
def get_full_evaluation_report():
    """
    Returns the complete evaluation report — both metrics and charts.

    Returns:
        dict: Complete evaluation report with chart paths

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    embeddings = node2vec_trainer.load_embeddings()
    metrics = evaluation_metrics.generate_full_report(current_graph.graph, embeddings)

    chart_paths = {}
    if embeddings:
        from evaluation.visualization import evaluation_visualizer
        chart_paths["embedding_scatter"] = evaluation_visualizer.plot_embedding_scatter(embeddings)

    return {
        "metrics": metrics,
        "charts": chart_paths,
    }