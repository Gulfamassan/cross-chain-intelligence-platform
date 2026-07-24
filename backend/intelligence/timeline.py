"""
Investigation Timeline

Ye module wallet ki transactions ko chronological (time-wise) order
mein arrange karta hai, aur bridge activity ko bhi highlight karta hai —
taake investigator ko ek clear "story" dikhe ke wallet ki activity
kaise unfold hui.
"""

import pandas as pd
from datetime import datetime

from attribution.bridge_detector import bridge_detector


class TimelineBuilder:
    """
    Ye class wallet transactions se ek chronological timeline banati hai.
    """

    def build_timeline(self, csv_path: str, wallet_address: str, chain: str) -> list:
        """
        Diye gaye wallet ki transactions se ek timeline banata hai,
        time ke hisaab se sorted, bridge events highlight kiye hue.

        Args:
            csv_path (str): Transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            list: Timeline events, purane se naye order mein
        """
        df = pd.read_csv(csv_path)
        transactions = df.to_dict("records")

        # Bridge transactions identify karte hain
        bridge_txs = bridge_detector.detect_bridge_transactions(transactions, chain)
        bridge_hashes = {tx.get("tx_hash") for tx in bridge_txs}

        wallet = wallet_address.lower()
        timeline_events = []

        for tx in transactions:
            from_addr = str(tx.get("from_address", "")).lower()
            to_addr = str(tx.get("to_address", "")).lower()

            # Event type decide karte hain
            if tx.get("tx_hash") in bridge_hashes:
                event_type = "Bridge Transfer"
            elif from_addr == wallet:
                event_type = "Sent"
            elif to_addr == wallet:
                event_type = "Received"
            else:
                event_type = "Transaction"

            timestamp = tx.get("timestamp")
            readable_time = self._format_timestamp(timestamp)

            # NaN values ko safe (JSON-compliant) values se replace karte hain
            value_eth = tx.get("value_eth")
            if pd.isna(value_eth):
                value_eth = 0.0

            if pd.isna(timestamp):
                timestamp = None

            timeline_events.append({
                "timestamp": timestamp,
                "datetime": readable_time,
                "event_type": event_type,
                "tx_hash": tx.get("tx_hash"),
                "from_address": tx.get("from_address"),
                "to_address": tx.get("to_address"),
                "value_eth": value_eth,
            })

        # Time ke hisaab se sort karte hain (purane se naye)
        timeline_events.sort(key=lambda e: e["timestamp"] if e["timestamp"] else 0)

        return timeline_events

    def _format_timestamp(self, timestamp) -> str:
        """
        Unix timestamp ko readable date-time string mein convert karta hai.

        Args:
            timestamp: Unix timestamp (seconds)

        Returns:
            str: Readable date-time, ya "Unknown" agar timestamp na ho
        """
        if not timestamp or pd.isna(timestamp):
            return "Unknown"

        try:
            return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            return "Unknown"


# Ek single instance banate hain jo poore project mein import hoga
timeline_builder = TimelineBuilder()