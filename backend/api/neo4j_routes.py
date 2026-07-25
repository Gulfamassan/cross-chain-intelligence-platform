"""
Neo4j API Routes

Ye module Neo4j graph database ke saath interact karne ke
endpoints handle karta hai — import, wallet lookup, neighbors,
path finding, aur community detection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from database.graph_loader import graph_loader
from database.graph_repository import graph_repository
from analytics.clustering import cluster_analyzer
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class ImportRequest(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    chain: str = "ethereum"


@router.post("/neo4j/import")
def import_graph_to_neo4j(request: ImportRequest):
    """
    Currently built (NetworkX) graph ko Neo4j database mein import karta hai.

    Args:
        request (ImportRequest): Blockchain ka naam

    Returns:
        dict: Kitne nodes aur relationships import hue

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    result = graph_loader.load_graph_to_neo4j(current_graph.graph, request.chain)

    return {
        "message": "Graph Imported to Neo4j Successfully",
        **result,
    }


@router.get("/neo4j/wallet/{address}")
def get_wallet_from_neo4j(address: str):
    """
    Neo4j se ek wallet ki info nikalta hai.

    Args:
        address (str): Wallet address

    Returns:
        dict: Wallet ki details aur uske connections

    Raises:
        HTTPException: Agar address invalid ho (400)
    """
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    connections = graph_repository.get_wallet_connections(address)

    return {
        "wallet": address,
        "connections_count": len(connections),
        "connections": connections,
    }


@router.get("/neo4j/neighbors/{address}")
def get_neo4j_neighbors(address: str):
    """
    Neo4j se ek wallet ke saare direct neighbors nikalta hai.

    Args:
        address (str): Wallet address

    Returns:
        dict: Neighbor wallets ki list

    Raises:
        HTTPException: Agar address invalid ho (400)
    """
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    connections = graph_repository.get_wallet_connections(address)
    neighbor_addresses = list({conn["wallet"] for conn in connections})

    return {
        "wallet": address,
        "neighbors": neighbor_addresses,
        "count": len(neighbor_addresses),
    }


@router.get("/neo4j/path")
def get_neo4j_path(wallet_1: str, wallet_2: str):
    """
    Neo4j se do wallets ke beech shortest path dhoondta hai.

    Args:
        wallet_1 (str): Pehli wallet (query parameter)
        wallet_2 (str): Dusri wallet (query parameter)

    Returns:
        dict: Path ke wallets

    Raises:
        HTTPException: Agar koi address invalid ho (400)
    """
    if not is_valid_ethereum_address(wallet_1) or not is_valid_ethereum_address(wallet_2):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    query = """
    MATCH path = shortestPath(
        (a:Wallet {address: $wallet_1})-[*..10]-(b:Wallet {address: $wallet_2})
    )
    RETURN [node in nodes(path) | node.address] AS path_addresses
    """

    from database.neo4j_client import neo4j_client
    result = neo4j_client.run_query(query, {
        "wallet_1": wallet_1.lower(),
        "wallet_2": wallet_2.lower(),
    })

    if not result:
        return {"wallet_1": wallet_1, "wallet_2": wallet_2, "connected": False, "path": []}

    return {
        "wallet_1": wallet_1,
        "wallet_2": wallet_2,
        "connected": True,
        "path": result[0]["path_addresses"],
    }


@router.get("/neo4j/community")
def get_neo4j_community():
    """
    Currently built graph par community detection chalata hai
    (Neo4j mein stored data ke corresponding).

    Returns:
        dict: Saare clusters aur unke wallets

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    clusters = cluster_analyzer.get_all_clusters(current_graph.graph)

    return {
        "total_clusters": len(clusters),
        "clusters": clusters,
    }