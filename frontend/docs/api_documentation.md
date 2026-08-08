# API Documentation

Full interactive documentation (Swagger UI) is available at:
\`\`\`
http://127.0.0.1:8000/docs
\`\`\`

This document summarizes the main endpoint groups. All request/response schemas can be explored and tested live in Swagger.

## Blockchain Data
- `GET /network` — Ethereum network status
- `POST /validate-wallet` — validate a wallet address
- `GET /wallet-balance/{address}` — live wallet balance
- `GET /wallet/{chain}/{address}/transactions` — fetch, normalize, and save transactions for a given chain (`ethereum`, `polygon`, `arbitrum`)

## Features
- `POST /extract-features` — extract behavioral features for a wallet from its transaction CSV

## Graph
- `POST /build-graph` — build a NetworkX graph from a CSV
- `GET /graph/statistics` — nodes, edges, density, components, most connected wallet
- `POST /graph/visualize` — generate an interactive HTML wallet network graph

## Relationships & Attribution
- `GET /wallet/{address}/relationships` — direct/indirect connections, cluster, centrality
- `POST /attribution/analyze` — bridge + similarity based attribution between two wallets

## AI
- `POST /ai/train` — train Node2Vec embeddings on the current graph
- `POST /ai/similarity` — cosine similarity between two wallet embeddings

## Hybrid Attribution
- `POST /hybrid/analyze` — combines rule-based, AI, relationship, and risk scores into a single confidence score with an explanation and evidence chain. Supports cross-chain pairs via `wallet_1_chain` / `wallet_2_chain`.

## Risk
- `POST /risk/analyze` — full risk breakdown (bridge usage, mixer interaction, high frequency, blacklist hits, rapid transfers, large transactions)

## Entity Resolution, Classification & Explainability
- `POST /entity/resolve` — classifies a wallet's entity type (Exchange / Bridge / Smart Contract / Personal / Unknown), given an explicit `csv_path`. Checks a known-address list first, then falls back to a rule-based heuristic classifier. Returns `label`, `confidence`, `confidence_percent`, `source` (`known_list` or `heuristic`), and `evidence`.
- `POST /entity/classify` — simplified version of `/entity/resolve`; auto-resolves the transaction dataset from `wallet_address` + `chain` by convention (`datasets/{chain}/{wallet_address}.csv`), no `csv_path` required. Returns `classification` and `confidence` only.
- `POST /entity/explain` — combined explainable AI report for a wallet. Runs both entity classification and explainable risk scoring, merges their evidence into one list, and returns a human-readable `explanation` sentence alongside the raw `features` used — so the dashboard can show "Why?" instead of a bare score.

## Joint Intelligence
- `POST /intelligence/report` — complete investigation report: wallet summary (including entity classification, confidence, and evidence — Sprint 12/13), AI/risk info, text summary, timeline, and recommendation (now also references entity type). This is the primary investigator-facing endpoint; most individual analysis endpoints above exist for standalone/dedicated use, but a full investigation should generally go through this one.

## Neo4j
- `POST /neo4j/import` — import the current graph into Neo4j
- `GET /neo4j/wallet/{address}` — wallet connections from Neo4j, **plus its Knowledge Graph entity classification** (`entity_type`, `neo4j_labels`) and `chain` (extended in Sprint 13)
- `GET /neo4j/neighbors/{address}` — direct neighbors
- `GET /neo4j/path?wallet_1=...&wallet_2=...` — shortest path between two wallets
- `GET /neo4j/community` — cluster/community detection

## Evaluation & Performance
- `GET /evaluation/metrics` — graph/embedding stats
- `POST /evaluation/benchmark` — compares Rule vs Node2Vec vs Hybrid scores for a pair
- `GET /evaluation/report` — metrics + charts
- `GET /performance/stats` — average operation times, cache stats
- `POST /performance/setup-indexes` — create Neo4j performance indexes

## Reports & Export
- `POST /report/generate` — generate a downloadable PDF investigation report
- `GET /export/pdf` \| `GET /export/csv` \| `GET /export/json` — export investigation data in the requested format

## Standard Error Responses
- `400` — invalid input (e.g., malformed wallet address, unsupported chain, graph not built yet)
- `404` — resource not found (e.g., CSV file missing, or no dataset found for a wallet/chain in `/entity/classify` and `/entity/explain`)
- `500` — unexpected server error (should not occur under normal use; report if seen)