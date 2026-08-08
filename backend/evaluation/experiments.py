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
    def evaluate_pair_cross_chain(self, wallet_1: str, chain_1: str, wallet_1_csv: str,
                                    wallet_2: str, chain_2: str, wallet_2_csv: str,
                                    expected: str) -> dict:
        """
        Sprint 14 Day 2 addition — same as evaluate_pair(), but supports
        two DIFFERENT chains for wallet_1 and wallet_2. The original
        evaluate_pair() only accepts a single shared `chain`, which is
        incorrect for genuinely cross-chain pairs.
        """
        profile_1 = feature_extractor.get_wallet_summary(wallet_1_csv, wallet_1, chain_1)
        profile_2 = feature_extractor.get_wallet_summary(wallet_2_csv, wallet_2, chain_2)

        result = similarity_engine.calculate_similarity_score(
            profile_1.to_dict(), profile_2.to_dict()
        )
        ai_score = result["overall_similarity_score"]

        predicted = "Related" if ai_score >= 0.5 else "Unrelated"
        is_correct = predicted == expected

        return {
            "wallet_1": wallet_1,
            "chain_1": chain_1,
            "wallet_2": wallet_2,
            "chain_2": chain_2,
            "expected": expected,
            "predicted": predicted,
            "ai_score": round(ai_score, 2),
            "correct": is_correct,
        }

    def run_ground_truth_experiment(self, ground_truth_cases: list, csv_path_resolver) -> dict:
        """
        Sprint 14 Day 2 addition — runs evaluate_pair_cross_chain() over
        every case in the ground_truth dataset (see ground_truth.py).

        Args:
            ground_truth_cases: list of dicts from ground_truth.get_dataset()
            csv_path_resolver: function(wallet_address, chain) -> csv_path,
                                so this method doesn't hardcode the dataset
                                folder convention itself

        Returns:
            dict: results per case, plus overall accuracy
        """
        results = []

        for case in ground_truth_cases:
            csv_1 = csv_path_resolver(case["wallet_a"], case["chain_a"])
            csv_2 = csv_path_resolver(case["wallet_b"], case["chain_b"])

            result = self.evaluate_pair_cross_chain(
                case["wallet_a"], case["chain_a"], csv_1,
                case["wallet_b"], case["chain_b"], csv_2,
                case["ground_truth"],
            )
            result["case_id"] = case["case_id"]
            result["basis"] = case["basis"]
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