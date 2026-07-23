"""
Batch Importer for the WooCommerce Product Automation System.

Handles batch imports of products and variations with per-stage checkpointing.
"""

from pathlib import Path

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
        checkpoint_path: Path | None = None,
    ):
        """Initialize the BatchImporter."""
        self.woocommerce_client = woocommerce_client
        self.image_manager = image_manager
        self.ai_manager = ai_manager
        self.validator = validator
        self.tracker = ProgressTracker(checkpoint_path=checkpoint_path)
        self.logger = Logger(__name__).get_logger()

    def import_products(self, products: list[Product], batch_size: int = 10, resume: bool = False) -> None:
        """Import a batch of products.

        Args:
            products: List of products to import
            batch_size: Number of products per batch
            resume: If True, skip fully completed products
        """
        # Validate products if validator is provided
        if self.validator:
            report = self.validator.validate_products(products)
            if report.errors:
                self.logger.error(f"Validation failed for {len(report.errors)} products.")
                ValidationReporter().generate_report(report, "validation_errors.xlsx")
                return

        # Filter out already-completed products if resuming
        if resume:
            original_count = len(products)
            products = [p for p in products if not self.tracker.is_completed(p.sku)]
            skipped = original_count - len(products)
            if skipped:
                self.logger.info(f"Resume mode: skipped {skipped} completed products, {len(products)} remaining")

        # Process products in batches
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            self.logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} products")

            for product in batch:
                self._import_single_product(product)

        # Generate import report
        self.tracker.generate_report()

    def _import_single_product(self, product: Product) -> None:
        """Import a single product through all pipeline stages."""
        sku = product.sku

        # Stage 1: AI processing (no checkpoint — fast, idempotent)
        if self.ai_manager:
            product = self.ai_manager.process_product(product)

        # Stage 2: Create/update product in WooCommerce
        if not self.tracker.should_skip_stage(sku, "product_created"):
            response = self.woocommerce_client.upsert_product(product)
            if not response:
                self.tracker.track_failure(product, "Failed to create product in WooCommerce", stage="product_created")
                return
            wc_product_id = response.get("id")
            if not wc_product_id:
                self.tracker.track_failure(product, "No product ID returned from WooCommerce", stage="product_created")
                return
            self.tracker.set_stage(sku, "product_created", product_id=wc_product_id)
        else:
            # Resume: get product ID from checkpoint
            cp = self.tracker._checkpoints.get(sku, {})
            wc_product_id = cp.get("product_id")
            if not wc_product_id:
                self.tracker.track_failure(product, "No product ID in checkpoint", stage="product_created")
                return
            self.logger.info(f"Resume: product {sku} already created (ID: {wc_product_id})")

        # Stage 3: Create/update variations
        if not self.tracker.should_skip_stage(sku, "variations_created"):
            wc_variation_ids = {}
            if product.attributes and wc_product_id:
                variations = self.woocommerce_client.get_product_variations(wc_product_id)
                if variations:
                    for var in variations:
                        if var.get("sku"):
                            wc_variation_ids[var["sku"]] = var["id"]
            self.tracker.set_stage(sku, "variations_created")
        else:
            # Resume: fetch existing variations
            wc_variation_ids = {}
            if product.attributes and wc_product_id:
                variations = self.woocommerce_client.get_product_variations(wc_product_id)
                if variations:
                    for var in variations:
                        if var.get("sku"):
                            wc_variation_ids[var["sku"]] = var["id"]
            self.logger.info(f"Resume: variations for {sku} already created")

        # Stage 4: Upload and attach images
        if not self.tracker.should_skip_stage(sku, "images_uploaded"):
            self.image_manager.process_product_images(
                product, wc_product_id, wc_variation_ids
            )
            self.tracker.set_stage(sku, "images_uploaded")
        else:
            self.logger.info(f"Resume: images for {sku} already uploaded")

        self.tracker.track_success(product)
        self.logger.info(f"Successfully imported product: {sku}")
