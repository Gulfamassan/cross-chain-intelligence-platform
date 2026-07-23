"""
AI API Routes

Ye module Node2Vec model training aur AI-based wallet similarity
comparison ke endpoints handle karta hai.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.graph import current_graph
from ai.node2vec_model import node2vec_trainer
from ai.similarity_model import embedding_similarity

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.post("/ai/train")
def train_embeddings():
    """
    Currently built graph par Node2Vec embeddings train karta hai.

    Returns:
        dict: Success message aur kitni wallets ke embeddings bane

    Raises:
        HTTPException: Agar abhi tak koi graph build nahi hua (400)
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
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    wallet_1: str
    wallet_2: str


@router.post("/ai/similarity")
def compare_wallet_similarity(request: SimilarityRequest):
    """
    Do wallets ka AI-based (embedding) similarity score deta hai.

    Args:
        request (SimilarityRequest): Dono wallets ke addresses

    Returns:
        dict: Similarity score

    Raises:
        HTTPException: Agar embeddings abhi tak train nahi hui (400),
                        ya koi wallet embeddings mein na mile (404)
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