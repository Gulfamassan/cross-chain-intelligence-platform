# Sprint 14 — Day 7 Final Validation & Research Summary

**Status:** Complete
**Dataset:** 3 verified ground-truth wallet pairs (see `evaluation/ground_truth.py`)
**⚠️ n=3 — no statistical significance claims are made. This is a qualitative case study, not a statistically powered evaluation.**

---

## 1. Ground Truth Dataset

| Case | Wallet A | Chain A | Wallet B | Chain B | Ground Truth | Basis |
|---|---|---|---|---|---|---|
| 1 | `0xd8dA6BF2...aA96045` | ethereum | `0xF977814e...441aceC` | polygon | Unrelated | A = Personal Wallet (system-classified); B = verified Binance Hot Wallet 20 |
| 2 | `0xd8dA6BF2...aA96045` | polygon | `0xF977814e...441aceC` | polygon | Unrelated | Same pair, same-chain control |
| 3 | `0x28c6c062...43bf21d60` | ethereum | `0xF977814e...441aceC` | polygon | **Related** | Both publicly verified Binance-owned wallets (Binance 14 & Binance Hot Wallet 20) |

---

## 2. Four-Way Comparison — Actual Results

| Case | Expected | Rule | Baseline Hybrid (Day 3) | Missing-Aware (Day 4) | Cross-Chain Hybrid (Day 6/7) |
|---|---|---|---|---|---|
| 1 | Unrelated | 0.5384 | 0.24 | 0.28 | 0.24 |
| 2 | Unrelated | 0.7045 | 0.30 | 0.30 | 0.30 |
| 3 | **Related** | 0.2193 | 0.11 | 0.13 | 0.11 |

**Case 2 (control) unchanged across all four approaches (0.30 throughout)** — confirms same-chain behavior was never affected by any Sprint 14 experiment. No regression.

**Case 3 (main research case):**
- Score improvement: baseline (0.11) → Day 6 (0.11) — **no change**
- Classification: 0.11 < 0.5 threshold → predicted "Unrelated" — **still incorrect** (expected "Related")
- Cross-chain evidence check: `available: true`, `source: "no_bridge_activity"`, `matched_bridge_pairs: 0` — the check ran correctly, but found no bridge-timing/amount correlation between the two wallets

---

## 3. Classification Metrics (Day 6/7 Cross-Chain Hybrid)

Threshold = 0.5, positive class = "Related"

| Metric | Value |
|---|---|
| True Positive | 0 |
| False Positive | 2 |
| True Negative | 0 |
| False Negative | 1 |
| Precision | 0.0 |
| Recall | 0.0 |
| F1-Score | 0.0 |
| Accuracy | 0.0 |
| False Positive Rate | 1.0 |
| False Negative Rate | 1.0 |

Identical to the Baseline Hybrid metrics (Day 2) — the cross-chain signal did not change any classification outcome on this dataset.

---

## 4. Regression Testing

| Component | Status | Evidence |
|---|---|---|
| `POST /attribution/analyze` | ✅ Pass | `similarity: 0.5384` — matches Rule score across all four days, unchanged |
| `POST /hybrid/analyze` | ✅ Pass | `cross_chain_evidence` block present, `confidence: 23.54%`, consistent with terminal experiment |
| Same-chain relationship scoring | ✅ Pass | `source: "graph"` for same-chain pairs — unit test confirms unchanged behavior |
| Ethereum / Polygon / Arbitrum data pipeline | ✅ Pass (indirect) | All datasets used successfully throughout Sprint 14 without errors |
| GUI — full workflow | ✅ Pass | Wallet analysis, Entity Intelligence, Cross-Chain Evidence panel, Recommendation, Summary, Timeline all rendered correctly with no errors |
| Unit tests (`test_cross_chain_evidence.py`) | ✅ Pass | 3/3 tests passed — same-chain unchanged, cross-chain evidence structure correct, missing evidence stays at 0.0 |

---

## 5. Final Research Finding

**Outcome: C — No meaningful improvement, with a valuable diagnostic insight.**

> The cross-chain bridge-evidence signal (Sprint 14 Day 6) was successfully implemented and integrated into the existing Hybrid Attribution pipeline without breaking any existing functionality (same-chain cases, `/attribution/analyze`, `/hybrid/analyze`, and the GUI all continued to work as before). However, it did not improve the score or classification for the one genuine "Related" case in the ground truth dataset.
>
> Investigation traced this to a root cause distinct from the original single-chain graph limitation (Day 5): the two verified Binance-owned wallets in Case 3 have no direct bridge transaction between them in the available transaction data. Their relationship is **ownership-level** (both independently identifiable as Binance via known-address labeling — see Sprint 12's `entity_labeling` module) rather than **transaction-level** (a bridge transfer moving funds from one wallet to the other).
>
> **Conclusion:** Bridge-transaction correlation alone is not a sufficient signal for all forms of cross-chain relationships. The current evidence suggests two directions for future work:
> 1. A larger, unified cross-chain graph (as originally scoped in Day 5's design document) may still reveal indirect multi-hop connections not visible to this pairwise approach.
> 2. Incorporating **entity-classification agreement** (both wallets independently classified as the same known entity type, e.g. "Exchange Wallet") as an additional fusion signal — since this is the only Sprint 12/13/14 signal that would have correctly flagged Case 3 as related, and it is not currently part of the Hybrid fusion formula.

---

## 6. Sprint 14 — Complete Timeline

| Day | Deliverable |
|---|---|
| 1 | Ground truth dataset (verified Related/Unrelated pairs) |
| 2 | Classification metrics framework (Precision/Recall/F1/FPR/FNR) |
| 3 | Rule vs Node2Vec vs Hybrid benchmark |
| 4 | Missing-signal fusion experiment (zero-substitution vs exclusion) |
| 5 | Cross-chain graph architecture investigation & design document |
| 6 | Cross-chain bridge-evidence signal — implemented, tested, wired to API + GUI |
| 7 | Final re-validation, regression testing, and consolidated research finding |