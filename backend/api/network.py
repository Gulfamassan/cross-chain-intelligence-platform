"""
Network API Routes

Handles network-related endpoints, such as checking the connection
status to the Ethereum network.
"""

from fastapi import APIRouter
from blockchain.ethereum_service import ethereum_service

router = APIRouter()


@router.get("/network")
def get_network_info():
    """
    Returns current Ethereum network information:
    - Network name
    - Latest block number
    - Connection status

    Returns:
        dict: Network information
    """
    return ethereum_service.get_network_info()