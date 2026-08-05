"""
backend/entity_labeling/label_database.py

Curated known-address lookup tables for entity labeling.

NOTE: backend/config/bridges.json already exists in this project.
This file's KNOWN_BRIDGE_CONTRACTS table is a TEMPORARY placeholder —
it should be replaced by loading from config/bridges.json once we
confirm that file's structure, to avoid maintaining two separate
bridge-address lists.
"""

KNOWN_EXCHANGE_WALLETS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Deposit Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance Cold Wallet",
}

# TODO: Replace with config/bridges.json once its structure is confirmed
KNOWN_BRIDGE_CONTRACTS = {
    "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf": "Polygon PoS Bridge",
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "Arbitrum Bridge",
}

KNOWN_SMART_CONTRACTS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
}


def lookup_known_address(address: str) -> dict | None:
    """Returns a known-entity match if found, else None."""
    addr = address.lower()

    if addr in KNOWN_EXCHANGE_WALLETS:
        return {"label": "Exchange Wallet", "name": KNOWN_EXCHANGE_WALLETS[addr], "source": "known_list"}

    if addr in KNOWN_BRIDGE_CONTRACTS:
        return {"label": "Bridge Wallet", "name": KNOWN_BRIDGE_CONTRACTS[addr], "source": "known_list"}

    if addr in KNOWN_SMART_CONTRACTS:
        return {"label": "Smart Contract", "name": KNOWN_SMART_CONTRACTS[addr], "source": "known_list"}

    return None