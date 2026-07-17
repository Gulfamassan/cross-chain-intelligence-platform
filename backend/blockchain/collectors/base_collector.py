"""
Base Collector

Ye file har blockchain collector ka "template" (blueprint) hai.
Har collector (Ethereum, Polygon, BNB, etc.) ko yehi functions
implement karne honge, taake poore system mein consistency rahe.

Isay "Abstract Base Class" kehte hain.
"""

from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """
    Ye ek abstract class hai. Isay directly use nahi kiya ja sakta,
    balki har blockchain-specific collector isay "inherit" karega
    aur in saare functions ko apne hisaab se implement karega.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Blockchain se connection setup karta hai.

        Returns:
            bool: True agar connection successful hai
        """
        pass

    @abstractmethod
    def get_balance(self, address: str) -> float:
        """
        Wallet ka balance nikalta hai.

        Args:
            address (str): Wallet address

        Returns:
            float: Balance (native currency mein, jaise ETH, MATIC, etc.)
        """
        pass

    @abstractmethod
    def get_transactions(self, address: str, limit: int = 25) -> list:
        """
        Wallet ki transactions nikalta hai.

        Args:
            address (str): Wallet address
            limit (int): Kitni transactions chahiye

        Returns:
            list: Transactions ki list
        """
        pass

    @abstractmethod
    def get_token_transfers(self, address: str, limit: int = 25) -> list:
        """
        Wallet ke token transfers (jaise USDT, USDC) nikalta hai.

        Args:
            address (str): Wallet address
            limit (int): Kitne transfers chahiye

        Returns:
            list: Token transfers ki list
        """
        pass

    @abstractmethod
    def get_internal_transactions(self, address: str, limit: int = 25) -> list:
        """
        Wallet ki internal transactions nikalta hai
        (smart contracts ke andar wale transfers).

        Args:
            address (str): Wallet address
            limit (int): Kitni transactions chahiye

        Returns:
            list: Internal transactions ki list
        """
        pass

    @abstractmethod
    def network_name(self) -> str:
        """
        Is collector ki blockchain ka naam deta hai.

        Returns:
            str: Network ka naam, jaise "Ethereum"
        """
        pass