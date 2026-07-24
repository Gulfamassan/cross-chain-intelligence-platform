"""
Neo4j Client

Ye module Neo4j database se connection setup karta hai.
Poore project mein isi client ko use karke queries chalayenge.
"""

from neo4j import GraphDatabase
from config.settings import settings


class Neo4jClient:
    """
    Ye class Neo4j database ke saath connection manage karti hai.
    """

    def __init__(self):
        """
        Neo4j driver banate hain jab class initialize hoti hai.
        """
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def verify_connection(self) -> bool:
        """
        Check karta hai ke Neo4j se connection successful hai ya nahi.

        Returns:
            bool: True agar connected hai
        """
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def run_query(self, query: str, parameters: dict = None):
        """
        Ek Cypher query chalata hai Neo4j par.

        Args:
            query (str): Cypher query
            parameters (dict): Query ke parameters (optional)

        Returns:
            list: Query ka result
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def close(self):
        """
        Connection band karta hai (jab app band ho).
        """
        self.driver.close()


# Ek single instance banate hain jo poore project mein import hoga
neo4j_client = Neo4jClient()