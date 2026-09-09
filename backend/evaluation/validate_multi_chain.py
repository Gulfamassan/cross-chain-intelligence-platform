"""
backend/evaluation/validate_multi_chain.py

Sprint 20, Day 2 — Multi-Chain Validation

Ethereum, Polygon, Arbitrum — teeno chains ko LIVE API (localhost
par chal rahe uvicorn server) se test karta hai, poori pipeline ke
saath (Wallet Search se GNN tak). BNB test NAHI karta (registered
collector hi nahi hai — `blockchain/chain_manager.py` mein comment-out
hai — isliye "working chain" claim karna galat hoga).

⚠️ Zaroori: Ye script LIVE blockchain API calls karta hai
(`/wallet/{chain}/{address}/transactions`) — internet aur configured
API keys (.env) chahiye. Sandbox mein test nahi ho sakta, sirf
aapke apne machine par.

Pehle server chalayein (alag terminal mein):
    uvicorn main:app --reload

Phir isay chalayein (ek aur terminal mein):
    pip install requests
    python -m evaluation.validate_multi_chain
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
CHAINS = ["ethereum", "polygon", "arbitrum"]

# Well-known, publicly active addresses — teeno EVM chains par
# transactions milne ka strong chance hai
WALLET_A = "0x71660c4005ba85c37ccec55d0c4493e66fe775d3"
WALLET_B = "0xF977814e90dA44bFA03b6295A0616a897441aceC"  # Binance hot wallet


def check(label: str, fn):
    """
    Ek check chalata hai, exception ko gracefully handle karta hai,
    result print karta hai, aur True/False return karta hai.
    """
    try:
        fn()
        print(f"    {label:<15} PASS")
        return True
    except Exception as e:
        print(f"    {label:<15} FAIL — {e}")
        return False


def post(path, body):
    r = requests.post(f"{BASE_URL}{path}", json=body, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    return r.json()


def get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", params=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    return r.json()


if __name__ == "__main__":
    results_matrix = {}

    csv_paths = {}  # {chain: {wallet: csv_path}}

    for chain in CHAINS:
        print(f"\n{'=' * 50}")
        print(f"Chain: {chain.upper()}")
        print("=" * 50)

        csv_paths[chain] = {}
        results_matrix[chain] = {}

        # 1. Wallet Search + Transactions
        def _fetch_wallet_a():
            data = get(f"/wallet/{chain}/{WALLET_A}/transactions", {"limit": 25})
            csv_paths[chain][WALLET_A] = data["csv_saved_at"]

        results_matrix[chain]["Wallet Search"] = check("Wallet Search", _fetch_wallet_a)
        results_matrix[chain]["Transactions"] = WALLET_A in csv_paths[chain]

        def _fetch_wallet_b():
            data = get(f"/wallet/{chain}/{WALLET_B}/transactions", {"limit": 25})
            csv_paths[chain][WALLET_B] = data["csv_saved_at"]

        check("Wallet B fetch", _fetch_wallet_b)

        if WALLET_A not in csv_paths[chain]:
            print(f"  [skip rest] Wallet Search failed for {chain} — baaki checks skip")
            for label in ["Features", "Graph", "Risk", "Attribution", "GNN"]:
                results_matrix[chain][label] = False
            continue

        csv_a = csv_paths[chain][WALLET_A]

        # 2. Features
        results_matrix[chain]["Features"] = check(
            "Features", lambda: post("/extract-features", {
                "csv_path": csv_a, "wallet_address": WALLET_A, "chain": chain
            })
        )

        # 3. Graph
        results_matrix[chain]["Graph"] = check(
            "Graph", lambda: post("/build-graph", {"csv_path": csv_a})
        )

        # 4. Risk
        results_matrix[chain]["Risk"] = check(
            "Risk", lambda: post("/risk/analyze", {
                "wallet": WALLET_A, "csv_path": csv_a, "chain": chain
            })
        )

        # 5. Attribution (same-chain pair, agar wallet_b bhi mil gaya)
        if WALLET_B in csv_paths[chain]:
            csv_b = csv_paths[chain][WALLET_B]
            results_matrix[chain]["Attribution"] = check(
                "Attribution", lambda: post("/attribution/analyze", {
                    "wallet_1": WALLET_A, "wallet_2": WALLET_B,
                    "wallet_1_csv": csv_a, "wallet_2_csv": csv_b,
                    "wallet_1_chain": chain, "wallet_2_chain": chain,
                })
            )
        else:
            print("    Attribution      SKIP — Wallet B data nahi mila")
            results_matrix[chain]["Attribution"] = False

        # 6. GNN (PyG GraphSAGE — is chain ke controlled graph par)
        def _gnn_check():
            post("/ai/pyg-graphsage/train", {})

        results_matrix[chain]["GNN"] = check("GNN (GraphSAGE)", _gnn_check)

    # 7. Cross-chain (Hybrid, cross-chain pairs — chain rotation)
    print(f"\n{'=' * 50}")
    print("CROSS-CHAIN CHECKS (Hybrid, alag chains ke beech)")
    print("=" * 50)

    cross_chain_results = {}
    for i, chain_1 in enumerate(CHAINS):
        chain_2 = CHAINS[(i + 1) % len(CHAINS)]
        if WALLET_A not in csv_paths.get(chain_1, {}) or WALLET_B not in csv_paths.get(chain_2, {}):
            print(f"  {chain_1} <-> {chain_2}: SKIP (data missing)")
            cross_chain_results[f"{chain_1}->{chain_2}"] = False
            continue

        def _cross_chain_check():
            post("/hybrid/analyze", {
                "wallet_1": WALLET_A, "wallet_2": WALLET_B,
                "wallet_1_csv": csv_paths[chain_1][WALLET_A],
                "wallet_2_csv": csv_paths[chain_2][WALLET_B],
                "wallet_1_chain": chain_1, "wallet_2_chain": chain_2,
            })

        cross_chain_results[f"{chain_1}->{chain_2}"] = check(
            f"{chain_1}->{chain_2}", _cross_chain_check
        )

    # --- Final matrix ---
    print(f"\n\n{'=' * 60}")
    print("FINAL VALIDATION MATRIX")
    print("=" * 60)
    checks = ["Wallet Search", "Transactions", "Features", "Graph", "Risk",
              "Attribution", "GNN"]
    print(f"{'Check':<16}" + "".join(f"{c.capitalize():<12}" for c in CHAINS))
    print("-" * 60)
    for check_name in checks:
        row = f"{check_name:<16}"
        for chain in CHAINS:
            status = "PASS" if results_matrix.get(chain, {}).get(check_name) else "FAIL"
            row += f"{status:<12}"
        print(row)

    print("\nCross-chain:")
    for pair, status in cross_chain_results.items():
        print(f"  {pair}: {'PASS' if status else 'FAIL'}")

    print("\n(GUI check is manual — open the frontend and try each chain "
          "in the search box.)")
    print("\nBNB: NOT tested — collector is disabled in blockchain/chain_manager.py")