"""
Scheduler for the WooCommerce Product Automation System.

Handles scheduling and incremental updates.
"""

from datetime import datetime

from src.automation.importer import BatchImporter
from src.excel_parser.models import Product
from src.utils.logger import Logger


class Scheduler:
    """Handles scheduling and incremental updates."""

    def __init__(self, importer: BatchImporter):
        """Initialize the Scheduler."""
        self.importer = importer
        self.logger = Logger(__name__).get_logger()

    def schedule_import(self, products: list[Product], schedule_time: datetime) -> None:
        """Schedule an import for a specific time."""
        delay = (schedule_time - datetime.now()).total_seconds()
        if delay > 0:
            self.logger.info(f"Scheduling import for {schedule_time}. Waiting {delay} seconds.")
            # In a real implementation, use threading.Timer or a task scheduler
            import time

            time.sleep(delay)

        self.importer.import_products(products)

    def incremental_import(self, products: list[Product], last_import_time: datetime) -> None:
        """Import only products modified since the last import."""
        new_products = [
            product
            for product in products
            if datetime.strptime(product.id, "%Y%m%d%H%M%S") > last_import_time
        ]

        if new_products:
            self.logger.info(
                f"Found {len(new_products)} new/modified products since {last_import_time}."
            )
            self.importer.import_products(new_products)
        else:
            self.logger.info("No new/modified products found.")
