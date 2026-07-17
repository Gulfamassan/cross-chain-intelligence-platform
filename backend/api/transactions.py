"""
Transactions API Routes

Ye module wallet ki transaction history se related
endpoints handle karta hai, aur unhe CSV dataset ke
roop mein bhi save karta hai.
"""

from fastapi import APIRouter, HTTPException
from blockchain.transaction_service import transaction_service
from blockchain.dataset_service import dataset_service
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/wallet/{address}/transactions")
def get_wallet_transactions(address: str, limit: int = 25):
    """
    Diye gaye wallet address ki transaction history deta hai,
    aur usay CSV dataset ke roop mein bhi save karta hai.

    Args:
        address (str): Ethereum wallet address
        limit (int): Kitni transactions chahiye (default 25)

    Returns:
        dict: Wallet address, transaction count, transactions,
              aur saved CSV file ka path

    Raises:
        HTTPException: Agar address invalid ho (400) ya API error aaye (500)
    """
    # Pehle address validate karo
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum wallet address")

    try:
        # Raw transactions Etherscan se fetch karo
        raw_transactions = transaction_service.get_transactions(address, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Transactions ko normalize (standard format mein convert) karo
    normalized_transactions = dataset_service.normalize_ethereum_transactions(raw_transactions)

    # Normalized data ko CSV mein save karo
    csv_path = dataset_service.save_to_csv(address, "ethereum", normalized_transactions)

    return {
        "wallet": address,
        "transaction_count": len(normalized_transactions),
        "transactions": normalized_transactions,
        "csv_saved_at": csv_path
    }