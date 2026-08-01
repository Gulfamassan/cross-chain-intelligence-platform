"""
Wallet API Routes

Handles wallet-related endpoints, such as validating an address
and checking its balance.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.wallet_service import wallet_service

router = APIRouter()


class WalletAddress(BaseModel):
    """
    Defines the expected request body for the POST endpoint.
    """
    address: str


@router.post("/validate-wallet")
def validate_wallet(wallet: WalletAddress):
    """
    Validates the given wallet address.

    Args:
        wallet (WalletAddress): The address provided in the request body

    Returns:
        dict: Validation result
    """
    return wallet_service.validate_wallet(wallet.address)


@router.get("/wallet-balance/{address}")
def get_wallet_balance(address: str):
    """
    Returns the balance of the given wallet address.

    Args:
        address (str): The wallet address provided in the URL

    Returns:
        dict: Address and its balance

    Raises:
        HTTPException: If the address is invalid (400)
    """
    try:
        return wallet_service.get_balance(address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))