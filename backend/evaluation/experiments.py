"""
Experiments (Similarity Evaluation)

Ye module manually diye gaye wallet pairs (jinka "expected" result
pehle se pata ho) par system ka score nikal kar compare karta hai —
taake pata chale system kitna accurate hai.
"""

from attribution.similarity import similarity_engine
from features.extractor import feature_extractor


class SimilarityExperiment:
    """
    Ye class known wallet pairs par similarity evaluation karti hai.
    """

    def evaluate_pair(self, wallet_1: str, wallet_2: str, wallet_1_csv: str,
                       wallet_2_csv: str, chain: str, expected: str) -> dict:
        """
        Ek wallet pair ka AI score nikalta hai aur expected result se compare karta hai.
        """
        profile_1 = feature_extractor.get_wallet_summary(wallet_1_csv, wallet_1, chain)
        profile_2 = feature_extractor.get_wallet_summary(wallet_2_csv, wallet_2, chain)

        result = similarity_engine.calculate_similarity_score(
            profile_1.to_dict(), profile_2.to_dict()
        )
        ai_score = result["overall_similarity_score"]

        predicted = "Same" if ai_score >= 0.5 else "Different"
        is_correct = predicted == expected

        return {
            "wallet_1": wallet_1,
            "wallet_2": wallet_2,
            "expected": expected,
            "predicted": predicted,
            "ai_score": round(ai_score, 2),
            "correct": is_correct,
        }

    def run_experiment(self, test_cases: list) -> dict:
        """
        Kai wallet pairs par evaluation chalata hai aur overall accuracy deta hai.
        """
        results = []

        for case in test_cases:
            result = self.evaluate_pair(
                case["wallet_1"], case["wallet_2"],
                case["wallet_1_csv"], case["wallet_2_csv"],
                case.get("chain", "ethereum"), case["expected"]
            )
            results.append(result)

        correct_count = sum(1 for r in results if r["correct"])
        total_count = len(results)
        accuracy = round((correct_count / total_count) * 100, 2) if total_count > 0 else 0.0

        return {
            "results": results,
            "accuracy": accuracy,
            "correct": correct_count,
            "total": total_count,
        }


similarity_experiment = SimilarityExperiment()