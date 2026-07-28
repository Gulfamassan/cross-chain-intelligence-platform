"""
Report Charts

Ye module PDF report ke liye chhote charts (images) banata hai —
jaise risk score gauge, timeline bar chart.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class ReportCharts:
    """
    Ye class report ke andar embed hone wale charts banati hai.
    """

    CHARTS_FOLDER = "report_charts"

    def __init__(self):
        os.makedirs(self.CHARTS_FOLDER, exist_ok=True)

    def generate_risk_gauge(self, risk_score: float, wallet_address: str) -> str:
        """
        Risk score ka ek simple bar chart banata hai (0-100 scale).

        Args:
            risk_score (float): Risk score
            wallet_address (str): Wallet address (filename unique banane ke liye)

        Returns:
            str: Saved chart ka path
        """
        fig, ax = plt.subplots(figsize=(6, 1.2))

        color = "#2ecc71" if risk_score < 40 else "#f39c12" if risk_score < 70 else "#e74c3c"

        ax.barh([0], [risk_score], color=color, height=0.5)
        ax.barh([0], [100], color="#eeeeee", height=0.5, zorder=0)
        ax.barh([0], [risk_score], color=color, height=0.5, zorder=1)
        ax.set_xlim(0, 100)
        ax.set_yticks([])
        ax.set_xlabel("Risk Score")
        ax.text(risk_score + 2, 0, f"{risk_score}/100", va="center", fontsize=10)

        plt.tight_layout()
        path = os.path.join(self.CHARTS_FOLDER, f"{wallet_address}_risk_gauge.png")
        plt.savefig(path, dpi=120)
        plt.close()

        return path

    def generate_timeline_chart(self, timeline: list, wallet_address: str) -> str:
        """
        Timeline events ka ek simple bar chart banata hai (event type counts).

        Args:
            timeline (list): Timeline events ki list
            wallet_address (str): Wallet address

        Returns:
            str: Saved chart ka path
        """
        event_counts = {}
        for event in timeline:
            event_type = event.get("event_type", "Unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(event_counts.keys(), event_counts.values(), color="#2e5395")
        ax.set_title("Transaction Event Types")
        ax.set_ylabel("Count")

        plt.tight_layout()
        path = os.path.join(self.CHARTS_FOLDER, f"{wallet_address}_timeline_chart.png")
        plt.savefig(path, dpi=120)
        plt.close()

        return path


# Ek single instance banate hain jo poore project mein import hoga
report_charts = ReportCharts()