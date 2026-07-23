"""
Image Uploader for the WooCommerce Product Automation System.

Uploads images to WordPress and attachs them to products/variations.
"""

import json
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
        media_cache_path: Path | None = None,
    ):
        """Initialize the ImageUploader."""
        self.woocommerce_client = woocommerce_client
        self.wp_user = wp_user
        self.wp_app_password = wp_app_password
        self.logger = Logger(__name__).get_logger()
        self.media_cache_path = media_cache_path or Path("output/media_cache.json")
        self._media_cache: dict[str, int] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load media cache from file."""
        if self.media_cache_path.exists():
            try:
                with open(self.media_cache_path, encoding="utf-8") as f:
                    self._media_cache = json.load(f)
                self.logger.info(f"Loaded media cache: {len(self._media_cache)} entries")
            except Exception as e:
                self.logger.warning(f"Failed to load media cache: {e}")
                self._media_cache = {}

    def _save_cache(self) -> None:
        """Save media cache to file."""
        try:
            self.media_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.media_cache_path, "w", encoding="utf-8") as f:
                json.dump(self._media_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save media cache: {e}")

    def _find_media_by_filename(self, filename: str) -> int | None:
        """Search WordPress media library for an image by filename."""
        # First check local cache
        if filename in self._media_cache:
            self.logger.info(f"Found image in cache: {filename} (ID: {self._media_cache[filename]})")
            return self._media_cache[filename]

        # Search WordPress media library
        try:
            # WordPress media search by filename
            base_url = self.woocommerce_client.api_url
            if base_url.endswith('/wp-json/wc/v3'):
                base_url = base_url.replace('/wp-json/wc/v3', '')
            url = f"{base_url}/wp-json/wp/v2/media"
            
            if self.wp_user and self.wp_app_password:
                auth = (self.wp_user, self.wp_app_password)
            else:
                auth = (self.woocommerce_client.consumer_key, self.woocommerce_client.consumer_secret)

            # Search by filename
            response = requests.get(
                url, auth=auth, params={"search": filename, "per_page": 5}, timeout=self.woocommerce_client.timeout
            )
            if response.status_code == 200:
                media_items = response.json()
                for item in media_items:
                    # Match by source_url filename or title
                    source_url = item.get("source_url", "")
                    title = item.get("title", {}).get("rendered", "")
                    if filename in source_url or filename in title:
                        media_id = item.get("id")
                        if media_id:
                            self._media_cache[filename] = media_id
                            self._save_cache()
                            self.logger.info(f"Found existing media: {filename} (ID: {media_id})")
                            return media_id
        except Exception as e:
            self.logger.warning(f"Failed to search media by filename: {e}")
        return None

    def upload_image(
        self, image_path: Path, alt_text: str = "", title: str = ""
    ) -> dict[str, Any] | None:
        """Upload an image to WordPress using requests directly for multipart/form-data."""
        try:
            # Check if image already exists in WordPress media library
            filename = image_path.name
            existing_id = self._find_media_by_filename(filename)
            if existing_id:
                self.logger.info(f"Image already exists, reusing: {filename} (ID: {existing_id})")
                return {"id": existing_id, "source_url": f"cached:{existing_id}"}

            # Prepare the multipart form data
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
