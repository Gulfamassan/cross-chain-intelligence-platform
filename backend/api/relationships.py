"""
Relationships API Routes

Returns a wallet's relationships, centrality score, and cluster
in a single response.
"""

from fastapi import APIRouter, HTTPException
from api.graph import current_graph
from analytics.centrality import centrality_analyzer
from analytics.relationship_engine import relationship_engine
from analytics.clustering import cluster_analyzer
from utils.validators import is_valid_ethereum_address

router = APIRouter()


@router.get("/wallet/{address}/relationships")
def get_wallet_relationships(address: str):
    """
    Returns a full summary of a wallet's relationships, centrality
    score, and cluster.

    Args:
        address (str): Wallet address

    Returns:
        dict: Direct/indirect connections, cluster name, centrality score

    Raises:
        HTTPException: If the address is invalid (400), no graph has
                        been built yet (400), or the wallet isn't in
                        the graph (404)
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

    direct = relationship_engine.find_direct_neighbors(current_graph.graph, wallet)
    indirect = relationship_engine.find_indirect_neighbors(current_graph.graph, wallet, depth=2)

    cluster = cluster_analyzer.get_wallet_cluster(current_graph.graph, wallet)

    all_centrality = centrality_analyzer.analyze_all(current_graph.graph)
    centrality_score = all_centrality.get(wallet, {}).get("degree", 0.0)

    return {
        "wallet": address,
        "direct_connections": len(direct),
        "indirect_connections": len(indirect),
        "cluster": cluster,
        "centrality_score": centrality_score,
    }