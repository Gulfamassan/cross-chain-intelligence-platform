"""
Evaluation API Routes

Ye module system ki performance metrics, benchmark comparison,
aur poori evaluation report ke endpoints handle karta hai.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from evaluation.metrics import evaluation_metrics
from evaluation.benchmark import benchmark_engine
from ai.node2vec_model import node2vec_trainer

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/evaluation/metrics")
def get_evaluation_metrics():
    """
    System ki basic performance metrics deta hai — wallets, edges,
    embedding dimension, waghera.

    Returns:
        dict: Metrics report

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
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
    Ye schema define karta hai ke POST-jaisa data GET request
    ke liye bhi query parameters se lena hoga — lekin hum simplicity
    ke liye POST body bhi support karenge.
    """
    wallet_1: str
    wallet_2: str
    wallet_1_csv: str
    wallet_2_csv: str
    chain: str = "ethereum"


@router.post("/evaluation/benchmark")
def get_benchmark_comparison(request: BenchmarkRequest):
    """
    Rule-Based, Node2Vec, aur Hybrid approaches ko compare karta hai
    ek wallet pair par.

    Args:
        request (BenchmarkRequest): Dono wallets, CSV paths, chain

    Returns:
        dict: Teeno models ka comparison

    Raises:
        HTTPException: Agar graph build nahi hua (400)
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
    Poori evaluation report deta hai — metrics aur charts dono
    generate karta hai.

    Returns:
        dict: Complete evaluation report, chart paths ke saath

    Raises:
        HTTPException: Agar graph build nahi hua (400)
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