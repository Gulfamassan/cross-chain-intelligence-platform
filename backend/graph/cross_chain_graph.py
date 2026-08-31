"""
Cross-Chain Unified Graph Builder (Sprint 17, Day 6)

Ye module alag-alag chains (Ethereum, Polygon, Arbitrum) ke transaction
graphs ko ek SINGLE unified graph mein combine karta hai — jahan har
node ki identity sirf "wallet_address" nahi, balki
"(wallet_address, chain)" hai.

Kyun zaroori hai: purane `graph/builder.py` mein node sirf address hai
(chain node ka attribute nahi) — isliye agar same address 2 chains pe
mile, wo automatically EK hi node ban jata hai (chain info na hone ki
wajah se). Ye kabhi sahi hota hai (jaise exchange same address dono
chains pe reuse karta hai), lekin generally implicit/accidental hai,
explicit design decision nahi.

Cross-chain edges 3 tarah ke evidence se bante hain (koi naya scoring
rule invent nahi kiya — sab EXISTING, already-tested modules reuse
kiye hain):

    1. same_address    -> same wallet address 2+ chains pe milti hai
    2. bridge           -> attribution/bridge_detector.py se bridge
                            transaction detect hoti hai
    3. transfer_linkage -> attribution/cross_chain_evidence.py se
                            bridge-timing/amount correlation milta hai
    4. known_exchange   -> entity_labeling/label_database.py se dono
                            wallets ek hi named exchange ke known hain
"""

import pandas as pd
import networkx as nx

from attribution.bridge_detector import bridge_detector
from attribution.cross_chain_evidence import calculate_cross_chain_evidence
from entity_labeling.label_database import lookup_known_address


def _node_id(address: str, chain: str) -> str:
    """
    Composite node identity banata hai: "chain:address".
    Isse same address alag chains pe alag nodes banti hain
    (jab tak explicitly same_address edge se link na ho).

    IMPORTANT (Sprint 19 Day 1 clarification): Same address 2 chains
    pe hona automatically same real-world entity hone ka proof NAHI
    hai — isliye hum address ko blindly merge NAHI karte. Har
    (address, chain) apna alag node hai; agar same address multiple
    chains pe mile, unhe sirf ek `same_address` EVIDENCE edge se
    connect karte hain (dekhein `_add_same_address_edges()`) — merge
    nahi karte. Model khud seekh sakta hai ke ye evidence kitni
    strong hai, hum khud decide nahi karte.
    """
    return f"{chain.lower()}:{address.lower()}"


def build_unified_graph(wallet_chain_csvs: list) -> nx.MultiDiGraph:
    """
    Ek unified, multi-chain graph banata hai.

    Args:
        wallet_chain_csvs (list): [(csv_path, chain), ...] — har CSV
            file aur uska chain naam. Ek CSV mein multiple wallets ke
            transactions ho sakte hain (jaise Day 5 ka combined dataset).

    Returns:
        nx.MultiDiGraph: Nodes = (wallet_address, chain), attrs =
            {wallet_address, chain}. Edges ka `edge_category` attribute
            batata hai wo kis tarah ka link hai ("transaction",
            "same_address", "bridge", "transfer_linkage", "known_exchange").

    Note: MultiDiGraph use kiya hai (DiGraph nahi) — taake agar do
    wallets ke beech multiple transactions hon, sab survive karein
    (Day 1 audit mein identify ki gayi "data loss" problem yahan
    fix hai, is naye unified graph ke liye).
    """
    graph = nx.MultiDiGraph()

    # Step 1: Har chain ka data load karke same-chain transaction edges add karo
    for csv_path, chain in wallet_chain_csvs:
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            # Khaali/corrupt CSV — skip karte hain, poora process crash
            # nahi hona chahiye ek badi file ki wajah se
            print(f"  [skipped] Empty/unreadable CSV: {csv_path}")
            continue

        if df.empty:
            continue

        for _, row in df.iterrows():
            sender = row.get("from_address")
            receiver = row.get("to_address")

            if pd.isna(sender) or pd.isna(receiver):
                continue

            sender_id = _node_id(sender, chain)
            receiver_id = _node_id(receiver, chain)

            graph.add_node(sender_id, wallet_address=str(sender).lower(), chain=chain.lower())
            graph.add_node(receiver_id, wallet_address=str(receiver).lower(), chain=chain.lower())

            graph.add_edge(
                sender_id,
                receiver_id,
                edge_category="transaction",
                tx_hash=row.get("tx_hash"),
                value_eth=row.get("value_eth"),
                timestamp=row.get("timestamp"),
                chain=chain,
            )

    # Step 2: same_address edges — jahan ek hi address multiple chains pe mili
    _add_same_address_edges(graph)

    # Step 3: bridge edges — bridge_detector se
    _add_bridge_edges(graph, wallet_chain_csvs)

    # Step 4: known_exchange edges — label_database se
    _add_known_exchange_edges(graph)

    return graph


def _add_same_address_edges(graph: nx.MultiDiGraph):
    """
    Agar ek wallet_address 2+ alag chains pe node ban chuki hai,
    unke beech "same_address" edge add karta hai (identity linkage —
    strong evidence, kyunki ye literally wahi address hai).
    """
    address_to_nodes = {}
    for node_id, attrs in graph.nodes(data=True):
        address = attrs["wallet_address"]
        address_to_nodes.setdefault(address, []).append(node_id)

    for address, node_ids in address_to_nodes.items():
        if len(node_ids) < 2:
            continue
        # Har pair ke beech bidirectional identity edge
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                graph.add_edge(node_ids[i], node_ids[j], edge_category="same_address")
                graph.add_edge(node_ids[j], node_ids[i], edge_category="same_address")


def _add_bridge_edges(graph: nx.MultiDiGraph, wallet_chain_csvs: list):
    """
    Har chain ke transactions mein bridge activity dhoondta hai
    (attribution/bridge_detector.py use karke) aur bridge-wallet ke
    node par ek explicit "bridge" edge-category flag lagata hai
    (edge attribute ke taur par, node pe bhi ek marker attribute).
    """
    for csv_path, chain in wallet_chain_csvs:
        try:
            df = pd.read_csv(csv_path)
        except pd.errors.EmptyDataError:
            continue

        if df.empty:
            continue

        transactions = df.to_dict("records")

        bridge_txs = bridge_detector.detect_bridge_transactions(transactions, chain)

        for tx in bridge_txs:
            sender = tx.get("from_address")
            receiver = tx.get("to_address")
            if pd.isna(sender) or pd.isna(receiver):
                continue

            sender_id = _node_id(sender, chain)
            receiver_id = _node_id(receiver, chain)

            if graph.has_node(sender_id):
                graph.nodes[sender_id]["used_bridge"] = tx.get("bridge_name")
            if graph.has_node(receiver_id):
                graph.nodes[receiver_id]["used_bridge"] = tx.get("bridge_name")

            graph.add_edge(
                sender_id, receiver_id,
                edge_category="bridge",
                bridge_name=tx.get("bridge_name"),
            )


def _add_known_exchange_edges(graph: nx.MultiDiGraph):
    """
    Agar 2 nodes (chahe alag chains pe hon) dono ek hi NAMED exchange
    ke taur par known hain (entity_labeling/label_database.py se),
    unke beech "known_exchange" edge add karta hai.
    """
    name_to_nodes = {}

    for node_id, attrs in graph.nodes(data=True):
        match = lookup_known_address(attrs["wallet_address"])
        if match and match["label"] == "Exchange Wallet":
            name_to_nodes.setdefault(match["name"], []).append(node_id)

    for name, node_ids in name_to_nodes.items():
        if len(node_ids) < 2:
            continue
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                graph.add_edge(node_ids[i], node_ids[j], edge_category="known_exchange", entity_name=name)
                graph.add_edge(node_ids[j], node_ids[i], edge_category="known_exchange", entity_name=name)


def add_transfer_linkage_edges(graph: nx.MultiDiGraph, wallet_chain_pairs: list, csv_resolver):
    """
    Diye gaye wallet pairs ke beech bridge-timing/amount evidence
    (attribution/cross_chain_evidence.py) check karta hai — agar
    evidence mile, "transfer_linkage" edge add karta hai.

    Ye alag function hai (auto-run nahi hota `build_unified_graph()`
    mein), kyunki ye har-pair-check O(n^2) operation hai — bade
    wallet sets ke liye explicitly call karna chahiye, sirf un
    pairs ke liye jo interest mein hain (jaise ek investigation ke
    candidate wallets).

    Args:
        graph: build_unified_graph() se bana graph
        wallet_chain_pairs (list): [(wallet_1, chain_1, wallet_2, chain_2), ...]
        csv_resolver: function(wallet, chain) -> csv_path
    """
    for wallet_1, chain_1, wallet_2, chain_2 in wallet_chain_pairs:
        if chain_1.lower() == chain_2.lower():
            continue  # Same-chain pairs ke liye ye signal relevant nahi

        csv_1 = csv_resolver(wallet_1, chain_1)
        csv_2 = csv_resolver(wallet_2, chain_2)

        evidence = calculate_cross_chain_evidence(csv_1, wallet_1, chain_1, csv_2, wallet_2, chain_2)

        if evidence["matched_pairs"] > 0:
            node_1 = _node_id(wallet_1, chain_1)
            node_2 = _node_id(wallet_2, chain_2)

            if graph.has_node(node_1) and graph.has_node(node_2):
                graph.add_edge(
                    node_1, node_2,
                    edge_category="transfer_linkage",
                    score=evidence["score"],
                    evidence=evidence["evidence"],
                )


if __name__ == "__main__":
    """
    Sprint 19, Day 1 sanity check — saare 3 chains (Ethereum, Polygon,
    Arbitrum) ke available CSVs ko ek unified graph mein combine karta hai.

    Run: python -m graph.cross_chain_graph
    """
    import os
    from collections import Counter

    wallet_chain_csvs = []
    chains_found = set()

    for chain in ["ethereum", "polygon", "arbitrum"]:
        chain_folder = os.path.join("datasets", chain)
        if not os.path.isdir(chain_folder):
            continue
        for filename in os.listdir(chain_folder):
            if filename.endswith(".csv"):
                wallet_chain_csvs.append((os.path.join(chain_folder, filename), chain))
                chains_found.add(chain.capitalize())

    graph = build_unified_graph(wallet_chain_csvs)

    print("Unified graph created successfully\n")
    print("Chains:")
    for chain in sorted(chains_found):
        print(f"  {chain}")
    print()
    print("Total nodes:", graph.number_of_nodes())
    print("Total edges:", graph.number_of_edges())
    print()

    edge_categories = Counter(d.get("edge_category") for _, _, d in graph.edges(data=True))
    print("Edge categories:")
    for category, count in edge_categories.items():
        print(f"  {category}: {count}")