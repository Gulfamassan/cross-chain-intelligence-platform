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
13. Joint Intelligence Layer → aggregates everything into one report
        ↓
14. Neo4j → persistent graph storage & queries
        ↓
15. Report Generation (PDF/CSV/JSON) + React Dashboard
\`\`\`

## Key Design Decisions

### Layered / Modular Design
Every module (blockchain, analytics, ai, risk, hybrid, intelligence) is independent and communicates only through well-defined function calls. This means:
- A new blockchain only requires a new collector class + one line of registration in `chain_manager.py`.
- A bug in one module (e.g., Risk Engine) does not require touching unrelated modules.

### Unified Transaction Schema
Regardless of which chain data comes from, it is normalized into:
\`\`\`
tx_hash, chain, from_address, to_address, value_eth,
gas_used, gas_price, timestamp, block_number, status
\`\`\`
This allows the Hybrid Engine, Graph Builder, and Feature Extractor to work identically across chains.

### Hybrid Attribution (Rule-Based + AI)
Two independent signals — a rule-based score (behavior similarity + bridge detection) and an AI score (Node2Vec embedding similarity) — are combined with a relationship score and a risk score using **configurable weights** (`config/weights.json`). This means priorities can be tuned without changing code.

### Known Limitation: Single-Chain Graph
The current graph (NetworkX + Neo4j) is built per analysis run from a single chain's CSV. When comparing wallets across two different chains, the relationship/graph-based score currently returns 0 with an explicit `relationship_note` explaining this — it is a documented limitation, not a silent failure. A true cross-chain graph (linking chains via bridge transactions) is listed under Future Work.