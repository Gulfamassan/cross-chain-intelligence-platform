"""
Wallet API Routes

Ye module wallet-related endpoints handle karta hai,
jaise address validate karna aur balance nikalna.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.wallet_service import wallet_service

# Router banate hain jo main.py mein include hoga
router = APIRouter()


class WalletAddress(BaseModel):
    """
    Ye schema define karta hai ke POST request mein
    kaisa data aana chahiye.
    """
    address: str


@router.post("/validate-wallet")
def validate_wallet(wallet: WalletAddress):
    """
    Diye gaye wallet address ko validate karta hai.

    Args:
        wallet (WalletAddress): Request body mein aane wala address

    Returns:
        dict: Validation result
    """
    return wallet_service.validate_wallet(wallet.address)


@router.get("/wallet-balance/{address}")
def get_wallet_balance(address: str):
    """
    Diye gaye wallet address ka balance nikalta hai.

    Args:
        address (str): URL mein aane wala wallet address

    Returns:
        dict: Address aur uska balance

    Raises:
        HTTPException: Agar address invalid ho (400 error)
    """
    try:
        return wallet_service.get_balance(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))