"""
Ethereum Blockchain Service

Ye module Ethereum blockchain se seedha connection banata hai
Web3.py library ke zariye. Iska kaam hai:
- Ethereum network se connect hona
- Wallet balance nikalna
- Network information dena
- Latest block number dena

Future mein isi tarah bnb_service.py, polygon_service.py, etc.
banaye jayenge.
"""

from web3 import Web3
from config.settings import settings


class EthereumService:
    """
    Ye class Ethereum blockchain ke saath saari interactions handle karti hai.
    """

    def __init__(self):
        """
        Jab is class ka object banega, ye Alchemy URL use karke
        Ethereum network se connection setup karega.
        """
        self.web3 = Web3(Web3.HTTPProvider(settings.ALCHEMY_URL))

    def is_connected(self) -> bool:
        """
        Check karta hai ke Ethereum network se connection successful hai ya nahi.

        Returns:
            bool: True agar connected hai, False agar nahi
        """
        return self.web3.is_connected()

    def get_latest_block_number(self) -> int:
        """
        Ethereum ka sabse latest (naya) block number nikalta hai.

        Returns:
            int: Latest block number
        """
        return self.web3.eth.block_number

    def get_network_info(self) -> dict:
        """
        Network ke baare mein basic information deta hai.

        Returns:
            dict: Network ka naam, latest block, aur connection status
        """
        return {
            "network": "Ethereum Mainnet",
            "latest_block": self.get_latest_block_number(),
            "connected": self.is_connected()
        }

    def get_wallet_balance(self, address: str) -> float:
        """
        Diye gaye wallet address ka ETH balance nikalta hai.

        Args:
            address (str): Ethereum wallet address

        Returns:
            float: Balance in ETH (Ether)
        """
        # Balance "Wei" mein aata hai (sabse chhoti unit), isay ETH mein convert karna hoga
        balance_wei = self.web3.eth.get_balance(address)
        balance_eth = self.web3.from_wei(balance_wei, "ether")
        return float(balance_eth)


# Ek single instance banate hain jo poore project mein import hoga
ethereum_service = EthereumService()