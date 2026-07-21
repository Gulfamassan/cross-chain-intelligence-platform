"""
Relationships API Routes

Ye module ek wallet ke relationships, centrality, aur cluster
ki poori summary deta hai — ek hi API call mein.
"""

from fastapi import APIRouter, HTTPException
from api.graph import current_graph
from analytics.centrality import centrality_analyzer
from analytics.relationship_engine import relationship_engine
from analytics.clustering import cluster_analyzer
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/wallet/{address}/relationships")
def get_wallet_relationships(address: str):
    """
    Diye gaye wallet ki relationships, centrality score, aur cluster
    ki poori summary deta hai.

    Args:
        address (str): Wallet address

    Returns:
        dict: Direct/indirect connections, cluster naam, centrality score

    Raises:
        HTTPException: Agar address invalid ho (400), graph build na hua ho (400),
                        ya wallet graph mein na ho (404)
    """
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    wallet = address.lower()

    if wallet not in current_graph.graph:
        raise HTTPException(status_code=404, detail="Wallet not found in the current graph")

    # Direct aur indirect connections nikalte hain
    direct = relationship_engine.find_direct_neighbors(current_graph.graph, wallet)
    indirect = relationship_engine.find_indirect_neighbors(current_graph.graph, wallet, depth=2)

    # Cluster nikalte hain
    cluster = cluster_analyzer.get_wallet_cluster(current_graph.graph, wallet)

    # Centrality score nikalte hain (degree centrality use kar rahe hain, sabse standard measure)
    all_centrality = centrality_analyzer.analyze_all(current_graph.graph)
    centrality_score = all_centrality.get(wallet, {}).get("degree", 0.0)

    return {
        "wallet": address,
        "direct_connections": len(direct),
        "indirect_connections": len(indirect),
        "cluster": cluster,
        "centrality_score": centrality_score,
    }