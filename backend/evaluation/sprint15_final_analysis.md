# Sprint 15 — Entity Agreement Signal: Final Analysis

**Status:** Complete — Frozen (not integrated into production)
**Dataset:** Same 3 verified ground-truth cases used across Sprint 14 (see `evaluation/ground_truth.py`)
**⚠️ n=3 — no statistical significance claims are made.**

---

## 1. Objective

Sprint 14 identified that no tested signal (bridge evidence, missing-aware
fusion) improved detection of the one genuine cross-chain "Related" case
(Case 3). Sprint 15 investigated one additional candidate signal: **entity
classification agreement** — whether two wallets independently classified
by `entity_labeling.resolve_entity()` (Sprint 12) agree on entity type.

---

## 2. Ablation Analysis (Day 5)

| Model | Signals Included | Case 1 (Unrelated) | Case 2 (Unrelated) | Case 3 (Related) |
|---|---|---|---|---|
| Rule only | Rule | 0.5384 | 0.7045 | 0.2193 |
| Baseline Hybrid | Rule + Node2Vec + Graph | 0.24 | 0.30 | 0.11 |
| Missing-Aware | Rule + Node2Vec + Graph (excluded when missing) | 0.28 | 0.30 | 0.13 |
| Cross-Chain | Rule + Node2Vec + Graph + Bridge-Evidence | 0.24 | 0.30 | 0.11 |
| Entity-Aware | Rule + Node2Vec + Graph + Entity Agreement | 0.22 | 0.29 | 0.10 |

**Finding:** Rule-based score alone (0.2193) was the strongest signal for
Case 3 of all approaches tested. Every additional signal (Node2Vec, Graph,
Bridge-Evidence, Entity Agreement) either had no effect or diluted the
score slightly. No combination reached the 0.5 classification threshold.

---

## 3. Entity Agreement Signal — Investigation Summary (Days 1–4)

- **Day 1:** Confirmed a three-state model (MATCH / NO_MATCH / UNKNOWN) was
  necessary — the existing `entity_labeling` classifier already supports this.
- **Day 2:** At confidence threshold 0.5, the signal produced confidently
  *wrong* answers (Case 1 & 2 → MATCH; Case 3 → NO_MATCH — all incorrect).
  Raising the threshold to 0.75 made the signal honestly report UNKNOWN in
  all three cases — safe, but uninformative on this dataset.
- **Day 3:** Wired into an experimental fusion method
  (`combine_scores_with_entity_agreement()`) with a transparent, conservative
  weight (0.05 in `config/weights.json`) — the smallest of all weights,
  reflecting the signal's unproven status.
- **Day 4:** Re-ran the exact 3 cases. Case 3 result: **0.11 → 0.11 (no
  change)**. Classified as "No Improvement" per the pre-defined success
  criteria (Strong / Partial / No Improvement).

**Root cause:** `wallet_classifier.py`'s heuristic confidence (60%) never
clears a trustworthy threshold, so the agreement signal is UNKNOWN for any
wallet not already in the known-address list. This is a data/calibration
limitation, not a logic error in the agreement-comparison itself.

---

## 4. Regression Testing (Day 6)

| Check | Status | Evidence |
|---|---|---|
| Same-chain (Case 2) | ✅ Stable | 0.30 → 0.29 (negligible, rounding-level) |
| Cross-chain unrelated (Case 1) | ✅ Stable | 0.24 → 0.22 (negligible, rounding-level) |
| `POST /attribution/analyze` | ✅ Pass | Unaffected — does not use `fusion.py` |
| `POST /hybrid/analyze` | ✅ Pass | Unaffected — production path still calls `combine_scores()`, not the experimental method |
| GUI (Wallet Analysis, Cross-Chain, Risk, Graph, Report) | ✅ Pass | Confirmed working in Sprint 14 Day 7; no changes made to production paths in Sprint 15 |

**Zero regression risk by design:** `combine_scores_with_entity_agreement()`
was never wired into `/hybrid/analyze` or any production code path — it
exists only as a standalone, evaluated experiment. Production behavior is
byte-for-byte unchanged.

---

## 5. Final Decision (Day 7)

```
Entity Signal → Evaluation → No useful improvement → FREEZE
```

**Decision: Freeze. Do not integrate into production fusion.**

- `attribution/entity_agreement.py` and
  `hybrid/fusion.py::combine_scores_with_entity_agreement()` remain in the
  codebase as documented research artifacts, validated against ground truth.
- Production fusion (`combine_scores()`, used by `/hybrid/analyze`) is
  **not modified** and continues to use only Rule, Node2Vec, Graph, and Risk.
- No further attribution-improvement signals will be added in pursuit of
  pushing Case 3 above the 0.5 threshold — per the pre-agreed stopping rule
  ("do not keep adding signals indefinitely").

---

## 6. Consolidated Research Conclusion (Sprint 14 + 15)

Across five independent signals/experiments — missing-signal-aware fusion,
cross-chain bridge-evidence, and entity-classification agreement — none
produced a significant improvement on the one verified cross-chain
"Related" case in the ground truth dataset. This indicates the limitation
is not any single missing signal, but a more fundamental gap: the small
transaction sample size available for the test wallets prevents the
heuristic classifier, bridge-timing correlation, and embedding similarity
from all reaching usable confidence simultaneously.

**Highest-value future work, in priority order:**
1. Expand the ground truth dataset beyond n=3 for statistically meaningful evaluation.
2. Expand the known-address list (`entity_labeling/label_database.py`) — the
   only signal that reliably reached high confidence (99%) in this project.
3. Build a true unified cross-chain graph (Sprint 14 Day 5 design document),
   which may reveal indirect multi-hop connections invisible to pairwise
   bridge-transaction correlation.

Additional fusion signals are **not** recommended as the next step, based
on the consistent ablation results above.