# Sprint 20 — Day 3: Final Attribution Benchmark (FROZEN)

**Dataset:** Sprint 16's n=7 verified wallet pairs (`evaluation/ground_truth.py`)
**Execution:** Fresh, single consolidated run — `evaluation/run_sprint20_final_benchmark.py`
**Data integrity note:** A Day 2 validation script accidentally overwrote 2 of
the shared wallet CSVs with live blockchain data (same addresses are reused
in the n=7 ground truth set). This was caught, the original Sprint 17
baseline CSVs were restored via `git checkout 610acfe -- backend/datasets/`,
and the benchmark below is from the corrected, uncontaminated re-run.

## Final Comparison Table

| Model | Scope | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Rule-Based | n=7 | 28.57% | 0.0 | 0.0 | 0.0 |
| Node2Vec | n=7 | 57.14% | 0.0 | 0.0 | 0.0 |
| Random Forest | n=3 (held-out) | 66.67% | 0.5 | 1.0 | 0.6667 |
| XGBoost | n=3 (held-out) | 33.33% | 0.3333 | 1.0 | 0.5 |
| **GraphSAGE** | n=7 | **71.43%** | **1.0** | 0.3333 | 0.5 |
| Cross-Chain GNN | n=7 | 42.86% | 0.3333 | 0.3333 | 0.3333 |

## Related / Unrelated Detection Breakdown

| Model | Related | Unrelated | False Positives | False Negatives |
|---|---|---|---|---|
| Rule-Based | 0/3 | 2/4 | 2 | 3 |
| Node2Vec | 0/3 | 4/4 | 0 | 3 |
| Random Forest | 1/1 | 1/2 | 1 | 0 |
| XGBoost | 1/1 | 0/2 | 2 | 0 |
| **GraphSAGE** | 1/3 | **4/4** | **0** | 2 |
| Cross-Chain GNN | 1/3 | 2/4 | 2 | 2 |

---

## Headline Finding

**GraphSAGE (Sprint 18, single/controlled graph) is `3`-sprint journey ka sabse strong result hai** — `71.43%` accuracy, `Precision 1.0` (matlab is run mein **koi bhi False Positive nahi**), aur `4/4` Unrelated wallets sahi identify kiye.

**Cross-Chain GNN (Sprint 19) ne is baar bhi single-chain GraphSAGE ko outperform nahi kiya** — teesri baar consistently (Sprint 19 Day 7 mein bhi yehi pattern tha). Isay ab ek **repeated, consistent finding** maan sakte hain, na ke ek-baar ki fluke:

> Cross-chain-specific evidence (bridges, same-address linking) ne is `n=7` case-study mein kabhi single-chain GraphSAGE se behtar perform nahi kiya. Sabse bada confound: dataset mein **`0` bridge transactions** hain (Sprint 19 Day 3 confirm), isliye Cross-Chain GNN ka sabse strong intended signal kabhi contribute nahi kar saka.

## Run-to-Run Variance (Important Honesty Note)

GraphSAGE ka accuracy alag-alag runs mein **`0.5714` → `0.5714` → `0.7143`** raha hai poori Sprint 17-19-20 journey mein. Root cause: `RandomLinkSplit` ka train/val edge-split **fixed seed nahi hai** (sirf model weights `torch.manual_seed(42)` se seeded hain). Chhote `n=7` graph par ye variance expected hai.

**Isliye `71.43%` ko "GraphSAGE ki guaranteed performance" NAHI samjhein** — ye is specific run ka result hai. Agar dobara chalayein, number thoda upar-neeche ho sakta hai. Jo **consistent** raha hai across saari runs:
- GraphSAGE ne har baar kam-se-kam `1` genuine Related case pakda (Sprint 18, 19, aur ab yahan bhi)
- Cross-Chain GNN ne kabhi single-chain GraphSAGE se behtar nahi kiya

## Final, Defensible Research Conclusion (Sprint 17-20)

1. **Rule-Based aur Node2Vec (behavioral similarity ke tareeqe) consistently `0/3` Related detect karte hain** — ye poore project ka sabse robust, repeated finding hai (Sprint 14-20 tak)
2. **GraphSAGE architecture khud mein genuine, repeated promise dikhata hai** — chhota, lekin consistent signal (kam se kam `1` Related case, controlled false positives)
3. **Cross-chain-specific graph extensions (Sprint 19) ne is dataset mein improvement nahi diya** — sabse bada confound bridge-evidence ka bilkul na hona hai, na ke architecture ka fundamentally kharab hona
4. **Random Forest/XGBoost ke `n=3` results statistically fragile hain** (`n=4` training) — inhe "trained models" ke taur par trust nahi karna chahiye, sirf pipeline demonstration
5. **Sabse honest overall verdict:** *"`n=7` case-study se hum keh sakte hain ke GraphSAGE-based approaches Rule/Node2Vec se behtar directional signal dikhate hain, lekin ye claim statistically weak hai. Cross-chain-specific evidence ka fayda is dataset mein prove nahi hua — bridge-transaction-containing, bade (`n=30+`) labeled dataset ke bina ye question genuinely open rehta hai."*