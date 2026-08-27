"""
XGBoost Baseline (Sprint 17 — added per feedback: "Add XGBoost before
going too deep into GNN")

⚠️ CRITICAL CAVEAT: Is project ka labeled dataset n=7 hai (Day 4 split:
4 dev, 3 held-out). XGBoost ek SUPERVISED classifier hai — 4 examples
pe train karna statistically kuch nahi sikhata (guaranteed
memorization/overfitting). Is module ka result isliye "trained model
ki accuracy" ke taur par report NAHI karna chahiye — sirf ek
"pipeline demonstration" (does the code work end-to-end) ke taur par.
"""

import os
import pickle

import numpy as np

try:
    import xgboost as xgb
except ImportError:
    xgb = None

from ai.feature_vector import FEATURE_NAMES


class XGBoostTrainer:
    """
    Pairwise feature vectors (ai/feature_vector.py se) par ek XGBoost
    classifier train karti hai — "Related" vs "Unrelated".
    """

    MODELS_FOLDER = "models"

    def __init__(self):
        self.model = None

    def train(self, X: list, y: list):
        """
        Args:
            X (list[dict]): Feature dicts (FEATURE_NAMES keys)
            y (list[int]): Labels (1=Related, 0=Unrelated)

        Returns:
            Trained XGBClassifier
        """
        if xgb is None:
            raise ImportError(
                "xgboost install nahi hai. Chalayein: "
                "pip install xgboost --break-system-packages"
            )

        X_matrix = np.array([[row[name] for name in FEATURE_NAMES] for row in X])
        y_array = np.array(y)

        # Shallow, kam trees — chhote n ke saath overfitting ka risk
        # kam karne ki koshish (lekin n=4 ke saath ye poori tarah
        # avoid nahi ho sakta, sirf halka mitigate hota hai)
        self.model = xgb.XGBClassifier(
            n_estimators=20,
            max_depth=2,
            learning_rate=0.3,
            eval_metric="logloss",
        )
        self.model.fit(X_matrix, y_array)

        self._save_model()
        return self.model

    def predict(self, X: list) -> list:
        """
        Args:
            X (list[dict]): Feature dicts

        Returns:
            list[dict]: [{"predicted": "Related"/"Unrelated", "probability": float}, ...]
        """
        if self.model is None:
            self._load_model()

        X_matrix = np.array([[row[name] for name in FEATURE_NAMES] for row in X])
        probabilities = self.model.predict_proba(X_matrix)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

        return [
            {"predicted": "Related" if p == 1 else "Unrelated", "probability": round(float(prob), 4)}
            for p, prob in zip(predictions, probabilities)
        ]

    def feature_importance(self) -> dict:
        """
        Har feature ka model ke decisions mein kitna weight tha —
        chhote n pe bhi ye ek useful diagnostic hai (chahe accuracy
        trust-worthy na ho, feature importance dikhata hai model
        KIS cheez ko dekh raha hai).
        """
        if self.model is None:
            self._load_model()
        importances = self.model.feature_importances_
        return dict(zip(FEATURE_NAMES, [round(float(i), 4) for i in importances]))

    def _save_model(self):
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        path = os.path.join(self.MODELS_FOLDER, "xgboost_model.pkl")
        with open(path, "wb") as f:
            pickle.dump(self.model, f)

    def _load_model(self):
        path = os.path.join(self.MODELS_FOLDER, "xgboost_model.pkl")
        with open(path, "rb") as f:
            self.model = pickle.load(f)


xgboost_trainer = XGBoostTrainer()