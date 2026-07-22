"""
Image Uploader for the WooCommerce Product Automation System.

Uploads images to WordPress and attachs them to products/variations.
"""

from pathlib import Path
from typing import Any

from src.utils.logger import Logger
from src.woocommerce.client import WooCommerceClient


class ImageUploader:
    """Uploads images to WordPress and attachs them to products/variations."""

    def __init__(self, woocommerce_client: WooCommerceClient):
        """Initialize the ImageUploader."""
        self.woocommerce_client = woocommerce_client
        self.logger = Logger(__name__).get_logger()

    def upload_image(
        self, image_path: Path, alt_text: str = "", title: str = ""
    ) -> dict[str, Any] | None:
        """Upload an image to WordPress."""
        try:
            # Prepare the multipart form data
            filename = image_path.name
            with open(image_path, "rb") as f:
                files = {
                    "file": (filename, f, "image/webp")
                }
                # Add alt_text and title as form fields
                data = {}
                if alt_text:
                    data["alt_text"] = alt_text
                if title:
                    data["title"] = title

                # Use the woocommerce client's _retry_request with the "media" endpoint
                # The woocommerce library handles the media endpoint correctly
                response = self.woocommerce_client._retry_request(
                    "post", "media", files=files, data=data
                )

                if response:
                    self.logger.info(f"Image uploaded: {filename}")
                    return response
                else:
                    self.logger.error(f"Failed to upload image: {filename}")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to upload image {image_path.name}: {e}")
            return None

    def attach_image_to_product(
        self, product_id: int, image_id: int, is_main: bool = False
    ) -> bool:
        """Attach an image to a product."""
        try:
            payload = {"images": [{"id": image_id, "position": 0 if is_main else 1}]}
            response = self.woocommerce_client._retry_request(
                "put", f"products/{product_id}", data=payload
            )

            if response:
                self.logger.info(f"Image {image_id} attached to product {product_id}")
                return True
            else:
                self.logger.error(f"Failed to attach image {image_id} to product {product_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to attach image {image_id} to product {product_id}: {e}")
            return False

    def attach_image_to_variation(self, product_id: int, variation_id: int, image_id: int) -> bool:
        """Attach an image to a variation."""
        try:
            payload = {"image": {"id": image_id}}
            response = self.woocommerce_client._retry_request(
                "put", f"products/{product_id}/variations/{variation_id}", data=payload
            )

            if response:
                self.logger.info(f"Image {image_id} attached to variation {variation_id}")
                return True
            else:
                self.logger.error(f"Failed to attach image {image_id} to variation {variation_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to attach image {image_id} to variation {variation_id}: {e}")
            return False
