"""
Network API Routes

Ye module network-related endpoints handle karta hai,
jaise Ethereum network se connection check karna.
"""

from fastapi import APIRouter
from blockchain.ethereum_service import ethereum_service

# Router banate hain jo main.py mein include hoga
router = APIRouter()


@router.get("/network")
def get_network_info():
    """
    Ethereum network ki current information deta hai:
    - Network ka naam
    - Latest block number
    - Connection status

    Returns:
        dict: Network information
    """
    return ethereum_service.get_network_info()