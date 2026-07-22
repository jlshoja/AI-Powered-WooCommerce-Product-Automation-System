"""
WooCommerce REST API Client for the WooCommerce Product Automation System.

Handles:
- Authentication
- Connection testing
- Product creation/updates (including variable products)
- Variation creation/updates
- Retry logic
- Rate limiting
- Logging
"""

import time
from typing import Any

from src.excel_parser.models import Product, Variation
from src.utils.logger import Logger
from src.utils.rate_limiter import RateLimiter
from woocommerce import API


class WooCommerceClient:
    """Client for interacting with the WooCommerce REST API."""

    def __init__(
        self,
        api_url: str,
        consumer_key: str,
        consumer_secret: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: float = 1.0,
        rate_burst: int = 2,
    ):
        """Initialize the WooCommerce client."""
        self.api_url = api_url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = Logger(__name__).get_logger()
        self.client = self._initialize_client()

        # Rate limiting
        endpoint_limits = {
            "products": (rate_limit, rate_burst),
            "products/{id}": (rate_limit, rate_burst),
            "products/{id}/variations": (rate_limit, rate_burst),
            "media": (rate_limit * 0.5, rate_burst),
        }
        self.rate_limiter = RateLimiter(
            default_rate=rate_limit,
            default_burst=rate_burst,
            endpoint_limits=endpoint_limits,
        )

    def _initialize_client(self) -> API:
        """Initialize the WooCommerce API client."""
        return API(
            url=self.api_url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            timeout=self.timeout,
            wp_api=True,
            version="wc/v3",
        )

    def test_connection(self) -> bool:
        """Test the connection to the WooCommerce API."""
        try:
            response = self.client.get("system_status")
            if response.status_code == 200:
                self.logger.info("WooCommerce API connection successful.")
                return True
            else:
                self.logger.error(f"WooCommerce API connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"WooCommerce API connection error: {e}")
            return False

    def delete_product(self, product_id: int, force: bool = True) -> bool:
        """Delete a product from WooCommerce."""
        try:
            response = self._retry_request(
                "delete", f"products/{product_id}", params={"force": force}
            )
            if response:
                self.logger.info(f"Product deleted: {product_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete product {product_id}: {e}")
            return False

    def delete_variation(self, product_id: int, variation_id: int, force: bool = True) -> bool:
        """Delete a variation from WooCommerce."""
        try:
            response = self._retry_request(
                "delete",
                f"products/{product_id}/variations/{variation_id}",
                params={"force": force},
            )
            if response:
                self.logger.info(f"Variation deleted: {variation_id} from product {product_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(
                f"Failed to delete variation {variation_id} from product {product_id}: {e}"
            )
            return False

    def _retry_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any] | None:
        """Retry a WooCommerce API request on failure with rate limiting."""
        # Acquire rate limit token
        self.rate_limiter.acquire(endpoint)

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = getattr(self.client, method)(endpoint, **kwargs)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited by server - wait and retry
                    self.logger.warning(f"Rate limited by server (429), attempt {attempt + 1}")
                    time.sleep(2 ** attempt)
                else:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                last_exception = e

        self.logger.error(f"All {self.max_retries} attempts failed. Last error: {last_exception}")
        return None

    def create_product(
        self, product: Product, track_for_rollback: bool = False
    ) -> dict[str, Any] | None:
        """Create a product in WooCommerce.

        Args:
            product: Product to create
            track_for_rollback: If True, return dict with created IDs for potential rollback

        Returns:
            Product response or dict with response and rollback info
        """
        payload = self._map_product_to_payload(product)
        response = self._retry_request("post", "products", data=payload)
        if response:
            self.logger.info(f"Product created: {product.sku}")
            # Create variations if the product is variable
            variation_ids = []
            if product.attributes and response.get("id"):
                variation_ids = self._create_variations(response["id"], product)

            if track_for_rollback:
                return {
                    "product": response,
                    "rollback": {"product_id": response.get("id"), "variation_ids": variation_ids},
                }
        return response

    def update_product(self, product_id: int, product: Product) -> dict[str, Any] | None:
        """Update a product in WooCommerce."""
        payload = self._map_product_to_payload(product)
        response = self._retry_request("put", f"products/{product_id}", data=payload)
        if response:
            self.logger.info(f"Product updated: {product.sku}")
        return response

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        """Get a product from WooCommerce."""
        response = self._retry_request("get", f"products/{product_id}")
        if response:
            self.logger.info(f"Product retrieved: {product_id}")
        return response

    def get_product_by_sku(self, sku: str) -> dict[str, Any] | None:
        """Get a product from WooCommerce by SKU."""
        response = self._retry_request("get", "products", params={"sku": sku, "per_page": 1})
        if response and isinstance(response, list) and len(response) > 0:
            self.logger.info(f"Product found by SKU: {sku}")
            return response[0]
        elif response and isinstance(response, dict) and response.get("sku") == sku:
            self.logger.info(f"Product found by SKU: {sku}")
            return response
        self.logger.info(f"No product found with SKU: {sku}")
        return None

    def get_product_variations(self, product_id: int) -> list[dict[str, Any]] | None:
        """Get all variations for a product."""
        response = self._retry_request("get", f"products/{product_id}/variations", params={"per_page": 100})
        if response and isinstance(response, list):
            self.logger.info(f"Retrieved {len(response)} variations for product {product_id}")
            return response
        return None

    def upsert_product(self, product: Product) -> dict[str, Any] | None:
        """Create or update a product in WooCommerce based on SKU."""
        existing = self.get_product_by_sku(product.sku)
        if existing:
            self.logger.info(
                f"Product with SKU {product.sku} exists (ID: {existing['id']}), updating..."
            )
            return self.update_product(existing["id"], product)
        else:
            self.logger.info(f"Product with SKU {product.sku} not found, creating new...")
            return self.create_product(product)

    def _create_variations(self, product_id: int, product: Product) -> list[int]:
        """Create variations for a variable product.

        Returns:
            List of created variation IDs for potential rollback
        """
        variation_ids = []
        # Group variations by parent_sku (if applicable)
        variations_by_parent = {}
        for variation in product.variations:
            if variation.parent_sku == product.sku:
                if product.sku not in variations_by_parent:
                    variations_by_parent[product.sku] = []
                variations_by_parent[product.sku].append(variation)

        # Create variations
        for variation in variations_by_parent.get(product.sku, []):
            response = self.create_variation(product_id, variation)
            if response and response.get("id"):
                variation_ids.append(response["id"])

        return variation_ids

    def create_variation(self, product_id: int, variation: Variation) -> dict[str, Any] | None:
        """Create a variation for a product in WooCommerce."""
        payload = self._map_variation_to_payload(variation)
        response = self._retry_request("post", f"products/{product_id}/variations", data=payload)
        if response:
            self.logger.info(f"Variation created: {variation.sku}")
        return response

    def rollback_product_creation(self, product_id: int, variation_ids: list[int] = None) -> bool:
        """Rollback product creation by deleting variations and product.

        Args:
            product_id: ID of the product to delete
            variation_ids: List of variation IDs to delete first

        Returns:
            True if all deletions succeeded
        """
        success = True

        # Delete variations first
        if variation_ids:
            for var_id in variation_ids:
                if not self.delete_variation(product_id, var_id):
                    self.logger.error(f"Failed to rollback variation {var_id}")
                    success = False

        # Delete the product
        if not self.delete_product(product_id):
            self.logger.error(f"Failed to rollback product {product_id}")
            success = False

        if success:
            self.logger.info(
                f"Rollback completed for product {product_id} and {len(variation_ids or [])} variations"
            )

        return success

    def _map_product_to_payload(self, product: Product) -> dict[str, Any]:
        """Map a Product model to a WooCommerce API payload."""
        payload = {
            "name": product.post_title,
            "type": "variable" if product.attributes else "simple",
            "status": product.post_status,
            "sku": product.sku,
            "regular_price": str(product.regular_price),
            "sale_price": str(product.sale_price) if product.sale_price else "",
            "manage_stock": product.manage_stock == "yes",
            "stock_quantity": product.stock_quantity,
            "stock_status": product.stock_status,
            "description": product.description or "",
            "short_description": product.short_description or "",
            "categories": [{"name": cat} for cat in product.categories],
            "images": [
                {"src": img.image_url, "alt": img.alt_text or "", "name": img.title or ""}
                for img in product.images + product.gallery_images
            ],
            "attributes": [
                {"name": attr_name, "options": attr_values, "visible": True, "variation": True}
                for attr_name, attr_values in product.attributes.items()
            ],
        }
        return payload

    def _map_variation_to_payload(self, variation: Variation) -> dict[str, Any]:
        """Map a Variation model to a WooCommerce API payload."""
        payload = {
            "sku": variation.sku,
            "regular_price": str(variation.regular_price),
            "sale_price": str(variation.sale_price) if variation.sale_price else "",
            "manage_stock": variation.manage_stock == "yes",
            "stock_quantity": variation.stock_quantity,
            "stock_status": variation.stock_status,
            "image": [
                {"src": img.image_url, "alt": img.alt_text or "", "name": img.title or ""}
                for img in variation.images
            ],
            "attributes": [
                {"name": attr_name, "option": attr_value}
                for attr_name, attr_value in variation.attributes.items()
            ],
        }
        return payload
