"""
CSV Export

Ye module wallet ki poori investigation data ko CSV format
mein export karta hai (flat, tabular structure).
"""

import os
import pandas as pd

from intelligence.intelligence_engine import intelligence_engine


class CSVExporter:
    """
    Ye class wallet report ko CSV format mein export karti hai.
    """

    EXPORT_FOLDER = "exported_reports"

    def __init__(self):
        os.makedirs(self.EXPORT_FOLDER, exist_ok=True)

    def export(self, graph, csv_path: str, wallet_address: str, chain: str) -> str:
        """
        Wallet ki summary data ko CSV mein export karta hai.

        Returns:
            str: Generated CSV file ka path
        """
        report = intelligence_engine.generate_report(graph, csv_path, wallet_address, chain)

        # Wallet summary ko ek row wali table banate hain
        summary_df = pd.DataFrame([report["wallet_summary"]])

        file_path = os.path.join(self.EXPORT_FOLDER, f"{wallet_address}_summary.csv")
        summary_df.to_csv(file_path, index=False)

        return file_path


# Ek single instance banate hain jo poore project mein import hoga
csv_exporter = CSVExporter()