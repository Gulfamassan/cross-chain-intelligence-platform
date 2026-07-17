"""
Transaction Service

Ye module Etherscan API se kisi bhi Ethereum wallet ki
transaction history fetch karta hai.

Iska sirf ek kaam hai:
Wallet Address -> Etherscan API Call -> Transactions Return
"""

import requests
from config.settings import settings


class TransactionService:
    """
    Ye class Etherscan API ke saath saari interactions handle karti hai.
    """

    BASE_URL = "https://api.etherscan.io/v2/api"

    def get_transactions(self, address: str, limit: int = 25) -> list:
        """
        Diye gaye wallet address ki transactions Etherscan se fetch karta hai.

        Args:
            address (str): Ethereum wallet address
            limit (int): Kitni transactions chahiye (default 25)

        Returns:
            list: Transactions ki list, har transaction ek dictionary hai

        Raises:
            ValueError: Agar Etherscan se koi error aaye
        """
        # Etherscan API ko bhejne wale parameters
        params = {
            "chainid": 1,
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

        # API ko request bhejo
        response = requests.get(self.BASE_URL, params=params)
        data = response.json()

        # Etherscan "status": "1" deta hai success pe, "0" deta hai error pe
        if data.get("status") != "1":
            # Agar wallet mein koi transaction hi nahi hai, Etherscan "No transactions found" bhejta hai
            if data.get("message") == "No transactions found":
                return []
            raise ValueError(f"Etherscan API error: {data.get('message')}")

        return data.get("result", [])


# Ek single instance banate hain jo poore project mein import hoga
transaction_service = TransactionService()