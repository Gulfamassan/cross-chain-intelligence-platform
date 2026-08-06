"""
backend/database/knowledge_graph_builder.py

Orchestrates the upgrade from a plain wallet-transaction graph into
a richer Knowledge Graph: adds entity-type labels (Exchange/Bridge/
Contract), Chain nodes, and BRIDGED_TO / INTERACTS relationships —
on top of the existing Wallet/SENT graph (graph_loader.py, unchanged).

Token nodes are intentionally NOT included yet — no token-level data
source exists in the current pipeline. Adding it here would mean
fabricating data. Flagged as future work.
"""

from database.graph_repository import graph_repository
from entity_labeling.label_engine import resolve_entity
from attribution.bridge_detector import bridge_detector


def enrich_knowledge_graph(wallet_profiles: dict, transactions: list, chain: str):
    """
    Args:
        wallet_profiles: dict of {address: WalletProfile.to_dict()} for
                          every wallet already loaded into Neo4j via graph_loader
        transactions: raw transaction records (same list passed to bridge_detector)
        chain: blockchain name for this batch (e.g. "ethereum")
    """
    # Step 1: Chain node
    graph_repository.create_chain_node(chain)

    # Step 2: Classify each wallet and add entity-type labels + BELONGS_TO
    for address, profile_dict in wallet_profiles.items():
        label_result = resolve_entity(address, profile_dict, is_contract=profile_dict.get("is_contract", False))
        graph_repository.create_entity_label(address, label_result["label"].replace(" Wallet", ""))
        graph_repository.link_wallet_to_chain(address, chain)

    # Step 3: Bridge relationships (reuses existing bridge_detector — no duplicate logic)
    bridge_txs = bridge_detector.detect_bridge_transactions(transactions, chain)
    for tx in bridge_txs:
        from_addr = tx.get("from_address")
        to_addr = tx.get("to_address")
        if from_addr and to_addr:
            graph_repository.create_bridged_to_relationship(
                from_address=from_addr,
                to_address=to_addr,
                source_chain=chain,
                dest_chain=tx.get("dest_chain", "unknown"),
                tx_hash=tx.get("tx_hash"),
            )

    return {
        "chain": chain,
        "wallets_labeled": len(wallet_profiles),
        "bridge_relationships_created": len(bridge_txs),
    }