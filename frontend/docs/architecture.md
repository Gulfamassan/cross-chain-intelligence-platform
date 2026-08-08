# System Architecture

## Overview

This platform follows a layered architecture where each layer has a single responsibility, making it easy to extend (e.g., adding a new blockchain) without breaking existing functionality.

## Data Flow

\`\`\`
1. Blockchain APIs (Alchemy / Etherscan V2)
        ↓
2. Chain Manager → routes to the correct chain-specific collector
        ↓
3. Blockchain Collectors (Ethereum / Polygon / Arbitrum)
        ↓
4. Normalization → converts raw data into the Unified Transaction Schema
        ↓
5. Dataset Layer (CSV storage, per-chain folders)
        ↓
6. Graph Builder (NetworkX) → wallets become nodes, transactions become edges
        ↓
7. Analytics Layer → centrality, clustering, relationship, shortest-path
        ↓
8. Feature Extractor → per-wallet behavioral profile
        ↓
9. AI Layer (Node2Vec) → graph embeddings + cosine similarity
        ↓
10. Attribution Engine → bridge detection, heuristics, entity resolution
        ↓
11. Risk Engine → indicators, blacklist checks, scoring
        ↓
12. Hybrid Attribution Engine → configurable-weight fusion of all scores
        ↓
13. Entity Resolution & Wallet Classification → classifies each wallet as
    Exchange / Bridge / Smart Contract / Personal / Unknown, using a
    known-address list first, then a rule-based heuristic classifier
        ↓
14. Explainable AI (XAI) Layer → converts raw scores (risk breakdown,
    attribution scores, classification reasoning) into human-readable
    evidence lists, so every decision has a stated "why"
        ↓
15. Joint Intelligence Layer → aggregates all of the above (transactions,
    graph stats, risk, entity classification, evidence) into one report
        ↓
16. Neo4j Knowledge Graph → persistent graph storage; wallets carry
    entity-type labels (e.g. `:Wallet:Personal`), linked to Chain nodes
    via `BELONGS_TO`, and to each other via `SENT`, `BRIDGED_TO`,
    and `INTERACTS`
        ↓
17. Report Generation (PDF/CSV/JSON) + React Dashboard
    (includes an Entity Intelligence panel with classification,
    confidence, evidence, and an on-demand explanation view)
\`\`\`

## Key Design Decisions

### Layered / Modular Design
Every module (blockchain, analytics, ai, risk, hybrid, intelligence, entity_labeling) is independent and communicates only through well-defined function calls. This means:
- A new blockchain only requires a new collector class + one line of registration in `chain_manager.py`.
- A bug in one module (e.g., Risk Engine) does not require touching unrelated modules.
- Entity Resolution and Explainability were added as additive layers (Sprint 12/13) on top of the existing pipeline without modifying the core attribution or risk scoring logic — they consume its output rather than duplicating it.

### Unified Transaction Schema
Regardless of which chain data comes from, it is normalized into:
\`\`\`
tx_hash, chain, from_address, to_address, value_eth,
gas_used, gas_price, timestamp, block_number, status
\`\`\`
This allows the Hybrid Engine, Graph Builder, and Feature Extractor to work identically across chains.

### Hybrid Attribution (Rule-Based + AI)
Two independent signals — a rule-based score (behavior similarity + bridge detection) and an AI score (Node2Vec embedding similarity) — are combined with a relationship score and a risk score using **configurable weights** (`config/weights.json`). This means priorities can be tuned without changing code.

### Explainability by Design (Not Bolted On)
Every scoring module (risk, attribution/relationship confidence, entity classification) returns a `reasons`/`evidence` list alongside its numeric output — not just a score. The `/entity/explain` endpoint and the dashboard's "View Explanation" panel simply surface this evidence; they do not compute new logic. This means explainability cannot silently drift out of sync with the underlying scoring, since it is read directly from the same function call.

### Entity Resolution: Known-List First, Heuristic Fallback
Wallet classification checks a curated known-address list first (e.g., known exchange/bridge addresses) before falling back to a rule-based heuristic classifier using transaction count, counterparty diversity, average value, and in/out ratio. Known-list matches return high confidence (~99%); heuristic matches return graded confidence (60–95%) with the specific triggering signals listed as evidence.

### Knowledge Graph: Labels, Not a Separate Node Type
Rather than replacing the `Wallet` node with separate `Exchange`/`Bridge`/`Contract` node types, entity classification is applied as an additional Neo4j label on the existing `Wallet` node (e.g. `(w:Wallet:Personal)`). This preserves all existing `SENT`/`BELONGS_TO` relationship queries while allowing new queries to filter by entity type.

## Known Limitations

### Single-Chain Graph
The current graph (NetworkX + Neo4j) is built per analysis run from a single chain's CSV. When comparing wallets across two different chains, the relationship/graph-based score currently returns 0 with an explicit `relationship_note` explaining this — it is a documented limitation, not a silent failure. A true cross-chain graph (linking chains via bridge transactions) is listed under Future Work.

### Bridge & Smart-Contract Usage Detection Is a Placeholder
`WalletProfile.bridge_usage` and `WalletProfile.smart_contract_usage` are currently hardcoded to `False` in the feature extraction layer — real on-chain detection has not been implemented yet. This means the Entity Resolution classifier's bridge-based classification rule cannot currently trigger from these fields; bridge relationships in the Knowledge Graph are instead detected separately via `attribution/bridge_detector.py`, which does have real detection logic. Completing `WalletProfile`'s placeholder fields is listed under Future Work.

### Token-Level Data Not Yet Modeled
The Knowledge Graph does not currently include `Token` nodes (e.g., specific ERC-20 tokens transacted), since no token-level data source exists in the current pipeline. Adding this without a real data source would mean fabricating graph data, so it has been deliberately deferred rather than stubbed out.