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

    def clear_database(self):
        """
        Neo4j database se saare nodes aur relationships delete karta hai.
        (Testing/reset ke liye — dhyan se use karna!)
        """
        query = "MATCH (n) DETACH DELETE n"
        neo4j_client.run_query(query)


# Ek single instance banate hain jo poore project mein import hoga
graph_repository = GraphRepository()