"""
backend/intelligence/search_engine.py

"Google Search for blockchain intelligence" — searches known entity
names (e.g. "Binance") and returns matching wallets/bridges/contracts,
enriched with live Neo4j graph data (chain, entity-type labels).

Reuses:
  - label_database.search_known_entities() for name matching
  - graph_repository.get_wallet_details_with_labels() for enrichment
No duplicate logic.
"""

from entity_labeling.label_database import search_known_entities
from database.graph_repository import graph_repository


def intelligence_search(query: str) -> dict:
    """
    Args:
        query (str): Free-text search term, e.g. "Binance"

    Returns:
        dict: Results grouped by entity type
              {"wallets": [], "bridges": [], "contracts": [], "exchanges": []}
    """
    matches = search_known_entities(query)

    grouped = {
        "wallets": [],
        "bridges": [],
        "contracts": [],
        "exchanges": [],
    }

    for match in matches:
        enriched = graph_repository.get_wallet_details_with_labels(match["address"])

        result_entry = {
            "address": match["address"],
            "name": match["name"],
            "chain": enriched.get("chain", "unknown"),
            "neo4j_labels": enriched.get("labels", []),
        }

        if match["label"] == "Exchange Wallet":
            grouped["exchanges"].append(result_entry)
        elif match["label"] == "Bridge Wallet":
            grouped["bridges"].append(result_entry)
        elif match["label"] == "Smart Contract":
            grouped["contracts"].append(result_entry)

        # Every match is also a wallet (address exists on-chain)
        grouped["wallets"].append(result_entry)

    grouped["total_results"] = len(matches)

    return grouped