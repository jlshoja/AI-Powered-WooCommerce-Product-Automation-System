"""
Image Manager for the WooCommerce Product Automation System.

Orchestrates the image workflow:
1. Download images
2. Validate images
3. Upload images (REST API or FTP)
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
        upload_mode: str = "restapi",
        ftp_config: dict | None = None,
    ):
        """Initialize the ImageManager.

        Args:
            attachment_mode: "gallery" (featured + gallery, no variation images) or "variation" (variation-specific images)
            media_cache_path: Path to JSON file for caching media IDs by filename
            upload_mode: "restapi" (default) or "ftp" (bulk upload for large imports)
            ftp_config: FTP configuration dict (required when upload_mode="ftp")
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
        self.upload_mode = upload_mode  # "restapi" or "ftp"

        # Initialize FTP uploader if needed
        self.ftp_uploader = None
        if upload_mode == "ftp" and ftp_config:
            from src.image_manager.ftp_uploader import FTPUploader

            self.ftp_uploader = FTPUploader(
                host=ftp_config.get("host", ""),
                port=ftp_config.get("port", 21),
                user=ftp_config.get("user", ""),
                password=ftp_config.get("password", ""),
                uploads_path=ftp_config.get("uploads_path", "/public_html/wp-content/uploads"),
                passive_mode=ftp_config.get("passive_mode", True),
                media_cache_path=media_cache_path,
                wp_api_url=ftp_config.get("wp_api_url", ""),
                registration_key=ftp_config.get("registration_key", ""),
            )

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
        if self.upload_mode == "ftp":
            self._process_images_ftp(product, wc_product_id, wc_variation_ids)
        else:
            self._process_images_restapi(product, wc_product_id, wc_variation_ids)

    def _process_images_restapi(
        self,
        product: Product,
        wc_product_id: int,
        wc_variation_ids: dict[str, int] | None = None,
    ) -> None:
        """Process images using REST API (original approach)."""
        # Process main image
        if product.images:
            self._process_image_restapi(product.images[0], wc_product_id, is_main=True)

        # Process gallery images
        for img in product.gallery_images:
            self._process_image_restapi(img, wc_product_id, is_main=False)

        # Process variation images only in "variation" mode
        self.logger.info(f"Image attachment mode: {self.attachment_mode}")
        if self.attachment_mode == "variation" and wc_variation_ids:
            self.logger.info("Processing variation images")
            for variation in product.variations:
                if variation.images and variation.sku in wc_variation_ids:
                    self._process_image_restapi(
                        variation.images[0],
                        wc_product_id,
                        variation_id=wc_variation_ids[variation.sku],
                    )

    def _process_image_restapi(
        self,
        product_image: ProductImage,
        wc_product_id: int,
        variation_id: int | None = None,
        is_main: bool = False,
    ) -> dict[str, Any] | None:
        """Download, validate, upload, and attach an image via REST API."""
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

    def _process_images_ftp(
        self,
        product: Product,
        wc_product_id: int,
        wc_variation_ids: dict[str, int] | None = None,
    ) -> None:
        """Process images using FTP bulk upload."""
        if not self.ftp_uploader:
            self.logger.error("FTP uploader not initialized")
            return

        # Collect all image paths for this product
        image_paths: list[Path] = []
        alt_texts: dict[str, str] = {}

        # Process main image
        if product.images:
            local_filename = getattr(product.images[0], "local_filename", None) or getattr(product.images[0], "id", None)
            image_path = self.downloader.download_image(
                product.images[0].image_url,
                local_filename=local_filename
            )
            if image_path and self.validator.validate_image(image_path):
                image_paths.append(image_path)
                if product.images[0].alt_text:
                    alt_texts[image_path.name] = product.images[0].alt_text

        # Process gallery images
        for img in product.gallery_images:
            local_filename = getattr(img, "local_filename", None) or getattr(img, "id", None)
            image_path = self.downloader.download_image(
                img.image_url,
                local_filename=local_filename
            )
            if image_path and self.validator.validate_image(image_path):
                image_paths.append(image_path)
                if img.alt_text:
                    alt_texts[image_path.name] = img.alt_text

        # Process variation images only in "variation" mode
        if self.attachment_mode == "variation" and wc_variation_ids:
            for variation in product.variations:
                if variation.images and variation.sku in wc_variation_ids:
                    local_filename = getattr(variation.images[0], "local_filename", None) or getattr(variation.images[0], "id", None)
                    image_path = self.downloader.download_image(
                        variation.images[0].image_url,
                        local_filename=local_filename
                    )
                    if image_path and self.validator.validate_image(image_path):
                        image_paths.append(image_path)
                        if variation.images[0].alt_text:
                            alt_texts[image_path.name] = variation.images[0].alt_text

        if not image_paths:
            self.logger.warning(f"No images to process for product {product.sku}")
            return

        # Upload all images via FTP
        uploaded = self.ftp_uploader.upload_batch(image_paths, alt_texts)

        # Register as WordPress media
        registered = self.ftp_uploader.register_media(uploaded)

        # Attach images to product
        for image_path in image_paths:
            filename = image_path.name
            media_id = registered.get(filename) or self.ftp_uploader.get_media_id(filename)
            if media_id:
                is_main = image_path == image_paths[0] if product.images else False
                self.uploader.attach_image_to_product(wc_product_id, media_id, is_main=is_main)
            else:
                self.logger.warning(f"No media ID for {filename}, skipping attachment")

    def bulk_upload_ftp(self, products: list[Product]) -> None:
        """Bulk upload all images for multiple products via FTP.

        This method collects all unique images from all products and uploads them
        in a single FTP session, then registers them as WordPress media.

        Args:
            products: List of products to process
        """
        if not self.ftp_uploader:
            self.logger.error("FTP uploader not initialized")
            return

        self.logger.info(f"Starting FTP bulk upload for {len(products)} products...")

        # Collect all unique image paths
        all_images: dict[str, Path] = {}  # filename -> path
        all_alt_texts: dict[str, str] = {}

        for product in products:
            # Main image
            if product.images:
                local_filename = getattr(product.images[0], "local_filename", None) or getattr(product.images[0], "id", None)
                image_path = self.downloader.download_image(
                    product.images[0].image_url,
                    local_filename=local_filename
                )
                if image_path and self.validator.validate_image(image_path):
                    all_images[image_path.name] = image_path
                    if product.images[0].alt_text:
                        all_alt_texts[image_path.name] = product.images[0].alt_text

            # Gallery images
            for img in product.gallery_images:
                local_filename = getattr(img, "local_filename", None) or getattr(img, "id", None)
                image_path = self.downloader.download_image(
                    img.image_url,
                    local_filename=local_filename
                )
                if image_path and self.validator.validate_image(image_path):
                    all_images[image_path.name] = image_path
                    if img.alt_text:
                        all_alt_texts[image_path.name] = img.alt_text

        self.logger.info(f"Total unique images to upload: {len(all_images)}")

        # Upload all images via FTP
        image_paths = list(all_images.values())
        uploaded = self.ftp_uploader.upload_batch(image_paths, all_alt_texts)

        # Register as WordPress media
        registered = self.ftp_uploader.register_media(uploaded)

        self.logger.info(f"FTP bulk upload complete: {len(registered)} images registered")
