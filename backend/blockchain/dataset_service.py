"""
Dataset Service

Ye module raw blockchain transactions ko ek standard (normalized)
format mein convert karta hai, aur unhe CSV file ke roop mein save karta hai.

Standard Schema (har blockchain ke liye same):
tx_hash, chain, from_address, to_address, value_eth,
gas_used, gas_price, timestamp, block_number, status
"""

import os
import pandas as pd


class DatasetService:
    """
    Ye class transactions ko normalize karke CSV mein save karti hai.
    """

    DATASETS_FOLDER = "datasets"

    def normalize_ethereum_transactions(self, transactions: list) -> list:
        """
        Etherscan se aaye raw transactions ko standard schema mein convert karta hai.

        Args:
            transactions (list): Etherscan se aayi raw transactions ki list

        Returns:
            list: Normalized transactions ki list
        """
        normalized = []

        for tx in transactions:
            normalized.append({
                "tx_hash": tx.get("hash"),
                "chain": "Ethereum",
                "from_address": tx.get("from"),
                "to_address": tx.get("to"),
                # Etherscan value "Wei" mein deta hai, ETH mein convert kar rahe hain
                "value_eth": int(tx.get("value", 0)) / (10 ** 18),
                "gas_used": tx.get("gasUsed"),
                "gas_price": tx.get("gasPrice"),
                "timestamp": tx.get("timeStamp"),
                "block_number": tx.get("blockNumber"),
                # Etherscan "0" deta hai success ke liye, "1" failure ke liye
                "status": "Success" if tx.get("isError") == "0" else "Failed",
            })

        return normalized

    def save_to_csv(self, address: str, chain: str, transactions: list) -> str:
        """
        Normalized transactions ko CSV file mein save karta hai.

        Args:
            address (str): Wallet address (file ka naam banega)
            chain (str): Blockchain ka naam (jaise "ethereum")
            transactions (list): Normalized transactions ki list

        Returns:
            str: Saved CSV file ka path
        """
        # Folder path banate hain: datasets/ethereum/
        folder_path = os.path.join(self.DATASETS_FOLDER, chain.lower())

        # Agar folder exist nahi karta, to bana do
        os.makedirs(folder_path, exist_ok=True)

        # File ka pura path: datasets/ethereum/0x123....csv
        file_path = os.path.join(folder_path, f"{address}.csv")

        # Transactions ko Pandas DataFrame mein convert karo
        df = pd.DataFrame(transactions)

        # CSV file mein save karo (index column ke bina)
        df.to_csv(file_path, index=False)

        return file_path


# Ek single instance banate hain jo poore project mein import hoga
dataset_service = DatasetService()