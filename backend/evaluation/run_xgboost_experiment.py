"""
backend/evaluation/run_xgboost_experiment.py

XGBoost ko Day 4 ke dev (n=4) set par train karta hai, phir held-out
(n=3) set par predict karta hai. Feature importance bhi dikhata hai.

⚠️ n=4 training set — statistically valid trained-model result NAHI
hai, sirf pipeline-demonstration hai. Dekhein ai/xgboost_model.py
docstring.

Run from `backend/`: python -m evaluation.run_xgboost_experiment
"""

from evaluation.graphsage_split import get_dev_cases, get_held_out_cases
from evaluation.run_graphsage_comparison import resolve_csv_path
from ai.feature_vector import build_feature_matrix, FEATURE_NAMES
from ai.xgboost_model import xgboost_trainer


if __name__ == "__main__":
    dev_cases = get_dev_cases()
    held_out_cases = get_held_out_cases()

    print("Building features for dev set (n=4)...")
    X_dev, y_dev = build_feature_matrix(dev_cases, resolve_csv_path)

    print("Building features for held-out set (n=3)...")
    X_held_out, y_held_out = build_feature_matrix(held_out_cases, resolve_csv_path)

    print("\nTraining XGBoost on dev set (n=4)...")
    print("*** CAVEAT: n=4 is NOT enough to train a statistically valid ***")
    print("*** classifier. This demonstrates the pipeline, not a real model. ***\n")
    xgboost_trainer.train(X_dev, y_dev)

    print("Feature importances (which signals the model leaned on):")
    for name, importance in sorted(xgboost_trainer.feature_importance().items(),
                                    key=lambda x: -x[1]):
        print(f"  {name:<35}{importance}")

    print("\nPredicting held-out set (n=3)...")
    predictions = xgboost_trainer.predict(X_held_out)

    correct = 0
    print(f"\n{'Case':<8}{'Expected':<12}{'Predicted':<12}{'Probability':<12}")
    print("-" * 44)
    for case, pred, label in zip(held_out_cases, predictions, y_held_out):
        expected = "Related" if label == 1 else "Unrelated"
        is_correct = expected == pred["predicted"]
        correct += is_correct
        status = "correct" if is_correct else "WRONG"
        print(f"{case['case_id']:<8}{expected:<12}{pred['predicted']:<12}"
              f"{pred['probability']:<12}[{status}]")

    print(f"\nHeld-out accuracy: {correct}/{len(held_out_cases)} "
          f"(n=3 — again, not a statistically meaningful percentage)")

    related_held_out = [c for c, l in zip(held_out_cases, y_held_out) if l == 1]
    related_correct = sum(
        1 for c, p, l in zip(held_out_cases, predictions, y_held_out)
        if l == 1 and p["predicted"] == "Related"
    )
    print(f"Related cases recovered (held-out): {related_correct}/{len(related_held_out)}")