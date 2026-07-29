"""
PDF Generator

Ye main module hai jo ReportLab use karke ek professional
investigation PDF report banata hai — Report Builder, Templates,
aur Charts ko combine karke.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reports.report_builder import report_builder
from reports.charts import report_charts
from reports.templates import report_templates
from performance.timer import performance_timer


class PDFGenerator:
    """
    Ye class poori investigation report ko PDF file mein generate karti hai.
    """

    REPORTS_FOLDER = "generated_reports"

    def __init__(self):
        os.makedirs(self.REPORTS_FOLDER, exist_ok=True)
        self.styles = getSampleStyleSheet()

    @performance_timer.timed("report_generation")
    def generate_pdf_report(self, graph, csv_path: str, wallet_address: str, chain: str) -> str:
        """
        Diye gaye wallet ki poori investigation report ek PDF file mein banata hai.

        Args:
            graph: NetworkX graph object
            csv_path (str): Wallet transactions CSV ka path
            wallet_address (str): Wallet address
            chain (str): Blockchain ka naam

        Returns:
            str: Generated PDF file ka path
        """
        # Step 1: Saara data collect karte hain
        data = report_builder.build_report_data(graph, csv_path, wallet_address, chain)

        # Step 2: Charts banate hain
        risk_chart_path = report_charts.generate_risk_gauge(
            data["risk_analysis"]["risk_score"], wallet_address
        )
        timeline_chart_path = report_charts.generate_timeline_chart(
            data["timeline"], wallet_address
        )

        # Step 3: PDF document banate hain
        pdf_path = os.path.join(self.REPORTS_FOLDER, f"{wallet_address}_report.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []

        title_style = ParagraphStyle(
            "TitleStyle", parent=self.styles["Title"], fontSize=16, spaceAfter=20
        )
        heading_style = ParagraphStyle(
            "HeadingStyle", parent=self.styles["Heading2"], spaceBefore=16, spaceAfter=8
        )
        body_style = self.styles["Normal"]

        # Title
        story.append(Paragraph(report_templates.title_section(wallet_address, chain), title_style))
        story.append(Spacer(1, 10))

        # Wallet Summary
        story.append(Paragraph("Wallet Summary", heading_style))
        for line in report_templates.wallet_summary_section(data["wallet_summary"]):
            story.append(Paragraph(line, body_style))

        # Risk Analysis
        story.append(Paragraph("Risk Analysis", heading_style))
        story.append(Image(risk_chart_path, width=4 * inch, height=0.8 * inch))
        for line in report_templates.risk_section(data["risk_analysis"]):
            story.append(Paragraph(line, body_style))

        # AI Similarity
        story.append(Paragraph("Node2Vec AI Similarity", heading_style))
        story.append(Paragraph(
            f"AI Embedding Available: {'Yes' if data['has_ai_embedding'] else 'No'}",
            body_style
        ))

        # Summary
        story.append(Paragraph("Summary", heading_style))
        story.append(Paragraph(data["summary"]["text_summary"], body_style))

        # Timeline
        story.append(Paragraph("Investigation Timeline", heading_style))
        story.append(Image(timeline_chart_path, width=4.5 * inch, height=2.2 * inch))
        for line in report_templates.timeline_section(data["timeline"]):
            story.append(Paragraph(line, body_style))

        # Recommendation
        story.append(Paragraph("Recommendation", heading_style))
        for line in report_templates.recommendation_section(data["recommendation"]):
            story.append(Paragraph(line, body_style))

        # PDF banate hain
        doc.build(story)

        return pdf_path


# Ek single instance banate hain jo poore project mein import hoga
pdf_generator = PDFGenerator()