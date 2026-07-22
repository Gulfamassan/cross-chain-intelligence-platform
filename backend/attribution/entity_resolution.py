"""
Entity Resolution

Ye module final decision leta hai ke kya multiple wallets ek hi
entity (user/organization) ke ho sakte hain, based on combined
evidence (bridge detection + similarity + heuristic scores).

Agar A-B same entity hain, aur B-C bhi same entity hain, to
A, B, C teeno ek hi entity group mein link ho jaate hain.
"""

from attribution.heuristics import heuristic_engine
from attribution.similarity import similarity_engine


class EntityResolver:
    """
    Ye class wallet pairs ko evaluate karke entity groups banati hai.
    """

    # Threshold — is se upar score ho to "Possible Same Entity" maana jayega
    ATTRIBUTION_THRESHOLD = 50

    def evaluate_wallet_pair(self, wallet_a_data: dict, wallet_b_data: dict, heuristic_inputs: dict) -> dict:
        """
        Ek wallet pair ko evaluate karta hai — similarity aur heuristic
        scores combine karke final decision deta hai.

        Args:
            wallet_a_data (dict): Wallet A ka feature profile (WalletProfile.to_dict())
            wallet_b_data (dict): Wallet B ka feature profile
            heuristic_inputs (dict): Heuristic rules ke liye zaroori data
                                      (bridge_tx_timestamp, receive_tx_timestamp,
                                      amount1, amount2, gas_price1, gas_price2,
                                      active_hours1, active_hours2, exchange1, exchange2)

        Returns:
            dict: Similarity score, heuristic score, combined verdict
        """
        # Behavior similarity nikalte hain
        similarity_result = similarity_engine.calculate_similarity_score(wallet_a_data, wallet_b_data)

        # Heuristic rules ka score nikalte hain
        heuristic_result = heuristic_engine.calculate_total_score(**heuristic_inputs)

        # Similarity ko 100 point scale par convert karte hain (abhi 0-1 hai)
        similarity_score_100 = similarity_result["overall_similarity_score"] * 100

        # Heuristic score (already 0-100) aur similarity score (0-100) ka average lete hain
        combined_score = (similarity_score_100 + heuristic_result["total_score"]) / 2

        is_same_entity = combined_score >= self.ATTRIBUTION_THRESHOLD

        return {
            "wallet_a": wallet_a_data.get("wallet_address"),
            "wallet_b": wallet_b_data.get("wallet_address"),
            "similarity_score": round(similarity_score_100, 2),
            "heuristic_score": heuristic_result["total_score"],
            "combined_score": round(combined_score, 2),
            "verdict": "Possible Same Entity" if is_same_entity else "Likely Different Entities",
            "is_same_entity": is_same_entity,
        }

    def resolve_entity_groups(self, evaluated_pairs: list) -> list:
        """
        Diye gaye evaluated pairs se entity groups banata hai — agar A-B
        same entity hain, aur B-C bhi same entity hain, to A, B, C
        teeno ek hi group mein aa jaate hain (chain linking).

        Args:
            evaluated_pairs (list): evaluate_wallet_pair() ke results ki list

        Returns:
            list: Entity groups ki list, har group wallets ka set hai
        """
        # Pehle sirf "same entity" wale pairs nikalte hain
        same_entity_pairs = [
            (pair["wallet_a"], pair["wallet_b"])
            for pair in evaluated_pairs
            if pair["is_same_entity"]
        ]

        groups = []

        for wallet_a, wallet_b in same_entity_pairs:
            # Check karo kya wallet_a ya wallet_b pehle se kisi group mein hai
            found_group = None
            for group in groups:
                if wallet_a in group or wallet_b in group:
                    found_group = group
                    break

            if found_group:
                found_group.add(wallet_a)
                found_group.add(wallet_b)
            else:
                groups.append({wallet_a, wallet_b})

        # Agar do groups overlap ho gaye hon (chain linking se), unhe merge karte hain
        merged = True
        while merged:
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    if groups[i].intersection(groups[j]):
                        groups[i] = groups[i].union(groups[j])
                        groups.pop(j)
                        merged = True
                        break
                if merged:
                    break

        return [list(group) for group in groups]


# Ek single instance banate hain jo poore project mein import hoga
entity_resolver = EntityResolver()