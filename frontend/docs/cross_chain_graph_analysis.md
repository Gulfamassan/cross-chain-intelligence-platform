# Cross-Chain Graph Analysis

**Sprint 14, Day 5 — Architecture Investigation Document**

This document is the output of an investigation into why cross-chain
wallet attribution underperforms (see Sprint 14 Day 3–4 experimental
results). It is a design/analysis document only — no production code
was modified during this investigation.

---

## Current Architecture
Ethereum Data (CSV) → Ethereum Graph (NetworkX DiGraph) → Node2Vec → Score
Polygon Data (CSV) → Polygon Graph (NetworkX DiGraph) → Node2Vec → Score
Arbitrum Data (CSV) → Arbitrum Graph (NetworkX DiGraph) → Node2Vec → Score

Each graph is built independently, from a single CSV file, via
`TransactionGraph.load_csv()` + `build_graph()`
(`backend/graph/builder.py`). The `/build-graph` API accepts exactly
one `csv_path` per call. There is no code path that merges two chains'
data into a single graph.

---

## Identified Limitations (from Task 1 & Task 2 inspection)

### 1. No unified cross-chain graph representation
`TransactionGraph` is instantiated fresh per analysis run and loads
exactly one chain's CSV. A wallet that only appears on Polygon cannot
be found in a graph built from Ethereum data, and vice versa. This was
confirmed empirically in Sprint 14 Day 3: `relationship_score` returned
`0.0` for every cross-chain pair tested, because one of the two wallets
was structurally absent from the graph — not because there was no
real relationship.

### 2. `chain` exists only as an edge attribute, not a node attribute
`build_graph()` attaches `chain=row.get("chain")` to each **edge**, but
no `chain` field is ever set on a **node**. Even if graphs from
multiple chains were merged, there would be no reliable way to query
"which chain does this wallet belong to" directly from the node itself
— a `Wallet → BELONGS_TO → Chain` relationship (as proposed below)
does not currently exist anywhere in the NetworkX graph.

### 3. Bridge transactions are detected, but never become graph edges
`bridge_detector.detect_bridge_transactions()` (`backend/attribution/
bridge_detector.py`) returns a flat list of transactions where one
side (`from_address` or `to_address`) matches a known bridge contract
address, with a `bridge_name` field attached. This function is never
called from `graph/builder.py`, so a detected bridge transaction never
creates a graph edge. Bridge detection and graph construction are two
completely disconnected code paths today.

### 4. Bridge detector cannot currently identify the destination side
This is the deepest gap, found during Task 2. `detect_bridge_transactions()`
can only confirm "this transaction touched a known bridge contract
address on chain X." It has no mechanism to determine:
- which wallet address receives the funds on the destination chain
  (`destination_wallet`)
- which chain that destination is (`destination_chain`)

`config/bridges.json` only stores bridge contract addresses **per
source chain** — it does not encode source→destination chain mappings
or any way to correlate an outgoing bridge transaction with its
corresponding incoming transaction on another chain. The only existing
attempt at this kind of correlation is the timing-based heuristic in
`attribution/heuristics.py` (`rule_bridge_timing()`, Sprint 12), which
compares timestamps between a manually-supplied bridge transaction and
a manually-supplied receive transaction — it does not automatically
discover the destination wallet on its own.

**Practical consequence:** even if a cross-chain graph builder is
implemented, it cannot draw a `Bridge → CONNECTS → Chain` edge to the
correct destination wallet without first solving destination inference
— most realistically via timestamp/amount-correlation heuristics
across chains, run at data-collection or graph-build time, not as an
afterthought.

---

## Proposed Architecture
Ethereum ─┐
Polygon ─┼──→ Unified Cross-Chain Graph
Arbitrum ─┘

### Proposed Graph Model

**Node types:**
- `Wallet`
- `Chain`
- `Bridge`
- `Contract`
- `Token` *(currently no token-level data source exists in the
  pipeline — see Sprint 13 Knowledge Graph work, where this was
  deliberately deferred for the same reason)*

**Relationship types:**
Wallet ──SENT──────────────> Wallet
Wallet ──INTERACTED_WITH───> Contract
Wallet ──USED───────────────> Bridge
Bridge ──CONNECTS──────────> Chain
Wallet ──BELONGS_TO─────────> Chain

Example instantiation:
Ethereum
       ↑
    BELONGS_TO
       │
   Wallet A
       │
      USED
       ↓
    Bridge
       │
    CONNECTS
       ↓
    Polygon
       ↑
    BELONGS_TO
       │
   Wallet B

This mirrors the entity-labeling approach already used in the Neo4j
Knowledge Graph (Sprint 12/13), where `Wallet` nodes carry additional
labels (e.g. `:Wallet:Personal`) rather than being replaced by a
separate node type — the same pattern should extend naturally to
`Chain` and `Bridge` as first-class nodes.

### Required Data (not all currently available)

| Data | Currently available? |
|---|---|
| Wallet address | ✅ Yes (from transaction CSVs) |
| Chain | ✅ Yes (per-transaction, in CSV) |
| Transaction (hash, amount, timestamp) | ✅ Yes |
| Bridge contract identification | ✅ Yes (`bridge_detector.py`) |
| **Bridge destination wallet/chain** | ❌ **No — this is the core gap (Task 2)** |
| Contract (non-bridge) identification | 🟡 Partial — `entity_labeling` classifies "Smart Contract" but bytecode detection is not wired (Sprint 12/13 known limitation) |
| Token | ❌ No — no token-level data source in the pipeline |

---

## Required Future Changes (Not Implemented in This Sprint)
1-Bridge destination inference
(timing/amount correlation across chains — extends
attribution/heuristics.py's existing rule_bridge_timing() concept
from a manual pairwise check into an automatic cross-chain scanner)
↓
2-Cross-chain graph builder
(merges multiple chains' TransactionGraph instances into one,
adds Chain and Bridge nodes, BELONGS_TO/CONNECTS/USED edges)
↓
3-Cross-chain Node2Vec
(retrain embeddings on the unified graph, so wallet vectors
capture cross-chain structural position, not just per-chain)
↓
4-Cross-chain relationship_score
(hybrid/scoring.py's calculate_relationship_score() would find
both wallets in the same graph, instead of returning 0.0)
↓
5-Hybrid attribution
(benefits automatically — no change needed to fusion.py itself,
since it already consumes relationship_score as an input)   

**Scope note:** Step 1 (bridge destination inference) is the
prerequisite for everything else — Steps 2–5 cannot produce
trustworthy results without it. This should be treated as the actual
starting point for any future cross-chain graph sprint, not graph
construction itself.

---

## Relationship to Sprint 14 Experimental Findings

This design directly explains the Day 3–4 results:
- Day 3 showed all three models (Rule, Node2Vec, Hybrid) failed to
  correctly classify the one genuine cross-chain "Related" pair
  (Case 3), because `relationship_score` was structurally `0`.
- Day 4's missing-aware fusion experiment showed that simply excluding
  the zero signal (rather than treating it as a real 0) produced only
  a marginal score change (+0.02 for Case 3) — confirming that the
  degradation is **not** primarily a fusion-weighting problem, but a
  **data representation** problem, consistent with the gaps identified
  in this document.

This is listed as Future Work in `README.md` and `architecture.md`
("Build a true cross-chain graph... linking chains via bridge
transactions") and is now backed by a concrete investigation rather
than a general statement.