"""
AI API Routes

Handles Node2Vec and GraphSAGE model training, and AI-based wallet
similarity comparison endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from ai.node2vec_model import node2vec_trainer
from ai.graphsage_model import graphsage_trainer
from ai.graphsage_model import graphsage_trainer, classify_relation
from ai.similarity_model import embedding_similarity

router = APIRouter()


@router.post("/ai/train")
def train_embeddings():
    """
    Trains Node2Vec embeddings on the currently built graph.

    Returns:
        dict: Success message and the number of wallets embedded

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    embeddings = node2vec_trainer.train(current_graph.graph)

    return {
        "message": "Embeddings Trained Successfully",
        "num_wallets": len(embeddings),
    }


class SimilarityRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_1: str
    wallet_2: str


@router.post("/ai/similarity")
def compare_wallet_similarity(request: SimilarityRequest):
    """
    Returns the AI-based (embedding) similarity score between two wallets.

    Args:
        request (SimilarityRequest): Both wallets' addresses

    Returns:
        dict: Similarity score

    Raises:
        HTTPException: If embeddings haven't been trained yet (400),
                        or a wallet isn't found in the embeddings (404)
    """
    embeddings = node2vec_trainer.load_embeddings()

    if not embeddings:
        raise HTTPException(
            status_code=400,
            detail="No trained embeddings found. Call /ai/train first."
        )

    try:
        result = embedding_similarity.compare_wallets(
            embeddings, request.wallet_1, request.wallet_2
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result


@router.post("/ai/graphsage/train")
def train_graphsage_embeddings():
    """
    Trains GraphSAGE embeddings on the currently built graph.

    Node2Vec ki tarah hi kaam karta hai, lekin sirf graph structure
    (random walks) ki jagah, GraphSAGE node features (degree, value
    sent/received) ko neighbors ke saath aggregate karke embeddings
    banata hai — isliye ye "inductive" approach hai.

    Returns:
        dict: Success message and the number of wallets embedded

    Raises:
        HTTPException: If no graph has been built yet (400)
    """
    if len(current_graph.get_nodes()) == 0:
        raise HTTPException(
            status_code=400,
            detail="No graph has been built yet. Call /build-graph first."
        )

    embeddings = graphsage_trainer.train(current_graph.graph)

    return {
        "message": "GraphSAGE Embeddings Trained Successfully",
        "num_wallets": len(embeddings),
    }


@router.post("/ai/graphsage/similarity")
def compare_wallet_similarity_graphsage(request: SimilarityRequest):
    """
    Returns the GraphSAGE-based embedding similarity score between two wallets.

    Args:
        request (SimilarityRequest): Both wallets' addresses

    Returns:
        dict: Similarity score

    Raises:
        HTTPException: If embeddings haven't been trained yet (400),
                        or a wallet isn't found in the embeddings (404)
    """
    embeddings = graphsage_trainer.load_embeddings()

    if not embeddings:
        raise HTTPException(
            status_code=400,
            detail="No trained GraphSAGE embeddings found. Call /ai/graphsage/train first."
        )

    try:
        result = embedding_similarity.compare_wallets(
            embeddings, request.wallet_1, request.wallet_2
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result["relation"] = classify_relation(result["ai_similarity"])

    return result