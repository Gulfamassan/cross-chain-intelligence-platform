"""
Wallet Service

Ye module API aur blockchain service ke beech ka bridge hai.
Iska kaam hai:
- Wallet address ko validate karna
- Ethereum service ko call karke data lena
- Data ko API ke liye ready format mein dena

Isay "Service Layer" kehte hain, jo business logic ko
API routes se alag rakhta hai.
"""

from blockchain.ethereum_service import ethereum_service
from utils.validators import is_valid_ethereum_address


class WalletService:
    """
    Ye class wallet se related saara business logic handle karti hai.
    """

    def validate_wallet(self, address: str) -> dict:
        """
        Wallet address ko validate karta hai aur result deta hai.

        Args:
            address (str): Wallet address jo check karni hai

        Returns:
            dict: Validation result (valid hai ya nahi, aur konsi blockchain)
        """
        is_valid = is_valid_ethereum_address(address)

        return {
            "valid": is_valid,
            "blockchain": "Ethereum" if is_valid else None
        }

    def get_balance(self, address: str) -> dict:
        """
        Wallet ka balance nikalta hai, lekin pehle address validate karta hai.

        Args:
            address (str): Wallet address

        Returns:
            dict: Address aur uska balance

        Raises:
            ValueError: Agar address invalid ho
        """
        # Pehle address validate karo
        if not is_valid_ethereum_address(address):
            raise ValueError("Invalid Ethereum wallet address")

        # Ethereum service se balance mangwao
        balance = ethereum_service.get_wallet_balance(address)

        return {
            "address": address,
            "balance": f"{balance} ETH"
        }


# Ek single instance banate hain jo poore project mein import hoga
wallet_service = WalletService()