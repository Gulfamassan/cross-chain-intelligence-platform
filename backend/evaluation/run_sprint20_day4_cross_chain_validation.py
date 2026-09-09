"""
backend/evaluation/run_sprint20_day4_cross_chain_validation.py

Sprint 20, Day 4 — Cross-Chain Research Validation

Focused question: "Does the unified graph improve the cross-chain
Related detection problem identified in Sprint 14-16?"

Sirf 3 genuine "Related" cases (Sprint 16 ground truth) ko detail
mein dekhta hai — Old approach (Rule-Based, Sprint 14-16 ka original
baseline) VS GraphSAGE (single-chain, Sprint 18) VS Cross-Chain GNN
(unified graph, Sprint 19). Har case ke liye diagnostic bhi deta hai:
kya unified graph mein in wallets ke beech koi extra evidence-edge
bana (same_address/known_exchange/bridge) ya nahi.

Run from `backend/`: python -m evaluation.run_sprint20_day4_cross_chain_validation
"""

from evaluation.ground_truth import get_dataset
from evaluation.run_graphsage_comparison import resolve_csv_path
from evaluation.experiments import similarity_experiment
from evaluation.run_cross_chain_graphsage_training import build_wallet_chain_csvs

from ai.wallet_embeddings import classify_wallet_pair
from ai.cross_chain_wallet_embeddings import classify_cross_chain_pair
from graph.cross_chain_graph import build_unified_graph, _node_id


if __name__ == "__main__":
    dataset = get_dataset()
    related_cases = [c for c in dataset if c["ground_truth"] == "Related"]

    print("=" * 84)
    print(f"CROSS-CHAIN RESEARCH VALIDATION — {len(related_cases)} known Related cases")
    print("=" * 84)

    # Rule-Based (deterministic, fresh run for this specific subset)
    rule_report = similarity_experiment.run_ground_truth_experiment(dataset, resolve_csv_path)
    rule_by_case = {r["case_id"]: r for r in rule_report["results"]}

    # Unified graph banate hain (diagnostic evidence-edge check ke liye)
    print("\nBuilding unified graph for diagnostic evidence check...")
    wallet_chain_csvs = build_wallet_chain_csvs()
    unified_graph = build_unified_graph(wallet_chain_csvs)

    for case in related_cases:
        is_cross_chain = case["chain_a"].lower() != case["chain_b"].lower()

        print(f"\n{'-' * 84}")
        print(f"Case {case['case_id']} — Expected: Related — "
              f"{'CROSS-CHAIN' if is_cross_chain else 'SAME-CHAIN'} "
              f"({case['chain_a']} -> {case['chain_b']})")
        print(f"{'-' * 84}")
        print(f"  Wallet A: {case['wallet_a']} ({case['chain_a']})")
        print(f"  Wallet B: {case['wallet_b']} ({case['chain_b']})")

        # --- Old approach: Rule-Based ---
        rule_result = rule_by_case.get(case["case_id"])
        rule_predicted = rule_result["predicted"] if rule_result else "N/A"
        rule_score = rule_result.get("ai_score") if rule_result else "N/A"
        print(f"\n  [Old — Rule-Based]      predicted={rule_predicted:<10} score={rule_score}")

        # --- GraphSAGE (single-chain, Sprint 18) ---
        try:
            gs_result = classify_wallet_pair(case["wallet_a"], case["wallet_b"])
            print(f"  [GraphSAGE]             predicted={gs_result['classification']:<10} "
                  f"score={gs_result['score']}")
        except KeyError:
            print("  [GraphSAGE]             predicted=N/A (embedding not found)")

        # --- Cross-Chain GNN (unified graph, Sprint 19) ---
        try:
            wallet_1_full = f"{case['chain_a'].lower()}:{case['wallet_a']}"
            wallet_2_full = f"{case['chain_b'].lower()}:{case['wallet_b']}"
            cc_result = classify_cross_chain_pair(wallet_1_full, wallet_2_full)
            print(f"  [Cross-Chain GNN]       predicted={cc_result['classification']:<10} "
                  f"score={cc_result['score']}")
        except (KeyError, ValueError) as e:
            print(f"  [Cross-Chain GNN]       predicted=N/A ({e})")

        # --- Diagnostic: kya unified graph mein extra evidence-edge bana? ---
        node_1 = _node_id(case["wallet_a"], case["chain_a"])
        node_2 = _node_id(case["wallet_b"], case["chain_b"])

        evidence_found = []
        if unified_graph.has_edge(node_1, node_2):
            for _, _, data in unified_graph.get_edge_data(node_1, node_2).items():
                pass
            edge_data_list = unified_graph.get_edge_data(node_1, node_2)
            for key, data in edge_data_list.items():
                cat = data.get("edge_category")
                if cat and cat != "transaction":
                    evidence_found.append(cat)
        if unified_graph.has_edge(node_2, node_1):
            edge_data_list = unified_graph.get_edge_data(node_2, node_1)
            for key, data in edge_data_list.items():
                cat = data.get("edge_category")
                if cat and cat != "transaction":
                    evidence_found.append(cat)

        if evidence_found:
            print(f"\n  DIAGNOSTIC: Unified graph has EXTRA evidence edge(s): {set(evidence_found)}")
        else:
            print("\n  DIAGNOSTIC: Unified graph has NO extra evidence edge between these "
                  "two wallets (no same_address/bridge/known_exchange link found).")

    print(f"\n\n{'=' * 84}")
    print("SUMMARY")
    print("=" * 84)
    print("Har case ke result ko upar dekhein. Agar Cross-Chain GNN ne GraphSAGE se")
    print("behtar/barabar kiya AUR uske paas ek extra evidence-edge tha -> improvement")
    print("ka plausible reason mil gaya. Agar evidence-edge nahi tha aur result same/worse")
    print("hai -> ye confirm karta hai ke unified graph ka structural extension akela")
    print("kaafi nahi hai bina genuine (bridge) evidence ke.")