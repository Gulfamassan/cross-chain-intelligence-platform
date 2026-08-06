"""
Graph Repository

Ye module Neo4j mein wallet nodes aur transaction relationships
create, query, aur manage karta hai. Cypher queries yahan likhi jaati hain.
"""

from database.neo4j_client import neo4j_client


class GraphRepository:
    """
    Ye class Neo4j database ke saath saari graph-related operations handle karti hai.
    """

    def create_wallet_node(self, address: str, chain: str):
        """
        Ek wallet node banata hai (agar pehle se exist nahi karta).

        Args:
            address (str): Wallet address
            chain (str): Blockchain ka naam
        """
        query = """
        MERGE (w:Wallet {address: $address})
        SET w.chain = $chain
        """
        neo4j_client.run_query(query, {"address": address.lower(), "chain": chain})

    def create_transaction_relationship(self, from_address: str, to_address: str,
                                          tx_hash: str, value_eth: float, timestamp=None):
        """
        Do wallets ke beech ek transaction relationship banata hai.

        Args:
            from_address (str): Sender wallet
            to_address (str): Receiver wallet
            tx_hash (str): Transaction hash
            value_eth (float): Transaction ki value
            timestamp: Transaction ka time (optional)
        """
        query = """
        MATCH (a:Wallet {address: $from_address})
        MATCH (b:Wallet {address: $to_address})
        MERGE (a)-[t:SENT {tx_hash: $tx_hash}]->(b)
        SET t.value_eth = $value_eth, t.timestamp = $timestamp
        """
        neo4j_client.run_query(query, {
            "from_address": from_address.lower(),
            "to_address": to_address.lower(),
            "tx_hash": tx_hash,
            "value_eth": value_eth,
            "timestamp": timestamp,
        })

    def get_wallet_connections(self, address: str) -> list:
        """
        Diye gaye wallet ke saare direct connections nikalta hai Neo4j se.

        Args:
            address (str): Wallet address

        Returns:
            list: Connected wallets aur unki transaction details
        """
        query = """
        MATCH (w:Wallet {address: $address})-[t:SENT]-(other:Wallet)
        RETURN other.address AS wallet, t.tx_hash AS tx_hash, t.value_eth AS value_eth
        """
        return neo4j_client.run_query(query, {"address": address.lower()})

    def get_all_wallets(self) -> list:
        """
        Neo4j mein saare wallets return karta hai.

        Returns:
            list: Saare wallet addresses
        """
        query = "MATCH (w:Wallet) RETURN w.address AS address, w.chain AS chain"
        return neo4j_client.run_query(query)

    def get_graph_stats(self) -> dict:
        """
        Neo4j database ki basic statistics deta hai.

        Returns:
            dict: Total nodes aur relationships ka count
        """
        node_query = "MATCH (w:Wallet) RETURN count(w) AS count"
        rel_query = "MATCH ()-[t:SENT]->() RETURN count(t) AS count"

        node_result = neo4j_client.run_query(node_query)
        rel_result = neo4j_client.run_query(rel_query)

        return {
            "total_wallets": node_result[0]["count"] if node_result else 0,
            "total_relationships": rel_result[0]["count"] if rel_result else 0,
        }

    # ============================================================
    # Day 6 additions — Knowledge Graph enrichment
    # (entity-type labels, Chain nodes, BRIDGED_TO, INTERACTS)
    # ============================================================

    def create_entity_label(self, address: str, entity_type: str):
        """
        Existing Wallet node par ek extra label lagata hai (jaise :Exchange, :Bridge,
        :Contract) — Wallet node khud replace nahi hota, sirf classify hota hai.
        Neo4j multi-label supports karta hai: (w:Wallet:Exchange)

        Args:
            address (str): Wallet address
            entity_type (str): "Exchange", "Bridge", "Contract", ya "Personal"
        """
        safe_label = entity_type.replace(" ", "")
        query = f"""
        MATCH (w:Wallet {{address: $address}})
        SET w:{safe_label}
        """
        neo4j_client.run_query(query, {"address": address.lower()})

    def create_chain_node(self, chain: str):
        """
        Ek Chain node banata hai (agar exist nahi karta).

        Args:
            chain (str): Blockchain ka naam, jaise "ethereum", "polygon"
        """
        query = "MERGE (c:Chain {name: $chain})"
        neo4j_client.run_query(query, {"chain": chain.lower()})

    def link_wallet_to_chain(self, address: str, chain: str):
        """
        Wallet ko uski Chain se BELONGS_TO relationship se jodta hai.
        (Ye chain property ko replace nahi karta, sirf graph-native link add karta hai.)
        """
        query = """
        MATCH (w:Wallet {address: $address})
        MATCH (c:Chain {name: $chain})
        MERGE (w)-[:BELONGS_TO]->(c)
        """
        neo4j_client.run_query(query, {"address": address.lower(), "chain": chain.lower()})

    def create_bridged_to_relationship(self, from_address: str, to_address: str,
                                         source_chain: str, dest_chain: str, tx_hash: str = None):
        """
        Do wallets ke beech ek cross-chain bridge relationship banata hai.

        Args:
            from_address (str): Source chain wallet
            to_address (str): Destination chain wallet
            source_chain (str): Jahan se bridge hua
            dest_chain (str): Jahan bridge hua
            tx_hash (str): Bridge transaction hash (optional)
        """
        query = """
        MATCH (a:Wallet {address: $from_address})
        MATCH (b:Wallet {address: $to_address})
        MERGE (a)-[br:BRIDGED_TO {tx_hash: $tx_hash}]->(b)
        SET br.source_chain = $source_chain, br.dest_chain = $dest_chain
        """
        neo4j_client.run_query(query, {
            "from_address": from_address.lower(),
            "to_address": to_address.lower(),
            "source_chain": source_chain.lower(),
            "dest_chain": dest_chain.lower(),
            "tx_hash": tx_hash,
        })

    def create_interacts_relationship(self, wallet_address: str, contract_address: str, tx_hash: str = None):
        """
        Wallet ka ek smart contract ke saath interaction record karta hai
        (jaise DEX swap, staking, waghera — SENT se alag kyunke ye
        contract-call hai, simple transfer nahi).

        Args:
            wallet_address (str): Interact karne wali wallet
            contract_address (str): Smart contract ka address
            tx_hash (str): Transaction hash (optional)
        """
        query = """
        MATCH (w:Wallet {address: $wallet_address})
        MATCH (c:Wallet:Contract {address: $contract_address})
        MERGE (w)-[i:INTERACTS {tx_hash: $tx_hash}]->(c)
        """
        neo4j_client.run_query(query, {
            "wallet_address": wallet_address.lower(),
            "contract_address": contract_address.lower(),
            "tx_hash": tx_hash,
        })

    def clear_database(self):
        """
        Neo4j database se saare nodes aur relationships delete karta hai.
        (Testing/reset ke liye — dhyan se use karna!)
        """
        query = "MATCH (n) DETACH DELETE n"
        neo4j_client.run_query(query)


# Ek single instance banate hain jo poore project mein import hoga
graph_repository = GraphRepository()