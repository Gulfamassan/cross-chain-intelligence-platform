"""
Feature ML API Routes (Sprint 20, Day 1)

Random Forest aur XGBoost (Sprint 17/18) ke liye API endpoints —
pehle ye sirf terminal scripts se accessible the.

⚠️ Reminder (jaisa poore project mein consistent raha hai): Training
`n=4` (dev set) par hoti hai — statistically fragile, sirf pipeline
demonstration hai (dekhein `ai/xgboost_model.py` docstring).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from evaluation.graphsage_split import get_dev_cases
from evaluation.run_graphsage_comparison import resolve_csv_path
from ai.feature_vector import build_feature_matrix, build_pairwise_features
from ai.xgboost_model import xgboost_trainer
from ai.random_forest_model import random_forest_trainer

router = APIRouter()


@router.post("/ai/feature-ml/train")
def train_feature_ml_models():
    """
    Random Forest aur XGBoost dono ko Sprint 17 Day 4 ke dev set
    (n=4) par train karta hai.

    Returns:
        dict: Dono models ki feature importances

    Raises:
        HTTPException: Agar training data build karne mein error aaye (500)
    """
    try:
        dev_cases = get_dev_cases()
        X_dev, y_dev = build_feature_matrix(dev_cases, resolve_csv_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature building failed: {e}")

    xgboost_trainer.train(X_dev, y_dev)
    random_forest_trainer.train(X_dev, y_dev)

    return {
        "message": "Feature ML models trained (Random Forest + XGBoost) on dev set (n=4)",
        "caveat": "n=4 training examples — statistically fragile, pipeline demonstration only",
        "xgboost_feature_importance": xgboost_trainer.feature_importance(),
        "random_forest_feature_importance": random_forest_trainer.feature_importance(),
    }


class FeatureMLPredictRequest(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    wallet_1: str
    chain_1: str
    wallet_2: str
    chain_2: str
    model: str = "xgboost"  # "xgboost" ya "random_forest"


@router.post("/ai/feature-ml/predict")
def predict_feature_ml(request: FeatureMLPredictRequest):
    """
    Do wallets ke liye pairwise features banata hai, aur trained
    model (XGBoost ya Random Forest) se predict karta hai.

    Args:
        request (FeatureMLPredictRequest): Both wallets + chains + model choice

    Returns:
        dict: {"wallet_1", "wallet_2", "model", "predicted", "probability"}

    Raises:
        HTTPException: Agar model train nahi hua (400), CSV nahi mili (404),
                        ya invalid model naam diya (400)
    """
    if request.model not in ("xgboost", "random_forest"):
        raise HTTPException(status_code=400, detail='model must be "xgboost" or "random_forest"')

    try:
        csv_1 = resolve_csv_path(request.wallet_1, request.chain_1)
        csv_2 = resolve_csv_path(request.wallet_2, request.chain_2)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    features = build_pairwise_features(
        request.wallet_1, request.chain_1, csv_1,
        request.wallet_2, request.chain_2, csv_2,
    )

    trainer = xgboost_trainer if request.model == "xgboost" else random_forest_trainer

    try:
        result = trainer.predict([features])[0]
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail=f"{request.model} not trained yet. Call /ai/feature-ml/train first."
        )

    return {
        "wallet_1": request.wallet_1,
        "wallet_2": request.wallet_2,
        "model": request.model,
        "predicted": result["predicted"],
        "probability": result["probability"],
    }