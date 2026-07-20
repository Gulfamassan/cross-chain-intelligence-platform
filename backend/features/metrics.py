"""
Metrics

Ye module wallet transactions se individual calculations karta hai.
Har function ek specific metric nikalta hai — koi complex logic nahi,
sirf pure calculations.
"""

import pandas as pd


def calculate_total_transactions(df: pd.DataFrame) -> int:
    """
    Total kitni transactions hain (sent + received dono milakar).
    """
    return len(df)


def calculate_sent_transactions(df: pd.DataFrame, wallet_address: str) -> int:
    """
    Kitni transactions is wallet ne bheji hain (sender hai).
    """
    wallet_address = wallet_address.lower()
    return len(df[df["from_address"].str.lower() == wallet_address])


def calculate_received_transactions(df: pd.DataFrame, wallet_address: str) -> int:
    """
    Kitni transactions is wallet ko mili hain (receiver hai).
    """
    wallet_address = wallet_address.lower()
    return len(df[df["to_address"].str.lower() == wallet_address])


def calculate_average_value(df: pd.DataFrame) -> float:
    """
    Average transaction value (ETH mein).
    """
    if len(df) == 0:
        return 0.0
    return round(df["value_eth"].mean(), 6)


def calculate_max_value(df: pd.DataFrame) -> float:
    """
    Sabse badi transaction value (ETH mein).
    """
    if len(df) == 0:
        return 0.0
    return round(df["value_eth"].max(), 6)


def calculate_min_value(df: pd.DataFrame) -> float:
    """
    Sabse choti transaction value (ETH mein).
    """
    if len(df) == 0:
        return 0.0
    return round(df["value_eth"].min(), 6)


def calculate_total_sent_value(df: pd.DataFrame, wallet_address: str) -> float:
    """
    Total kitna ETH is wallet ne bheja hai.
    """
    wallet_address = wallet_address.lower()
    sent = df[df["from_address"].str.lower() == wallet_address]
    return round(sent["value_eth"].sum(), 6)


def calculate_total_received_value(df: pd.DataFrame, wallet_address: str) -> float:
    """
    Total kitna ETH is wallet ko mila hai.
    """
    wallet_address = wallet_address.lower()
    received = df[df["to_address"].str.lower() == wallet_address]
    return round(received["value_eth"].sum(), 6)


def calculate_unique_senders(df: pd.DataFrame, wallet_address: str) -> int:
    """
    Kitne alag-alag wallets ne is wallet ko paisa bheja hai.
    """
    wallet_address = wallet_address.lower()
    received = df[df["to_address"].str.lower() == wallet_address]
    return received["from_address"].nunique()


def calculate_unique_receivers(df: pd.DataFrame, wallet_address: str) -> int:
    """
    Kitne alag-alag wallets ko is wallet ne paisa bheja hai.
    """
    wallet_address = wallet_address.lower()
    sent = df[df["from_address"].str.lower() == wallet_address]
    return sent["to_address"].nunique()


def calculate_total_unique_contacts(df: pd.DataFrame, wallet_address: str) -> int:
    """
    Total kitne alag-alag wallets ke saath is wallet ne interact kiya hai
    (chahe paisa bheja ho ya liya ho).
    """
    wallet_address = wallet_address.lower()
    sent_to = set(df[df["from_address"].str.lower() == wallet_address]["to_address"].str.lower())
    received_from = set(df[df["to_address"].str.lower() == wallet_address]["from_address"].str.lower())
    return len(sent_to.union(received_from))


def calculate_active_days(df: pd.DataFrame) -> int:
    """
    Kitne alag-alag dinon mein is wallet ne transactions ki hain.
    """
    if len(df) == 0:
        return 0

    # Timestamp (Unix format) ko readable date mein convert karte hain
    dates = pd.to_datetime(df["timestamp"], unit="s").dt.date
    return dates.nunique()


def calculate_first_last_transaction(df: pd.DataFrame):
    """
    Pehli aur aakhri transaction ka timestamp deta hai.

    Returns:
        tuple: (first_timestamp, last_timestamp)
    """
    if len(df) == 0:
        return None, None

    timestamps = pd.to_datetime(df["timestamp"], unit="s")
    return timestamps.min(), timestamps.max()