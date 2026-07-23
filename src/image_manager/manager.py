"""
Image Manager for the WooCommerce Product Automation System.

Orchestrates the image workflow:
1. Download images
2. Validate images
3. Upload images
4. Attach images to products/variations
"""

from pathlib import Path
from typing import Any

from src.excel_parser.models import Product, ProductImage
from src.image_manager.downloader import ImageDownloader
from src.image_manager.uploader import ImageUploader
from src.image_manager.validator import ImageValidator
from src.utils.logger import Logger


class ImageManager:
    """Orchestrates the image workflow."""

    def __init__(
        self,
        woocommerce_client,
        local_images_dir: Path | None = None,
        wp_user: str = "",
        wp_app_password: str = "",
        attachment_mode: str = "gallery",
        media_cache_path: Path | None = None,
    ):
        """Initialize the ImageManager.

        Args:
            attachment_mode: "gallery" (featured + gallery, no variation images) or "variation" (variation-specific images)
            media_cache_path: Path to JSON file for caching media IDs by filename
        """
        self.downloader = ImageDownloader(local_images_dir=local_images_dir)
        self.validator = ImageValidator()
        self.uploader = ImageUploader(
            woocommerce_client,
            wp_user=wp_user,
            wp_app_password=wp_app_password,
            media_cache_path=media_cache_path,
        )
        self.logger = Logger(__name__).get_logger()
        self.attachment_mode = attachment_mode  # "gallery" or "variation"

    def process_product_images(
        self,
        product: Product,
        wc_product_id: int,
        wc_variation_ids: dict[str, int] | None = None,
    ) -> None:
        """Process all images for a product.

        Args:
            product: Product model with image data
            wc_product_id: WooCommerce numeric product ID
            wc_variation_ids: Optional mapping of variation SKU -> WC variation ID
        """
        # Process main image
        if product.images:
            self._process_image(product.images[0], wc_product_id, is_main=True)

        # Process gallery images
        for img in product.gallery_images:
            self._process_image(img, wc_product_id, is_main=False)

        # Process variation images only in "variation" mode
        if self.attachment_mode == "variation" and wc_variation_ids:
            for variation in product.variations:
                if variation.images and variation.sku in wc_variation_ids:
                    self._process_image(
                        variation.images[0],
                        wc_product_id,
                        variation_id=wc_variation_ids[variation.sku],
                    )

    def _process_image(
        self,
        product_image: ProductImage,
        wc_product_id: int,
        variation_id: int | None = None,
        is_main: bool = False,
    ) -> dict[str, Any] | None:
        """Download, validate, upload, and attach an image.

        Args:
            product_image: ProductImage model with image data
            wc_product_id: WooCommerce numeric product ID
            variation_id: Optional WooCommerce numeric variation ID
            is_main: Whether this is the main product image
        """
        # Use product_image.id as local filename hint
        local_filename = getattr(product_image, "local_filename", None) or getattr(product_image, "id", None)

        # Download the image
        image_path = self.downloader.download_image(
            product_image.image_url,
            local_filename=local_filename
        )
        if not image_path:
            return None

        # Validate the image
        if not self.validator.validate_image(image_path):
            return None

        # Upload the image
        upload_response = self.uploader.upload_image(
            image_path, alt_text=product_image.alt_text, title=product_image.title
        )
        if not upload_response:
            return None

        # Attach the image
        image_id = upload_response["id"]
        if variation_id:
            success = self.uploader.attach_image_to_variation(wc_product_id, variation_id, image_id)
        else:
            success = self.uploader.attach_image_to_product(wc_product_id, image_id, is_main=is_main)

        return upload_response if success else None
