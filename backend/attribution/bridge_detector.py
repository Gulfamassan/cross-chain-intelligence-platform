"""
Bridge Detector

Ye module check karta hai ke koi transaction kisi known cross-chain
bridge (jaise Polygon Bridge, Arbitrum Bridge) se ho kar gayi hai ya nahi.
"""

import json
import os


class BridgeDetector:
    """
    Ye class bridges.json file padh kar transactions mein bridge
    activity detect karti hai.
    """

    CONFIG_PATH = os.path.join("config", "bridges.json")

    def __init__(self):
        """
        Bridges configuration load karte hain jab class banti hai.
        """
        self.bridges = self._load_bridges()

    def _load_bridges(self) -> dict:
        """
        bridges.json file se saare known bridge addresses padhta hai.

        Returns:
            dict: Bridge configuration
        """
        if not os.path.exists(self.CONFIG_PATH):
            return {}

        with open(self.CONFIG_PATH, "r") as f:
            return json.load(f)

    def is_bridge_address(self, chain: str, address: str) -> bool:
        """
        Check karta hai ke diya gaya address kisi known bridge ka hai ya nahi.

        Args:
            chain (str): Blockchain ka naam (jaise "ethereum")
            address (str): Check karne wala address

        Returns:
            bool: True agar ye ek known bridge address hai
        """
        if not address or not isinstance(address, str):
            return False
        chain = chain.lower()
        address = address.lower()

        if chain not in self.bridges:
            return False

        for bridge_name, addresses in self.bridges[chain].items():
            addresses_lower = [a.lower() for a in addresses]
            if address in addresses_lower:
                return True

        return False

    def identify_bridge(self, chain: str, address: str) -> str:
        """
        Diye gaye address ka bridge naam batata hai (agar ho).

        Args:
            chain (str): Blockchain ka naam
            address (str): Check karne wala address

        Returns:
            str: Bridge ka naam (jaise "polygon_pos_bridge"), ya None agar bridge na ho
        """
        chain = chain.lower()
        address = address.lower()

        if chain not in self.bridges:
            return None

        for bridge_name, addresses in self.bridges[chain].items():
            addresses_lower = [a.lower() for a in addresses]
            if address in addresses_lower:
                return bridge_name

        return None

    def detect_bridge_transactions(self, transactions: list, chain: str) -> list:
        """
        Diye gaye transactions mein se wo saari transactions dhoondta hai
        jo kisi bridge se involve hain (chahe sender ho ya receiver).

        Args:
            transactions (list): Transactions ki list (dictionaries)
            chain (str): Blockchain ka naam

        Returns:
            list: Sirf wo transactions jo bridge se involve hain,
                  har ek mein extra "bridge_name" field ke saath
        """
        bridge_transactions = []

        for tx in transactions:
            from_address = tx.get("from_address", "")
            to_address = tx.get("to_address", "")

            bridge_name = None
            if self.is_bridge_address(chain, to_address):
                bridge_name = self.identify_bridge(chain, to_address)
            elif self.is_bridge_address(chain, from_address):
                bridge_name = self.identify_bridge(chain, from_address)

            if bridge_name:
                tx_with_bridge = dict(tx)
                tx_with_bridge["bridge_name"] = bridge_name
                bridge_transactions.append(tx_with_bridge)

        return bridge_transactions


# Ek single instance banate hain jo poore project mein import hoga
bridge_detector = BridgeDetector()