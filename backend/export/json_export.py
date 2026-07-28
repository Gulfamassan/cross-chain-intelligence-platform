"""
JSON Export

Ye module wallet ki poori investigation data ko JSON file
ke roop mein export karta hai (poora nested structure).
"""

import os
import json

from intelligence.intelligence_engine import intelligence_engine


class JSONExporter:
    """
    Ye class wallet report ko JSON file mein export karti hai.
    """

    EXPORT_FOLDER = "exported_reports"

    def __init__(self):
        os.makedirs(self.EXPORT_FOLDER, exist_ok=True)

    def export(self, graph, csv_path: str, wallet_address: str, chain: str) -> str:
        """
        Wallet ki poori report ko JSON file mein export karta hai.

        Returns:
            str: Generated JSON file ka path
        """
        report = intelligence_engine.generate_report(graph, csv_path, wallet_address, chain)

        file_path = os.path.join(self.EXPORT_FOLDER, f"{wallet_address}_report.json")

        with open(file_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return file_path


# Ek single instance banate hain jo poore project mein import hoga
json_exporter = JSONExporter()