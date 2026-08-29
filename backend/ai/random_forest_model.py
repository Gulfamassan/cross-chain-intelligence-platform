"""
Random Forest Baseline (Sprint 18, Day 7)

XGBoost jaisa hi wrapper — same 8-feature pairwise vectors
(`ai/feature_vector.py`, Sprint 17 se) reuse karta hai, sirf
classifier `sklearn.ensemble.RandomForestClassifier` hai.

⚠️ SAME CAVEAT jo XGBoost ke liye tha: `n=4` training examples se
statistically valid classifier train nahi ho sakta — ye sirf pipeline
demonstration hai.
"""

import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ai.feature_vector import FEATURE_NAMES


class RandomForestTrainer:
    MODELS_FOLDER = "models"

    def __init__(self):
        self.model = None

    def train(self, X: list, y: list):
        X_matrix = np.array([[row[name] for name in FEATURE_NAMES] for row in X])
        y_array = np.array(y)

        # Shallow trees, kam estimators — XGBoost jaisa hi mitigation
        # (chhote n ke saath overfitting poori tarah avoid nahi hoti,
        # sirf halka kam hoti hai)
        self.model = RandomForestClassifier(
            n_estimators=20,
            max_depth=2,
            random_state=42,
        )
        self.model.fit(X_matrix, y_array)

        self._save_model()
        return self.model

    def predict(self, X: list) -> list:
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
        if self.model is None:
            self._load_model()
        importances = self.model.feature_importances_
        return dict(zip(FEATURE_NAMES, [round(float(i), 4) for i in importances]))

    def _save_model(self):
        os.makedirs(self.MODELS_FOLDER, exist_ok=True)
        path = os.path.join(self.MODELS_FOLDER, "random_forest_model.pkl")
        with open(path, "wb") as f:
            pickle.dump(self.model, f)

    def _load_model(self):
        path = os.path.join(self.MODELS_FOLDER, "random_forest_model.pkl")
        with open(path, "rb") as f:
            self.model = pickle.load(f)


random_forest_trainer = RandomForestTrainer()