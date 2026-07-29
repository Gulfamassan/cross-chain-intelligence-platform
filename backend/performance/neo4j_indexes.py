"""
Neo4j Indexes

Ye module Neo4j database par indexes create karta hai — indexes
queries ko bahut fast bana dete hain, especially jab data bara ho jaye.

Bina index ke, Neo4j ko wallet dhoondne ke liye SAARE nodes check
karne padte hain. Index ke saath, ye seedha sahi node tak pahunch
jata hai.
"""

from database.neo4j_client import neo4j_client


class Neo4jIndexManager:
    """
    Ye class Neo4j database ke performance indexes manage karti hai.
    """

    def create_wallet_address_index(self):
        """
        Wallet address par ek index banata hai — taake wallet
        dhoondna (MATCH queries) bahut fast ho jaye.
        """
        query = """
        CREATE INDEX wallet_address_index IF NOT EXISTS
        FOR (w:Wallet) ON (w.address)
        """
        neo4j_client.run_query(query)

    def create_all_indexes(self) -> dict:
        """
        Saare zaroori indexes ek saath create karta hai.

        Returns:
            dict: Confirmation message
        """
        self.create_wallet_address_index()

        return {
            "message": "Indexes created successfully",
            "indexes": ["wallet_address_index"],
        }

    def list_indexes(self) -> list:
        """
        Neo4j mein currently maujood saare indexes ki list deta hai.

        Returns:
            list: Indexes ki details
        """
        query = "SHOW INDEXES"
        return neo4j_client.run_query(query)


# Ek single instance banate hain jo poore project mein import hoga
neo4j_index_manager = Neo4jIndexManager()