"""
Graph API Routes

Handles building, visualizing, and analyzing the wallet
transaction graph.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from graph.builder import TransactionGraph
from graph.visualization import graph_visualizer

router = APIRouter()

# Kept in memory so the graph doesn't need to be rebuilt every time
current_graph = TransactionGraph()


class BuildGraphRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    csv_path: str


@router.post("/build-graph")
def build_graph(request: BuildGraphRequest):
    """
    Builds a transaction graph from the given CSV file.

    Args:
        request (BuildGraphRequest): Path to the CSV file

    Returns:
        dict: Success message and basic graph info

    Raises:
        HTTPException: If the CSV file doesn't exist (404) or another error occurs (500)
    """
    import os
    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail="CSV file not found")

    try:
        current_graph.load_csv(request.csv_path)
        current_graph.build_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Graph Built Successfully",
        "num_wallets": len(current_graph.get_nodes()),
        "num_transactions": len(current_graph.get_edges()),
    }


@router.get("/graph/statistics")
def get_graph_statistics():
    """
    Returns statistics for the currently built graph.

    Returns:
        dict: Nodes, edges, density, components, average degree

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    return current_graph.graph_statistics()


@router.post("/graph/visualize")
def visualize_graph():
    """
    Generates an interactive HTML visualization of the currently
    built graph.

    Returns:
        dict: Path and public URL of the saved HTML file

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    output_path = graph_visualizer.visualize(current_graph.graph, "static_graphs/wallet_graph.html")

    return {
        "message": "Graph Visualization Created Successfully",
        "html_path": output_path,
        "url": "http://127.0.0.1:8000/static_graphs/wallet_graph.html"
    }