# Sprint 19 — Day 7: Final Model Evaluation Report

## Final Comparison Table

| Model | Scope | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Rule-Based | n=7 | 28.57% | 0.0 | 0.0 | 0.0 |
| Node2Vec | n=7 | 57.14% | 0.0 | 0.0 | 0.0 |
| Hybrid | n=7 | 42.86% | 0.0 | 0.0 | 0.0 |
| **GraphSAGE (Sprint 18)** | n=7 | 57.14% | 0.5 | 0.3333 | 0.4 |
| **Cross-Chain GraphSAGE (Sprint 19)** | n=7 | 28.57% | 0.0 | 0.0 | 0.0 |
| Random Forest | n=3 (held-out) | 66.67% | 0.5 | 1.0 | 0.6667 |
| XGBoost | n=3 (held-out) | 33.33% | 0.3333 | 1.0 | 0.5 |

## Related / Unrelated Detection Breakdown

| Model | Related | Unrelated | False Positives | False Negatives |
|---|---|---|---|---|
| Rule-Based | 0/3 | 2/4 | 2 | 3 |
| Node2Vec | 0/3 | 4/4 | 0 | 3 |
| Hybrid | 0/3 | 3/4 | 1 | 3 |
| **GraphSAGE (Sprint 18)** | **1/3** | 3/4 | **1** | 2 |
| **Cross-Chain GraphSAGE (Sprint 19)** | **0/3** | 2/4 | **2** | 3 |
| Random Forest | 1/1 | 1/2 | 1 | 0 |
| XGBoost | 1/1 | 0/2 | 2 | 0 |

## Cross-Chain Subset Only (5 of 7 cases where chain_a ≠ chain_b)

| Model | Cross-chain Related | Cross-chain Unrelated |
|---|---|---|
| Rule-Based | 0/2 | 2/3 |
| Node2Vec | 0/2 | 3/3 |
| Hybrid | 0/2 | 3/3 |
| **GraphSAGE (Sprint 18)** | **1/2** | 2/3 |
| **Cross-Chain GraphSAGE (Sprint 19)** | **0/2** | **1/3** |

---

## Headline Finding — Honest, Not Spun

**Sprint 19 ka pura research objective tha: "Kya true cross-chain unified graph (chain-aware nodes, bridge/entity evidence edges) controlled single-chain GraphSAGE (Sprint 18) se behtar attribution deta hai?"**

**`n=7` dataset ke saath, honest answer hai: NAHI.** Cross-Chain GraphSAGE ne:
- `0/3` Related pakde (Sprint 18 ke `1/3` se **kharab**)
- `2` False Positives diye (Sprint 18 ke `1` se **zyada**)
- Cross-chain subset (jo iska poora target tha) par bhi Sprint 18 se **kharab** perform kiya (`0/2` vs `1/2` Related)

## Kyun Aisa Hua Ho Sakta Hai (Hypotheses, Proof Nahi)

1. **Bridge evidence bilkul missing tha** (Day 3 confirm: `0` bridge transactions poore dataset mein). Sprint 19 ka sabse strong evidence-type (`weight=0.5`) kabhi contribute nahi kar saka — model ko sirf `same_address` aur `known_exchange` edges mile, jo weaker signals hain.
2. **Bada, complex graph, same chhota data** — `251` nodes/`11` features (vs Sprint 18 ka `183`/`8`) matlab zyada parameters seekhne hain usi `n=7` labeled evaluation set ke saath — signal-to-noise ratio kharab ho sakta hai.
3. **Naye edge-types (`same_address`, `known_exchange`) shayad in specific `7` cases ke liye helpful nahi the**, ya unhone conflicting signal diya (jaise ek False Positive un edges ki wajah se trigger hua ho — isay verify karne ke liye specific case-level investigation chahiye hogi, jo abhi nahi ki).

## Critical Honest Caveat

**Ye result "Cross-Chain GraphSAGE bekar hai" prove NAHI karta.** `n=7` itna chhota hai ke:
- Ek single case ka result flip hona (jaisa yahan hua) poori tarah **noise** ho sakta hai, genuine regression nahi
- **Bridge evidence ka bilkul na hona** iska sabse bada confound hai — agar dataset mein genuine bridge transactions hote, result alag ho sakta tha
- Isay dobara chalana (different random seed) different result de sakta hai — humne ye check nahi kiya (future work)

## Sprint 17 Se Sprint 19 Tak — Overall Research Answer

> "Determine whether graph-based representation learning improves
> cross-chain wallet attribution over rule-based behavioral similarity."

**3 sprints ke baad, honest, defensible answer:**
1. GraphSAGE architecture *khud* mein promise dikhata hai (Sprint 18 — `1/3` Related, controlled false positives) — behtar Rule/Node2Vec/Hybrid se is specific case mein
2. **Cross-chain-specific evidence (bridges, same-address linking) ne is chhote dataset mein improvement nahi diya** — ya to (a) evidence khud dataset mein nahi tha (bridge=0), ya (b) `n=7` itna chhota hai ke koi bhi conclusion statistically fragile hai
3. **Sabse honest overall conclusion:** *"Is n=7 case-study se hum ye claim NAHI kar sakte ke cross-chain-aware GNN architecture attribution improve karta hai. Jo hum keh sakte hain: bunyadi GraphSAGE architecture ek weak-but-nonzero signal deta hai; cross-chain-specific extensions ko properly evaluate karne ke liye — khaas kar bridge-evidence ke saath — kaafi zyada labeled data (n=30+) aur genuine bridge-transaction-containing dataset chahiye hoga."*