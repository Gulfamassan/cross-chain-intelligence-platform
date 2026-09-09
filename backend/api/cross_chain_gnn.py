"""
Cross-Chain GNN API Routes (Sprint 20, Day 1)

Sprint 19 (unified cross-chain graph + GraphSAGE) ke liye API
endpoints — pehle ye sirf terminal scripts se accessible the.

`current_cross_chain_graph` module-level state hai (jaisa
`api/graph.py` ka `current_graph`) — build -> train -> similarity,
teen sequential steps.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph.cross_chain_graph import build_unified_graph
from ai.pyg_graphsage_trainer import train_pyg_graphsage
from ai.cross_chain_wallet_embeddings import classify_cross_chain_pair, save_embeddings

router = APIRouter()

# Module-level state — build-graph endpoint isay set karta hai,
# train/similarity endpoints isay use karte hain
current_cross_chain_graph = None


class BuildCrossChainGraphRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    csvs: list  # [{"csv_path": "...", "chain": "ethereum"}, ...]


@router.post("/cross-chain-gnn/build-graph")
def build_cross_chain_graph(request: BuildCrossChainGraphRequest):
    """
    Sprint 19 Day 1 — Diye gaye CSVs se unified cross-chain graph
    banata hai (chain-aware `chain:address` nodes + evidence edges).

    Args:
        request (BuildCrossChainGraphRequest): CSV paths + unke chains

    Returns:
        dict: Node/edge counts, edge-category breakdown

    Raises:
        HTTPException: Agar koi CSV nahi mili (404)
    """
    global current_cross_chain_graph

    wallet_chain_csvs = [(item["csv_path"], item["chain"]) for item in request.csvs]

    try:
        current_cross_chain_graph = build_unified_graph(wallet_chain_csvs)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    from collections import Counter
    edge_categories = Counter(
        d.get("edge_category") for _, _, d in current_cross_chain_graph.edges(data=True)
    )

    return {
        "message": "Unified cross-chain graph built successfully",
        "num_nodes": current_cross_chain_graph.number_of_nodes(),
        "num_edges": current_cross_chain_graph.number_of_edges(),
        "edge_categories": dict(edge_categories),
    }


@router.post("/cross-chain-gnn/train")
def train_cross_chain_graphsage():
    """
    Sprint 19 Day 4 — GraphSAGE ko unified cross-chain graph par
    train karta hai (Sprint 18 ka leakage-free methodology reuse).

    Returns:
        dict: Training stats

    Raises:
        HTTPException: Agar graph build nahi hua (400), ya graph
                        itna chhota hai ke split possible nahi (400)
    """
    if current_cross_chain_graph is None:
        raise HTTPException(
            status_code=400,
            detail="No unified graph built yet. Call /cross-chain-gnn/build-graph first."
        )

    try:
        result = train_pyg_graphsage(
            current_cross_chain_graph,
            checkpoint_path="models/cross_chain_graphsage_best.pt",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    save_embeddings(result["embeddings"])

    return {
        "message": "Cross-Chain GraphSAGE trained successfully",
        "best_epoch": result["best_epoch"],
        "best_val_loss": result["best_val_loss"],
        "num_nodes": result["num_nodes"],
        "num_edges": result["num_edges"],
    }


class CrossChainSimilarityRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_1: str  # "chain:address" format, e.g. "ethereum:0x..."
    wallet_2: str


@router.post("/cross-chain-gnn/similarity")
def cross_chain_similarity(request: CrossChainSimilarityRequest):
    """
    Sprint 19 Day 6 — Do wallets (chahe alag chains pe hon) ka
    cross-chain pair classification.

    Args:
        request (CrossChainSimilarityRequest): "chain:address" format mein wallets

    Returns:
        dict: {"wallet_1", "wallet_2", "cross_chain", "score", "classification"}

    Raises:
        HTTPException: Agar training nahi hui (400), format galat hai (400),
                        ya wallet embeddings mein nahi mila (404)
    """
    try:
        return classify_cross_chain_pair(request.wallet_1, request.wallet_2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="No trained cross-chain embeddings found. Call "
                   "/cross-chain-gnn/train first."
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))