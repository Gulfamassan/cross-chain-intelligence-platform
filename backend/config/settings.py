"""
Configuration Settings Module

Ye module poore project ki settings aur API keys manage karta hai.
Saari sensitive values (.env) file se load hoti hain, code mein
kabhi hardcode nahi ki jaatin.
"""

import os
from dotenv import load_dotenv

# .env file ko load karo taake environment variables available ho jayein
load_dotenv()


class Settings:
    """
    Project ki saari settings is class mein rakhi jaati hain.
    """

    # Alchemy API Key - blockchain node access ke liye
    ALCHEMY_API_KEY: str = os.getenv("ALCHEMY_API_KEY")

    # Etherscan API Key - wallet transaction history ke liye
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY")

    # Ethereum Mainnet RPC URL (Alchemy key ke saath banaya gaya)
    ALCHEMY_URL: str = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"


# Ek single instance banate hain jo poore project mein import hoga
settings = Settings()