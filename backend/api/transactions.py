"""
Transactions API Routes

Handles wallet transaction history endpoints, and saves the
retrieved data as a CSV dataset.
"""

from fastapi import APIRouter, HTTPException
from blockchain.chain_manager import chain_manager
from blockchain.dataset_service import dataset_service
from utils.validators import is_valid_ethereum_address

router = APIRouter()


@router.get("/wallet/{chain}/{address}/transactions")
def get_wallet_transactions(chain: str, address: str, limit: int = 25):
    """
    Returns the transaction history for the given blockchain and wallet
    address, and also saves it as a CSV dataset.

    Args:
        chain (str): Blockchain name, e.g. "ethereum"
        address (str): Wallet address
        limit (int): Number of transactions to fetch (default 25)

    Returns:
        dict: Wallet address, transaction count, transactions,
              and the path of the saved CSV file

    Raises:
        HTTPException: If the chain is unsupported (400), the address
                        is invalid (400), or an API error occurs (500)
    """
    if not is_valid_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    try:
        collector = chain_manager.get_collector(chain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        raw_transactions = collector.get_transactions(address, limit)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    normalized_transactions = dataset_service.normalize_transactions(
        raw_transactions, collector.network_name()
    )

    csv_path = dataset_service.save_to_csv(address, chain, normalized_transactions)

    return {
        "chain": collector.network_name(),
        "wallet": address,
        "transaction_count": len(normalized_transactions),
        "transactions": normalized_transactions,
        "csv_saved_at": csv_path
    }