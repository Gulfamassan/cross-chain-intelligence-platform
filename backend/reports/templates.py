"""
Report Templates

Ye module PDF report ke text sections ke liye readable templates
(formatted strings) banata hai.
"""


class ReportTemplates:
    """
    Ye class report ke har section ke liye text format karti hai.
    """

    def title_section(self, wallet_address: str, chain: str) -> str:
        return f"Investigation Report: {wallet_address} ({chain.title()})"

    def wallet_summary_section(self, wallet_summary: dict) -> list:
        return [
            f"Blockchain: {wallet_summary.get('chain', 'N/A')}",
            f"Total Transactions: {wallet_summary.get('transactions', 0)}",
            f"Graph Connections: {wallet_summary.get('graph_connections', 0)}",
            f"Cluster: {wallet_summary.get('cluster', 'N/A')}",
            f"Centrality Score: {wallet_summary.get('centrality_score', 0)}",
            f"Total Sent: {wallet_summary.get('total_sent_eth', 0)} ETH",
            f"Total Received: {wallet_summary.get('total_received_eth', 0)} ETH",
            f"Unique Contacts: {wallet_summary.get('unique_contacts', 0)}",
            f"Active Days: {wallet_summary.get('active_days', 0)}",
        ]

    def risk_section(self, risk_analysis: dict) -> list:
        lines = [
            f"Risk Score: {risk_analysis.get('risk_score', 0)}/100",
            f"Risk Level: {risk_analysis.get('risk_level', 'N/A')}",
        ]
        indicators = risk_analysis.get("indicators", {})
        for key, value in indicators.items():
            lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
        return lines

    def recommendation_section(self, recommendation: dict) -> list:
        lines = [f"Priority: {recommendation.get('priority', 'N/A')}"]
        for reason in recommendation.get("reasons", []):
            lines.append(f"  - {reason}")
        return lines

    def timeline_section(self, timeline: list, max_events: int = 15) -> list:
        lines = []
        for event in timeline[:max_events]:
            lines.append(
                f"{event.get('datetime', 'Unknown')} | {event.get('event_type', '')} | "
                f"{event.get('value_eth', 0)} ETH"
            )
        return lines


# Ek single instance banate hain jo poore project mein import hoga
report_templates = ReportTemplates()