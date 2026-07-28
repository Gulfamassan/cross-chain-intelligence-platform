"""
PDF Export

Ye module PDF export ki functionality ko wrap karta hai
(humari existing pdf_generator.py use karke).
"""

from reports.pdf_generator import pdf_generator


class PDFExporter:
    """
    Ye class wallet report ko PDF format mein export karti hai.
    """

    def export(self, graph, csv_path: str, wallet_address: str, chain: str) -> str:
        """
        Wallet ki report PDF mein export karta hai.

        Returns:
            str: Generated PDF file ka path
        """
        return pdf_generator.generate_pdf_report(graph, csv_path, wallet_address, chain)


# Ek single instance banate hain jo poore project mein import hoga
pdf_exporter = PDFExporter()