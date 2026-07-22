"""
Batch Importer for the WooCommerce Product Automation System.

Handles batch imports of products and variations.
"""

from src.ai.manager import AIManager
from src.automation.tracker import ProgressTracker
from src.excel_parser.models import Product
from src.image_manager.manager import ImageManager
from src.reporter.exporter import ValidationReporter
from src.utils.logger import Logger
from src.validator.validator import Validator
from src.woocommerce.client import WooCommerceClient


class BatchImporter:
    """Handles batch imports of products and variations."""

    def __init__(
        self,
        woocommerce_client: WooCommerceClient,
        image_manager: ImageManager,
        ai_manager: AIManager | None = None,
        validator: Validator | None = None,
    ):
        """Initialize the BatchImporter."""
        self.woocommerce_client = woocommerce_client
        self.image_manager = image_manager
        self.ai_manager = ai_manager
        self.validator = validator
        self.tracker = ProgressTracker()
        self.logger = Logger(__name__).get_logger()

    def import_products(self, products: list[Product], batch_size: int = 10) -> None:
        """Import a batch of products."""
        # Validate products if validator is provided
        if self.validator:
            report = self.validator.validate_products(products)
            if report.errors:
                self.logger.error(f"Validation failed for {len(report.errors)} products.")
                ValidationReporter().generate_report(report, "validation_errors.xlsx")
                return

        # Process products in batches
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            self.logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} products")

            for product in batch:
                # Process with AI if AIManager is provided
                if self.ai_manager:
                    product = self.ai_manager.process_product(product)

                # Create or update the product in WooCommerce
                response = self.woocommerce_client.upsert_product(product)
                if not response:
                    self.tracker.track_failure(product, "Failed to create product in WooCommerce")
                    continue

                wc_product_id = response.get("id")
                if not wc_product_id:
                    self.tracker.track_failure(product, "No product ID returned from WooCommerce")
                    continue

                # Get variation IDs if product is variable
                wc_variation_ids = {}
                if product.attributes and response.get("id"):
                    # Fetch variations to get their IDs
                    variations = self.woocommerce_client.get_product_variations(wc_product_id)
                    if variations:
                        for var in variations:
                            if var.get("sku"):
                                wc_variation_ids[var["sku"]] = var["id"]

                # Upload and attach images using WC numeric IDs
                self.image_manager.process_product_images(
                    product, wc_product_id, wc_variation_ids
                )

                self.tracker.track_success(product)
                self.logger.info(f"Successfully imported product: {product.sku}")

        # Generate import report
        self.tracker.generate_report()
