"""
backend/evaluation/test_error_regression.py

Sprint 20, Day 6 — Final Error & Regression Testing

9 deliberate edge cases + regression check on existing production
endpoints (`/attribution/analyze`, `/hybrid/analyze`) aur saare GNN
endpoints (Sprint 20 Day 1 se).

Goal: koi bhi test SERVER KO CRASH NAHI karni chahiye (uvicorn process
zinda rehna chahiye) — chahe response 400/404/500 ho, jab tak server
responsive rehta hai aur clean JSON error deta hai, wo PASS hai.
Sirf agar request HANG ho jaye (timeout) ya connection hi na bane,
wo genuine crash/hang hai — FAIL.

⚠️ Zaroori: Ye script LIVE server (localhost:8000) ke against chalta
hai. Kuch tests (Invalid address, Unsupported chain, API failure)
live blockchain API calls karte hain — internet chahiye.

Pehle server chalayein: uvicorn main:app --reload
Phir: python -m evaluation.test_error_regression
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

results = []


def record(category, description, passed, detail=""):
    results.append({"category": category, "description": description, "passed": passed, "detail": detail})
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {description}" + (f" — {detail}" if detail and not passed else ""))


def safe_request(method, path, **kwargs):
    """
    Request bhejta hai — agar server crash/hang ho (timeout, connection
    error), None return karta hai (genuine failure). Agar server ne
    KOI BHI response diya (chahe 4xx/5xx), wo True hai (server zinda hai).
    """
    try:
        r = requests.request(method, f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 0 — Missing Graph / Missing Model (run FIRST, before any training)")
    print("=" * 70)
    print("(NOTE: agar server pehle se use ho chuka hai is session mein,")
    print(" ye tests false-positive PASS de sakte hain kyunki graph/model")
    print(" already exist karte hain. Fresh restart pe sabse accurate hai.)\n")

    r = safe_request("POST", "/ai/train")
    record("Missing graph", "/ai/train without /build-graph first",
           r is not None, "no response — possible crash/hang" if r is None else "")

    r = safe_request("POST", "/ai/pyg-graphsage/train")
    record("Missing graph", "/ai/pyg-graphsage/train without /build-graph first",
           r is not None)

    r = safe_request("POST", "/ai/similarity", json={"wallet_1": "0xabc", "wallet_2": "0xdef"})
    record("Missing model", "/ai/similarity without training first", r is not None)

    r = safe_request("POST", "/cross-chain-gnn/similarity",
                      json={"wallet_1": "ethereum:0xabc", "wallet_2": "polygon:0xdef"})
    record("Missing model", "/cross-chain-gnn/similarity without build+train first", r is not None)

    print("\n" + "=" * 70)
    print("PHASE 1 — Invalid / Empty / Unsupported Inputs")
    print("=" * 70)

    r = safe_request("GET", "/wallet/ethereum/not_a_valid_address/transactions", params={"limit": 5})
    record("Invalid address", "GET /wallet/ethereum/not_a_valid_address/transactions", r is not None)

    r = safe_request("GET", "/wallet/ethereum/ /transactions", params={"limit": 5})
    record("Empty address", "GET /wallet/ethereum/ /transactions (whitespace)", r is not None)

    r = safe_request("GET", "/wallet/bnb/0xF977814e90dA44bFA03b6295A0616a897441aceC/transactions",
                      params={"limit": 5})
    record("Unsupported chain", "GET /wallet/bnb/.../transactions (BNB disabled)", r is not None)

    print("\n" + "=" * 70)
    print("PHASE 2 — Missing / Empty CSV")
    print("=" * 70)

    r = safe_request("POST", "/build-graph", json={"csv_path": "datasets/ethereum/does_not_exist_xyz.csv"})
    ok = r is not None and r.status_code == 404
    record("Missing CSV", "/build-graph with nonexistent CSV -> expect 404", ok,
           f"got {r.status_code if r else 'no response'}")

    r = safe_request("POST", "/build-graph",
                      json={"csv_path": "datasets/arbitrum/0x161ba15a5f335c9f06bb5bbb0a9ce14076fbb645.csv"})
    record("No transactions", "/build-graph with empty (0-byte) CSV", r is not None,
           f"status={r.status_code if r else 'no response'}")

    print("\n" + "=" * 70)
    print("PHASE 3 — Invalid Pair")
    print("=" * 70)

    r = safe_request("POST", "/attribution/analyze", json={
        "wallet_1": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "wallet_2": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "wallet_1_csv": "datasets/polygon/0xF977814e90dA44bFA03b6295A0616a897441aceC.csv",
        "wallet_2_csv": "datasets/polygon/0xF977814e90dA44bFA03b6295A0616a897441aceC.csv",
        "wallet_1_chain": "polygon", "wallet_2_chain": "polygon",
    })
    record("Invalid pair", "/attribution/analyze with wallet_1 == wallet_2", r is not None,
           f"status={r.status_code if r else 'no response'}")

    r = safe_request("POST", "/ai/feature-ml/predict", json={
        "wallet_1": "0xabc", "chain_1": "ethereum",
        "wallet_2": "0xdef", "chain_2": "polygon", "model": "not_a_real_model",
    })
    ok = r is not None and r.status_code == 400
    record("Invalid pair", "/ai/feature-ml/predict with invalid model name -> expect 400", ok,
           f"got {r.status_code if r else 'no response'}")

    print("\n\n" + "=" * 70)
    print("REGRESSION — Existing Production Endpoints")
    print("=" * 70)

    csv_a = "datasets/polygon/0xF977814e90dA44bFA03b6295A0616a897441aceC.csv"
    csv_b = "datasets/ethereum/0x28c6c06298d514db089934071355e5743bf21d60.csv"

    r = safe_request("POST", "/attribution/analyze", json={
        "wallet_1": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "wallet_2": "0x28c6c06298d514db089934071355e5743bf21d60",
        "wallet_1_csv": csv_a, "wallet_2_csv": csv_b,
        "wallet_1_chain": "polygon", "wallet_2_chain": "ethereum",
    })
    record("Regression", "/attribution/analyze (valid pair)", r is not None and r.status_code == 200,
           f"status={r.status_code if r else 'no response'}")

    r = safe_request("POST", "/hybrid/analyze", json={
        "wallet_1": "0xF977814e90dA44bFA03b6295A0616a897441aceC",
        "wallet_2": "0x28c6c06298d514db089934071355e5743bf21d60",
        "wallet_1_csv": csv_a, "wallet_2_csv": csv_b,
        "wallet_1_chain": "polygon", "wallet_2_chain": "ethereum",
    })
    record("Regression", "/hybrid/analyze (valid pair)", r is not None and r.status_code == 200,
           f"status={r.status_code if r else 'no response'}")

    print("\n" + "=" * 70)
    print("REGRESSION — GNN Endpoints (Sprint 20 Day 1)")
    print("=" * 70)

    r = safe_request("POST", "/build-graph", json={"csv_path": csv_a})
    record("Regression", "/build-graph (setup for GraphSAGE)", r is not None and r.status_code == 200)

    r = safe_request("POST", "/ai/pyg-graphsage/train")
    record("Regression", "/ai/pyg-graphsage/train", r is not None,
           f"status={r.status_code if r else 'no response'}")

    r = safe_request("POST", "/ai/feature-ml/train")
    record("Regression", "/ai/feature-ml/train", r is not None and r.status_code == 200,
           f"status={r.status_code if r else 'no response'}")

    r = safe_request("POST", "/cross-chain-gnn/build-graph", json={
        "csvs": [{"csv_path": csv_a, "chain": "polygon"}, {"csv_path": csv_b, "chain": "ethereum"}]
    })
    record("Regression", "/cross-chain-gnn/build-graph", r is not None and r.status_code == 200,
           f"status={r.status_code if r else 'no response'}")

    r = safe_request("POST", "/cross-chain-gnn/train")
    record("Regression", "/cross-chain-gnn/train", r is not None,
           f"status={r.status_code if r else 'no response'}")

    # --- Final summary ---
    print("\n\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"{passed}/{total} checks passed\n")
    for r in results:
        if not r["passed"]:
            print(f"  FAILED: [{r['category']}] {r['description']} — {r['detail']}")

    if passed == total:
        print("\nNo crashes, no hangs, no broken endpoints detected.")