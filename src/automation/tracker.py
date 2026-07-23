"""
Progress Tracker for the WooCommerce Product Automation System.

Tracks import progress with per-stage checkpoints and generates reports.
"""

import json
from datetime import datetime
from pathlib import Path

from src.excel_parser.models import Product
from src.utils.logger import Logger


# Pipeline stages in order
STAGES = ["product_created", "variations_created", "images_uploaded", "completed"]


class ProgressTracker:
    """Tracks import progress with per-stage checkpoints."""

    def __init__(self, checkpoint_path: Path | None = None):
        """Initialize the ProgressTracker.

        Args:
            checkpoint_path: Path to JSON checkpoint file for persisting progress
        """
        self.logger = Logger(__name__).get_logger()
        self.imported_products: list[dict[str, str]] = []
        self.failed_products: list[dict[str, str]] = []
        self._checkpoints: dict[str, dict] = {}
        self._checkpoint_path = checkpoint_path or Path("output/import_checkpoint.json")

        if self._checkpoint_path.exists():
            self._load_checkpoints()

    def _load_checkpoints(self) -> None:
        """Load checkpoints from disk."""
        try:
            with open(self._checkpoint_path, "r", encoding="utf-8") as f:
                self._checkpoints = json.load(f)
            self.logger.info(f"Loaded checkpoints: {len(self._checkpoints)} products")
        except Exception as e:
            self.logger.warning(f"Failed to load checkpoints: {e}")
            self._checkpoints = {}

    def _save_checkpoints(self) -> None:
        """Save checkpoints to disk."""
        try:
            self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(self._checkpoints, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save checkpoints: {e}")

    def get_stage(self, sku: str) -> str | None:
        """Get the last completed stage for a product.

        Returns:
            Stage name (e.g. "product_created") or None if not started
        """
        cp = self._checkpoints.get(sku)
        if not cp:
            return None
        return cp.get("stage")

    def is_completed(self, sku: str) -> bool:
        """Check if a product was fully imported."""
        return self.get_stage(sku) == "completed"

    def should_skip_stage(self, sku: str, stage: str) -> bool:
        """Check if a stage should be skipped (already completed)."""
        current = self.get_stage(sku)
        if current is None:
            return False
        try:
            current_idx = STAGES.index(current)
            target_idx = STAGES.index(stage)
            return current_idx >= target_idx
        except ValueError:
            return False

    def set_stage(self, sku: str, stage: str, product_id: int | None = None, error: str | None = None) -> None:
        """Record completion of a stage for a product.

        Args:
            sku: Product SKU
            stage: Stage name (must be in STAGES)
            product_id: WooCommerce product ID (for reference)
            error: Error message if stage failed
        """
        if stage not in STAGES:
            self.logger.warning(f"Unknown stage: {stage}")
            return

        self._checkpoints[sku] = {
            "stage": stage,
            "product_id": product_id,
            "error": error,
            "updated_at": datetime.now().isoformat(),
        }
        self._save_checkpoints()

    def track_success(self, product: Product) -> None:
        """Track a successfully imported product."""
        self.imported_products.append(
            {"sku": product.sku, "name": product.post_title, "status": "success"}
        )
        self.set_stage(product.sku, "completed")
        self.logger.info(f"Tracked success: {product.sku}")

    def track_failure(self, product: Product, error: str, stage: str | None = None) -> None:
        """Track a failed product import."""
        self.failed_products.append(
            {"sku": product.sku, "name": product.post_title, "status": "failed", "error": error}
        )
        if stage:
            self.set_stage(product.sku, stage, error=error)
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

    def clear_checkpoints(self) -> None:
        """Clear all checkpoints (for fresh import)."""
        self._checkpoints = {}
        self._save_checkpoints()
        self.logger.info("Checkpoints cleared")
