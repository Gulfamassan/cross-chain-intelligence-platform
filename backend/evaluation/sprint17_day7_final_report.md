# Sprint 17 — Day 7: Final GNN Experiment Report

**Dataset:** n=7 verified wallet pairs (`evaluation/ground_truth.py`) — 3 "Related", 4 "Unrelated".
**Disclaimer (Day 4):** Ye ek chhota case-study hai, statistically reliable ML benchmark NAHI hai.
Har number ko qualitative signal maanein, general-purpose accuracy claim nahi.

## Final Comparison Table

| Method | Accuracy | Precision | Recall | F1 | Related Recovered |
|---|---|---|---|---|---|
| Rule | 28.57% | 0.0 | 0.0 | 0.0 | 0/3 |
| Node2Vec | 57.14% | 0.0 | 0.0 | 0.0 | 0/3 |
| Hybrid | 42.86% | 0.0 | 0.0 | 0.0 | 0/3 |
| GraphSAGE | 57.14% | 0.0 | 0.0 | 0.0 | 0/3 |
| Cross-Chain GraphSAGE | 28.57% | 0.0 | 0.0 | 0.0 | 0/3 |

## Headline Finding

**Koi bhi method — Rule, Node2Vec, Hybrid, GraphSAGE, ya Cross-Chain
GraphSAGE — ek bhi genuine "Related" case sahi predict nahi kar
saka.** Ye Sprint 14-16 ke pehle-se-documented finding
(`final_benchmark_report.md`) ko is naye GraphSAGE experiment ke
saath bhi confirm karta hai — same-entity exchange wallets ka
behavior (transaction pattern) itna alag hota hai ke koi bhi
behavioral-similarity-based approach unhe link nahi kar pa raha.

---

## Method-by-Method: Kahan Succeed/Fail Hua

### 1. Rule (Accuracy 28.57%)
- **Fail:** Related cases 0/3 — rule-based similarity engine ka
  static thresholding exchange-wallet behavior ko capture nahi karta.
- Sabse simple approach, expected baseline — koi surprise nahi.

### 2. Node2Vec (Accuracy 57.14% — highest raw accuracy)
- **Partial success (misleading):** High accuracy sirf isliye hai
  kyunki dataset mein 4/7 cases genuinely "Unrelated" hain — agar
  model **hamesha "Unrelated" predict kare**, accuracy already
  57.14% ban jayegi bina kuch seekhe. Ye **"majority-class baseline"**
  hai, real detection capability nahi.
- **Fail:** Related cases 0/3.

### 3. Hybrid (Accuracy 42.86%)
- Rule + Node2Vec + Relationship + Risk ka fusion, phir bhi
  **standalone Node2Vec se kam accurate** — fusion weights in specific
  7 cases ke liye favorable nahi (production system in cases ke liye
  optimize nahi kiya gaya tha).
- **Fail:** Related cases 0/3.

### 4. GraphSAGE — single-chain (Accuracy 57.14%, post bug-fix)
- **Important honest observation:** Per-case detail dekhein — model
  **har single case ko "Unrelated" predict kar raha hai** (koi bhi
  case "Related" nahi aaya). Ye Node2Vec jaisa hi "majority-class
  collapse" hai — embedding collapse bug fix hone ke baad, model ab
  crash nahi karta (scores natural range mein hain: `-0.45` se `0.004`
  tak), lekin **abhi bhi kisi bhi pair ko positively "Related" flag
  karne laayak signal nahi seekh paya** — sirf 4 dev-jaisi examples
  (n=7 mein se) itna kam data hai ke model ek trivial "always-negative"
  solution mein settle ho gaya.
- **Fail:** Related cases 0/3. **Bug fixed, lekin underlying detection
  capability abhi bhi unproven hai** — chhota dataset iski wajah hai.

### 5. Cross-Chain GraphSAGE (Accuracy 28.57% — lowest)
- **Sabse interesting/qualitatively different result:** Ye akela
  method hai jo **kabhi "Related" predict karta hai** (Case 1 aur 2
  — dono `score > 0.77`) — matlab naye cross-chain edges
  (`same_address`, `bridge`, `known_exchange`) model ko **kuch naya
  signal** de rahe hain, single-chain version ke against.
- **Lekin galat jagah confident hai:** Case 1 aur 2 dono actually
  **"Unrelated"** hain, jinhe model ne galat "Related" bol diya
  (false positives) — jabke actual Related cases (3, 4, 5) abhi bhi
  miss ho gaye (false negatives).
- **Hypothesis (confirmed nahi, sirf ek observation):** Cases 1
  aur 2 mein Binance ka wallet (`0xd8dA6...`) shamil hai, jo
  **literally same address 2 chains pe reuse karta hai** — `same_address`
  edge is wallet ko strongly connect karta hai apne hi doosre-chain
  instance se. Ho sakta hai model ye "high connectivity via
  same_address" signal ko galat generalize kar raha ho ("is wallet
  ka koi cross-chain presence hai" ≈ "ye related hai"), na ke actual
  entity-relationship ko.
- **Fail:** Related cases 0/3, aur false positive rate bhi worst hai
  in 5 mein se.

---

## Sabse Important Takeaway (jo aapne khud highlight kiya tha)

> "We care particularly about whether the GNN can recover positive
> related-wallet detection without producing excessive false positives."

**Is criteria par:**
- Single-chain GraphSAGE: **0 false positives, lekin 0 true positives
  bhi** — ek "safe but useless" model (kabhi kuch flag hi nahi karta)
- Cross-Chain GraphSAGE: **2 false positives, 0 true positives** —
  behtar signal-seeking (kam se kam kuch predict kar raha hai) lekin
  abhi miscalibrated

**Dono mein se koi bhi production-ready nahi hai.** Cross-Chain
approach directionally zyada promising hai (naya, non-trivial signal
use kar raha hai), lekin n=7 itna chhota hai ke isay "improvement" ya
"regression" kehna abhi possible nahi — sirf itna keh sakte hain ke
**behavior qualitatively different hai**, jo further investigation
ka wajah hai.

### 6. XGBoost (n=4 training — pipeline demonstration only)
- **Genuine, informative failure:** Feature importances sab `0.0`,
  predictions sab probability `0.5` — model ne **literally kuch nahi
  seekha**. `n=4` training examples itne kam the ke koi bhi tree-split
  nahi bana (root-node hi reh gaya).
- Model effectively "hamesha Related predict karo" jaisa constant
  output de raha hai (GraphSAGE ke "hamesha Unrelated" collapse ka
  bilkul opposite) — held-out `1/3` accuracy sirf coincidence hai
  (ek hi genuine Related case tha, jo is trivial baseline se
  automatically "correct" nikal gaya).
- **Fail — lekin ye ek EXPECTED aur PREDICTED fail tha**, jo humne
  training se pehle hi flag kiya tha. Ye khud proof hai ke
  n=4/n=7 ka data volume kisi bhi supervised classical ML method
  (chahe kitna bhi accha ho) ko fairly evaluate karne ke liye kaafi
  nahi hai.

---

## Updated Research Progression — Final State

| Stage | Method | Related Recovered | Verdict |
|---|---|---|---|
| 1 | Rule | 0/3 | Fail — behavioral thresholds exchange wallets ke liye kaam nahi karte |
| 2 | Node2Vec | 0/3 | Fail — majority-class collapse |
| 3 | Hybrid | 0/3 | Fail — fusion in cases ke liye favorable nahi |
| 4 | XGBoost (n=4) | 1/3* | **Invalid** — model ne kuch nahi seekha (constant output) |
| 5 | GraphSAGE | 0/3 | Fail — majority-class collapse (opposite direction se XGBoost) |
| 6 | Cross-Chain GraphSAGE | 0/3 | Fail — lekin akela method jo kabhi "Related" predict karta hai (miscalibrated) |

*\*Statistically meaningless — coincidental result se ek trivial constant classifier ka.*

## Research Question — Honest Answer (per naya framing)

> "Determine whether graph-based representation learning improves
> cross-chain wallet attribution over rule-based behavioral similarity."

**Is n=7 dataset ke saath, ye question reliably answer NAHI ki ja
sakti.** Koi bhi method (chahe simple rule, chahe GNN) related cases
detect nahi kar pa raha — is wajah se "GraphSAGE ne improve kiya ya
nahi" ka koi statistically meaningful comparison possible nahi hai.
Jo cheez clear hai: **saare methods ka bottleneck data volume hai,
model complexity nahi** — na Rule, na Node2Vec, na XGBoost, na
GraphSAGE ke paas is chhote dataset se seekhne ke liye kaafi signal
hai.

**Genuine, defensible conclusion (agar report/thesis mein likhna ho):**
*"Is n=7 case-study ke sath, hum GNN-based approaches ke bare mein
koi statistically valid claim nahi kar sakte — na positive, na
negative. Cross-Chain GraphSAGE ka miscalibrated-lekin-non-trivial
behavior (Day 7) ek weak signal hai ke graph structure kuch dikha
raha hai, lekin isay confirm karne ke liye kaafi zyada labeled data
chahiye hoga (recommend: n=30+)."*