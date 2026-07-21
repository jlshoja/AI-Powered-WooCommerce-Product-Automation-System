"""
Progress Tracker for the WooCommerce Product Automation System.

Tracks import progress and generates reports.
"""

from typing import List, Dict
from src.excel_parser.models import Product
from src.utils.logger import Logger


class ProgressTracker:
    """Tracks import progress and generates reports."""

    def __init__(self):
        """Initialize the ProgressTracker."""
        self.logger = Logger(__name__).get_logger()
        self.imported_products: List[Dict[str, str]] = []
        self.failed_products: List[Dict[str, str]] = []

    def track_success(self, product: Product) -> None:
        """Track a successfully imported product."""
        self.imported_products.append({
            "sku": product.sku,
            "name": product.post_title,
            "status": "success"
        })
        self.logger.info(f"Tracked success: {product.sku}")

    def track_failure(self, product: Product, error: str) -> None:
        """Track a failed product import."""
        self.failed_products.append({
            "sku": product.sku,
            "name": product.post_title,
            "status": "failed",
            "error": error
        })
        self.logger.error(f"Tracked failure: {product.sku} - {error}")

    def generate_report(self, file_path: str = "import_report.xlsx") -> None:
        """Generate an import report."""
        import pandas as pd
        
        report = self.imported_products + self.failed_products
        if report:
            df = pd.DataFrame(report)
            df.to_excel(file_path, index=False)
            self.logger.info(f"Import report generated: {file_path}")
        else:
            self.logger.warning("No import data to report.")