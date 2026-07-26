"""
Polygon Collector

Ye file BaseCollector ke template ko follow karke
Polygon blockchain ke liye saare functions implement karti hai.

Note: Etherscan ka unified V2 API Polygon ko bhi support karta hai
(same API key, sirf chainid alag hai), isliye humein alag Polygon
API key ki zaroorat nahi padi.
"""

import requests
from web3 import Web3
from blockchain.collectors.base_collector import BaseCollector
from config.settings import settings


class PolygonCollector(BaseCollector):
    """
    Polygon blockchain ke liye collector.
    Etherscan V2 unified API use karta hai (chainid: 137).
    """

    ETHERSCAN_URL = "https://api.etherscan.io/v2/api"
    CHAIN_ID = 137  # Polygon Mainnet

    # Polygon RPC endpoint (public, free) - balance check karne ke liye
    POLYGON_RPC_URL = "https://polygon-rpc.com"

    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(self.POLYGON_RPC_URL))

    def connect(self) -> bool:
        return self.web3.is_connected()

    def get_balance(self, address: str) -> float:
        balance_wei = self.web3.eth.get_balance(address)
        balance_matic = self.web3.from_wei(balance_wei, "ether")
        return float(balance_matic)

    def get_transactions(self, address: str, limit: int = 25) -> list:
        params = {
            "chainid": self.CHAIN_ID,
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": settings.ETHERSCAN_API_KEY,
        }
        return self._call_etherscan(params)

    def get_token_transfers(self, address: str, limit: int = 25) -> list:
        params = {
            "chainid": self.CHAIN_ID,
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": settings.ETHERSCAN_API_KEY,
        }
        return self._call_etherscan(params)

    def get_internal_transactions(self, address: str, limit: int = 25) -> list:
        params = {
            "chainid": self.CHAIN_ID,
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": settings.ETHERSCAN_API_KEY,
        }
        return self._call_etherscan(params)

    def network_name(self) -> str:
        return "Polygon"

    def _call_etherscan(self, params: dict) -> list:
        """
        Etherscan V2 API ko call karne ka common (shared) function.
        """
        response = requests.get(self.ETHERSCAN_URL, params=params)
        data = response.json()

        if data.get("status") != "1":
            if data.get("message") == "No transactions found":
                return []
            raise ValueError(f"Etherscan API error: {data.get('message')}")

        return data.get("result", [])