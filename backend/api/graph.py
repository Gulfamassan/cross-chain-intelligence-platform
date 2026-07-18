"""
Graph API Routes

Ye module wallet transaction graph banane aur uski
statistics dekhne ke endpoints handle karta hai.
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from graph.builder import TransactionGraph
from graph.visualization import graph_visualizer

# Router banate hain jo main.py mein include hoga
router = APIRouter()

# Graph ko memory mein rakhte hain taake baar-baar rebuild na karna pade
current_graph = TransactionGraph()


class BuildGraphRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    csv_path: str


@router.post("/build-graph")
def build_graph(request: BuildGraphRequest):
    """
    Diye gaye CSV file se ek transaction graph banata hai.

    Args:
        request (BuildGraphRequest): CSV file ka path

    Returns:
        dict: Success message aur basic graph info

    Raises:
        HTTPException: Agar CSV file exist nahi karti (404)
                        ya koi aur error aaye (500)
    """
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
    Currently built graph ki statistics deta hai.

    Returns:
        dict: Nodes, edges, density, components, average degree

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
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
    Currently built graph ka interactive HTML visualization banata hai.

    Returns:
        dict: Saved HTML file ka path

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    output_path = graph_visualizer.visualize(current_graph.graph, "wallet_graph.html")

    return {
        "message": "Graph Visualization Created Successfully",
        "html_path": output_path
    }