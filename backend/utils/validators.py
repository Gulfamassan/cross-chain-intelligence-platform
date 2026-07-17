"""
Wallet Address Validators

Ye module different blockchains ke wallet addresses ko validate karta hai.
Har blockchain ka address format alag hota hai, isliye har ek ke liye
alag function banaya gaya hai.
"""


def is_valid_ethereum_address(address: str) -> bool:
    """
    Check karta hai ke diya gaya address ek valid Ethereum address hai ya nahi.

    Ethereum address ka format:
    - "0x" se shuru hota hai
    - Uske baad 40 hexadecimal characters hote hain
    - Total length 42 characters (0x + 40)

    Args:
        address (str): Wallet address jo check karni hai

    Returns:
        bool: True agar valid hai, False agar invalid hai
    """
    # Pehle check karo ke address khaali to nahi
    if not address:
        return False

    # Address "0x" se start hona chahiye
    if not address.startswith("0x"):
        return False

    # Total length 42 honi chahiye (0x + 40 characters)
    if len(address) != 42:
        return False

    # "0x" ke baad wale hissay ko nikal lo
    hex_part = address[2:]

    # Check karo ke wo hissa sirf hexadecimal characters (0-9, a-f, A-F) se bana hai
    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False