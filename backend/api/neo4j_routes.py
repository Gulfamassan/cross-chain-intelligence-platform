"""
Neo4j API Routes

Handles interaction with the Neo4j graph database — import, wallet
lookup, neighbors, path finding, and community detection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from database.graph_loader import graph_loader
from database.graph_repository import graph_repository
from analytics.clustering import cluster_analyzer
from utils.validators import is_valid_ethereum_address

router = APIRouter()


class ImportRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    chain: str = "ethereum"


@router.post("/neo4j/import")
def import_graph_to_neo4j(request: ImportRequest):
    """
    Imports the currently built (NetworkX) graph into the Neo4j database.

    Args:
        request (ImportRequest): Blockchain name

    Returns:
        dict: Number of nodes and relationships imported

    Raises:
        HTTPException: If no graph has been built yet (400)
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
    Retrieves a wallet's information from Neo4j — including its
    Knowledge Graph entity classification (Wallet/Exchange/Bridge/
    Contract/Personal labels), chain, and direct connections.

    Args:
        address (str): Wallet address

    Returns:
        dict: Wallet details (entity labels, chain), connections

    Raises:
        HTTPException: If the address is invalid (400)
    """
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    connections = graph_repository.get_wallet_connections(address)

    # Sprint 12/13 addition: entity-type labels + chain from the
    # Knowledge Graph enrichment (Day 6-7 work), via the same
    # graph_repository — no duplicate query logic.
    details = graph_repository.get_wallet_details_with_labels(address)
    entity_labels = [label for label in details.get("labels", []) if label != "Wallet"]

    return {
        "wallet": address,
        "chain": details.get("chain"),
        "entity_type": entity_labels[0] if entity_labels else "Unclassified",
        "neo4j_labels": details.get("labels", []),
        "connections_count": len(connections),
        "connections": connections,
    }


@router.get("/neo4j/neighbors/{address}")
def get_neo4j_neighbors(address: str):
    """
    Retrieves all of a wallet's direct neighbors from Neo4j.

    Args:
        address (str): Wallet address

    Returns:
        dict: List of neighbor wallets

    Raises:
        HTTPException: If the address is invalid (400)
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
    Finds the shortest path between two wallets in Neo4j.

    Args:
        wallet_1 (str): First wallet (query parameter)
        wallet_2 (str): Second wallet (query parameter)

    Returns:
        dict: The wallets that make up the path

    Raises:
        HTTPException: If an address is invalid (400)
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
    Runs community detection on the currently built graph
    (corresponding to the data stored in Neo4j).

    Returns:
        dict: All clusters and their wallets

    Raises:
        HTTPException: If no graph has been built yet (400)
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