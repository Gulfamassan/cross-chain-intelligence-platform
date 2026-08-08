# User Manual — Investigation Dashboard

## Getting Started

1. Start the backend: `uvicorn main:app --reload` (inside `backend/`)
2. Start the frontend: `npm run dev` (inside `frontend/`)
3. Open the dashboard: `http://localhost:5173`

## Running an Investigation

1. **Enter a wallet address** you want to investigate (e.g., `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`).
2. **Enter the CSV path** for that wallet's transaction data. If you haven't fetched it yet, use the API first:
   \`\`\`
   GET /wallet/{chain}/{address}/transactions
   \`\`\`
   This automatically saves a CSV to `datasets/{chain}/{address}.csv` — use that exact path in the dashboard.
3. **Select the blockchain** from the dropdown (Ethereum, Polygon, or Arbitrum).
4. Click **Analyze**.

## Reading the Results

- **Stat Cards** — quick overview: wallet count, transaction count, community/cluster, risk score, AI availability, and chain.
- **Timeline Chart** — breakdown of Sent vs. Received events.
- **Risk Distribution** — visual split of risk vs. safety score.
- **Chain Distribution** — transaction volume for the analyzed chain.
- **Wallet Network** — an interactive, zoomable/draggable graph of the wallet's connections. Click and drag nodes to explore.
- **Entity Intelligence** — shows the wallet's classified entity type (Exchange / Bridge / Smart Contract / Personal / Unknown) with a confidence percentage and a bullet list of supporting evidence.
  - **View Graph** — scrolls to the Wallet Network graph above.
  - **View Explanation** — fetches a combined explainable AI breakdown (entity + risk reasoning merged into one summary sentence and evidence list), shown inline below the buttons.
- **Recommendation** — a priority label (e.g., "Investigate Further") with the specific reasons behind it, now including the entity classification as a contributing factor.
- **Summary** — a plain-language description of the wallet's activity, including its entity classification.
- **Timeline Details** — a scrollable list of individual transaction events with timestamps.

## Cross-Chain Attribution

To check whether two wallets (potentially on different chains) may belong to the same entity, use the API directly:
\`\`\`
POST /hybrid/analyze
{
  "wallet_1": "0x...",
  "wallet_2": "0x...",
  "wallet_1_csv": "datasets/ethereum/0x....csv",
  "wallet_2_csv": "datasets/polygon/0x....csv",
  "wallet_1_chain": "ethereum",
  "wallet_2_chain": "polygon"
}
\`\`\`
The response includes a `confidence` score (0–100), a `classification` (e.g., "Likely Same Entity", "Likely Different Entities"), and an `evidence` chain explaining the reasoning step by step.

## Checking a Wallet's Entity Type Directly

To classify a single wallet's entity type without running a full investigation, use:
\`\`\`
POST /entity/classify
{
  "wallet_address": "0x...",
  "chain": "ethereum"
}
\`\`\`
This automatically locates the wallet's dataset CSV by convention and returns a `classification` and `confidence`. For the full evidence list and source (`known_list` vs. `heuristic`), use `POST /entity/resolve` instead, which requires an explicit `csv_path`.

For a combined entity + risk explanation ("Why?"), use `POST /entity/explain` — this is what powers the dashboard's "View Explanation" button.

## Exporting a Report

To generate a downloadable PDF report for a wallet:
\`\`\`
POST /report/generate
{
  "wallet": "0x...",
  "csv_path": "datasets/ethereum/0x....csv",
  "chain": "ethereum"
}
\`\`\`
CSV and JSON exports are available via `GET /export/csv` and `GET /export/json` with the same parameters as query strings.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `400: No graph has been built yet` | You called an endpoint before `/build-graph` | Call `POST /build-graph` first with the correct CSV path |
| `404: CSV file not found` | Wrong or missing CSV path | Fetch transactions first via `/wallet/{chain}/{address}/transactions` |
| `400: Unsupported blockchain` | Chain not yet activated (e.g., BNB) | Use Ethereum, Polygon, or Arbitrum for now |
| `404: No transaction dataset found` (on `/entity/classify` or `/entity/explain`) | Dataset CSV doesn't exist at the expected path `datasets/{chain}/{wallet_address}.csv` | Fetch transactions first via `/wallet/{chain}/{address}/transactions`, or use `/entity/resolve` with an explicit `csv_path` |
| Entity Intelligence shows "Unknown" with low confidence | Wallet doesn't match the known-address list and doesn't clearly fit a heuristic rule (e.g., moderate activity that isn't clearly personal or exchange-like) | Expected behavior for ambiguous wallets — check the `evidence` list for the specific reason |
| Dashboard shows old data after a new analysis | Rare frontend state issue | Refresh the page and re-run the analysis |