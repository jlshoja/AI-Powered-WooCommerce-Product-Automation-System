"""
Image Uploader for the WooCommerce Product Automation System.

Uploads images to WordPress and attachs them to products/variations.
"""

from pathlib import Path
from typing import Any

import mimetypes

import requests

from src.utils.logger import Logger
from src.woocommerce.client import WooCommerceClient


class ImageUploader:
    """Uploads images to WordPress and attachs them to products/variations."""

    def __init__(
        self,
        woocommerce_client: WooCommerceClient,
        wp_user: str = "",
        wp_app_password: str = "",
    ):
        """Initialize the ImageUploader."""
        self.woocommerce_client = woocommerce_client
        self.wp_user = wp_user
        self.wp_app_password = wp_app_password
        self.logger = Logger(__name__).get_logger()

    def upload_image(
        self, image_path: Path, alt_text: str = "", title: str = ""
    ) -> dict[str, Any] | None:
        """Upload an image to WordPress using requests directly for multipart/form-data."""
        try:
            # Prepare the multipart form data
            filename = image_path.name
            # Detect MIME type from file extension, fallback to content sniffing
            mime_type = mimetypes.guess_type(filename)[0]
            if not mime_type:
                # Sniff first bytes for common image signatures
                with open(image_path, "rb") as f:
                    header = f.read(8)
                if header[:4] == b"\x89PNG":
                    mime_type = "image/png"
                elif header[:2] == b"\xff\xd8":
                    mime_type = "image/jpeg"
                elif header[:4] == b"RIFF" and header[8:12] == b"WEBP":
                    mime_type = "image/webp"
                elif header[:4] == b"GIF8":
                    mime_type = "image/gif"
                else:
                    mime_type = "application/octet-stream"

            with open(image_path, "rb") as f:
                files = {
                    "file": (filename, f, mime_type)
                }
                # Add alt_text and title as form fields
                data = {}
                if alt_text:
                    data["alt_text"] = alt_text
                if title:
                    data["title"] = title

                # Use requests directly for multipart/form-data (woocommerce library doesn't handle it well)
                # WordPress media endpoint is /wp-json/wp/v2/media (not woocommerce)
                base_url = self.woocommerce_client.api_url
                if base_url.endswith('/wp-json/wc/v3'):
                    base_url = base_url.replace('/wp-json/wc/v3', '')
                url = f"{base_url}/wp-json/wp/v2/media"

                # Use WordPress Application Passwords for media upload
                # WooCommerce consumer keys don't have media upload permission
                if self.wp_user and self.wp_app_password:
                    auth = (self.wp_user, self.wp_app_password)
                else:
                    auth = (self.woocommerce_client.consumer_key, self.woocommerce_client.consumer_secret)

                # Retry logic
                for attempt in range(self.woocommerce_client.max_retries):
                    try:
                        self.woocommerce_client.rate_limiter.acquire("media")
                        response = requests.post(
                            url, auth=auth, files=files, data=data, timeout=self.woocommerce_client.timeout
                        )
                        if response.status_code == 201:
                            self.logger.info(f"Image uploaded: {filename}")
                            return response.json()
                        elif response.status_code == 429:
                            self.logger.warning(f"Rate limited (429), attempt {attempt + 1}")
                            import time
                            time.sleep(2 ** attempt)
                        else:
                            self.logger.warning(
                                f"Upload attempt {attempt + 1} failed: {response.status_code} - {response.text}"
                            )
                    except Exception as e:
                        self.logger.warning(f"Upload attempt {attempt + 1} failed: {e}")

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
