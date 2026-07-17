"""
Transactions API Routes

Ye module wallet ki transaction history se related endpoints
handle karta hai. Ab ye kisi bhi supported blockchain ke saath
kaam karta hai, Chain Manager ke through.
"""

from fastapi import APIRouter, HTTPException
from blockchain.chain_manager import chain_manager
from blockchain.dataset_service import dataset_service
from utils.validators import is_valid_ethereum_address

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/wallet/{chain}/{address}/transactions")
def get_wallet_transactions(chain: str, address: str, limit: int = 25):
    """
    Diye gaye blockchain aur wallet address ki transaction history deta hai,
    aur usay CSV dataset ke roop mein bhi save karta hai.

    Args:
        chain (str): Blockchain ka naam, jaise "ethereum"
        address (str): Wallet address
        limit (int): Kitni transactions chahiye (default 25)

    Returns:
        dict: Wallet address, transaction count, transactions,
              aur saved CSV file ka path

    Raises:
        HTTPException: Agar chain unsupported ho (400), address invalid ho (400),
                        ya API error aaye (500)
    """
    # Address validate karo (abhi sirf Ethereum-style addresses support hain)
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    try:
        # Chain Manager se sahi collector mangwao
        collector = chain_manager.get_collector(chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Us collector se raw transactions fetch karo
        raw_transactions = collector.get_transactions(address, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Transactions ko normalize karo (chain ka naam automatically collector se milega)
    normalized_transactions = dataset_service.normalize_transactions(
        raw_transactions, collector.network_name()
    )

    # Normalized data ko CSV mein save karo (chain ke naam ke folder mein)
    csv_path = dataset_service.save_to_csv(address, chain, normalized_transactions)

    return {
        "chain": collector.network_name(),
        "wallet": address,
        "transaction_count": len(normalized_transactions),
        "transactions": normalized_transactions,
        "csv_saved_at": csv_path
    }