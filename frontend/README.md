# Cross-Chain Wallet Attribution & Joint Intelligence Layer

A blockchain intelligence research prototype that analyzes wallet behavior, builds transaction graphs, and uses a hybrid (rule-based + AI) engine to determine whether wallets across different blockchains may belong to the same entity.

---

## 📖 Project Overview

Most blockchain explorers show raw transaction data. This platform goes further — it collects on-chain data across multiple blockchains, builds a graph of wallet relationships, extracts behavioral features, generates AI-based graph embeddings (Node2Vec), and combines all of this into a **Hybrid Attribution Engine** that produces an explainable confidence score for whether two wallets (possibly on different chains) belong to the same real-world entity.

The system also includes a **Risk Intelligence Engine**, **Neo4j graph database integration**, a **React investigation dashboard**, and **PDF/CSV/JSON report export** — making it a complete, demoable investigation tool rather than just a set of APIs.

---

## ✨ Features

- **Multi-Chain Data Collection** — Ethereum, Polygon, and Arbitrum (via Etherscan's unified V2 API)
- **Feature Extraction** — per-wallet behavioral profiles (transaction frequency, volume, unique contacts, active days, etc.)
- **Graph Construction & Analytics** — NetworkX-based transaction graphs with centrality, clustering, and shortest-path analysis
- **Cross-Chain Attribution Engine** — bridge detection, behavioral similarity, heuristic scoring, and entity resolution
- **AI Layer** — Node2Vec graph embeddings with cosine-similarity comparison
- **Hybrid Attribution Engine** — configurable-weight fusion of rule-based, AI, relationship, and risk scores with human-readable explanations
- **Risk Intelligence Engine** — bridge usage, mixer interaction, high-frequency behavior, blacklist checks, rapid transfers, large transactions
- **Neo4j Integration** — graph import, wallet lookups, neighbor queries, shortest path, community detection
- **Joint Intelligence Layer** — combines every engine into a single investigation report with a timeline, evidence chain, and recommendation
- **Investigation Dashboard (React)** — multi-chain wallet analysis with charts (timeline, risk distribution, chain distribution) and an embedded interactive wallet network graph
- **Report Export** — professional PDF reports, plus CSV and JSON export
- **Performance Layer** — timing instrumentation, in-memory caching, Neo4j indexes

---

## 🛠️ Installation

### Prerequisites
- Python 3.11
- Node.js (for the frontend)
- A free [Neo4j AuraDB](https://neo4j.com/cloud/aura-free/) instance
- API keys: [Alchemy](https://www.alchemy.com/) and [Etherscan](https://etherscan.io/) (V2 API works across Ethereum, Polygon, and Arbitrum)

### Backend Setup
\`\`\`bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
\`\`\`

Create a `.env` file inside `backend/` with:
\`\`\`
ALCHEMY_API_KEY=your_key_here
ETHERSCAN_API_KEY=your_key_here
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password
\`\`\`

Run the backend:
\`\`\`bash
uvicorn main:app --reload
\`\`\`
API docs available at `http://127.0.0.1:8000/docs`

### Frontend Setup
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`
Dashboard available at `http://localhost:5173`

---

## 🔌 Key APIs

| Endpoint | Purpose |
|---|---|
| `GET /wallet/{chain}/{address}/transactions` | Fetch & normalize transactions for a chain |
| `POST /build-graph` | Build wallet transaction graph |
| `POST /extract-features` | Extract per-wallet behavioral features |
| `POST /ai/train` | Train Node2Vec embeddings |
| `POST /risk/analyze` | Run risk analysis on a wallet |
| `POST /hybrid/analyze` | Cross-chain wallet attribution (rule + AI + risk fusion) |
| `POST /intelligence/report` | Full joint intelligence report |
| `POST /report/generate` | Generate downloadable PDF report |
| `GET /export/pdf` \| `/csv` \| `/json` | Export investigation data |
| `POST /neo4j/import` | Import graph into Neo4j |
| `GET /performance/stats` | System performance metrics |

Full interactive documentation: `http://127.0.0.1:8000/docs`

---

## 📁 Folder Structure

\`\`\`
backend/
├── api/            # FastAPI route handlers
├── blockchain/      # Chain-specific collectors (Ethereum, Polygon, Arbitrum)
├── attribution/      # Bridge detection, similarity, heuristics, entity resolution
├── analytics/        # Centrality, clustering, relationship, shortest-path
├── ai/               # Node2Vec embeddings + similarity model
├── hybrid/            # Fusion engine, confidence classification, explanations
├── risk/              # Risk engine, indicators, blacklist, scoring
├── intelligence/       # Joint intelligence: aggregator, summary, timeline, recommendation
├── graph/              # Graph builder + visualization
├── database/            # Neo4j client, repository, loader
├── evaluation/           # Metrics, benchmarking, experiments, visualization
├── reports/               # PDF report generation
├── export/                 # CSV/JSON/PDF export wrappers
├── performance/             # Timing, caching, Neo4j indexes
├── features/                 # Feature extraction
├── normalization/              # Unified transaction schema
├── config/                      # Settings, supported chains, bridge addresses
├── utils/                        # Validators
├── datasets/                      # Auto-generated per-chain transaction CSVs
├── models/                         # Saved Node2Vec model & embeddings
└── main.py

frontend/
└── src/
    ├── InvestigationDashboard.jsx
    └── InvestigationDashboard.css
\`\`\`

---

## 📸 Screenshots

_(Add dashboard and PDF report screenshots here before presenting.)_

---

## 🏗️ Architecture

\`\`\`
Wallet Address
   ↓
Chain Manager → [Ethereum / Polygon / Arbitrum Collectors]
   ↓
Normalizer (Unified Transaction Schema)
   ↓
Dataset (CSV) ──────────────► Neo4j Graph Database
   ↓                                  ↑
Graph Builder (NetworkX) ─────────────┘
   ↓
Feature Extractor    Node2Vec AI Embeddings
   ↓                        ↓
        Hybrid Attribution Engine
                ↓
        Risk Engine ──► Joint Intelligence Layer
                ↓
     PDF / CSV / JSON Reports  +  React Dashboard
\`\`\`

---

## 💻 Technologies

- **Backend:** Python, FastAPI, Web3.py, Pandas, NetworkX, PyVis, scikit-learn, Node2Vec/Gensim, ReportLab
- **Database:** Neo4j (AuraDB)
- **Frontend:** React (Vite), Recharts
- **APIs:** Alchemy, Etherscan (unified V2 multi-chain API)
- **Version Control:** Git & GitHub

---

## 🔮 Future Work

- Activate BNB Chain support (requires Etherscan Pro plan or alternate API)
- Add Tron, Optimism, and Avalanche collectors
- Build a true cross-chain graph (currently graph analytics is per-chain only)
- Replace sample bridge/blacklist addresses with verified production data sources
- Graph Neural Network (GNN) models (GCN/GAT/GraphSAGE) as a further AI layer
- Multi-wallet batch investigation and case management in the GUI