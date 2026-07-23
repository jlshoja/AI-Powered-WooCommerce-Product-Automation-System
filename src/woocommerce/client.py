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
        self._category_cache: dict[str, int] = {}

        # Rate limiting
        endpoint_limits = {
            "products": (rate_limit, rate_burst),
            "products/{id}": (rate_limit, rate_burst),
            "products/{id}/variations": (rate_limit, rate_burst),
            "categories": (rate_limit, rate_burst),
            "tags": (rate_limit, rate_burst),
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
                if response.status_code in (200, 201):
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
        """Update a product in WooCommerce and sync its variations."""
        payload = self._map_product_to_payload(product)
        response = self._retry_request("put", f"products/{product_id}", data=payload)
        if response:
            self.logger.info(f"Product updated: {product.sku}")
            if product.attributes:
                self._sync_variations(product_id, product)
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

    def _sync_variations(self, product_id: int, product: Product) -> list[int]:
        """Sync variations: create missing ones, return all variation IDs."""
        existing = self.get_product_variations(product_id) or []
        existing_skus = {v["sku"]: v["id"] for v in existing if v.get("sku")}

        created_ids = []
        for variation in product.variations:
            if variation.parent_sku != product.sku:
                continue
            if variation.sku in existing_skus:
                self.logger.info(f"Variation {variation.sku} already exists (ID: {existing_skus[variation.sku]}), updating...")
                self._retry_request(
                    "put",
                    f"products/{product_id}/variations/{existing_skus[variation.sku]}",
                    data=self._map_variation_to_payload(variation),
                )
                created_ids.append(existing_skus[variation.sku])
            else:
                resp = self.create_variation(product_id, variation)
                if resp and resp.get("id"):
                    created_ids.append(resp["id"])

        for sku, var_id in existing_skus.items():
            if var_id not in created_ids:
                self.logger.info(f"Deleting stale variation: {sku} (ID: {var_id})")
                self.delete_variation(product_id, var_id)

        return created_ids

    def resolve_category_ids(self, category_names: list[str]) -> list[dict[str, Any]]:
        """Resolve category names to WC category IDs, creating if needed."""
        resolved = []
        for name in category_names:
            cat_id = self._category_cache.get(name)
            if cat_id is None:
                cat_id = self._find_or_create_category(name)
                if cat_id:
                    self._category_cache[name] = cat_id
            if cat_id:
                resolved.append({"id": cat_id})
            else:
                resolved.append({"name": name})
        return resolved

    def _find_or_create_category(self, name: str) -> int | None:
        """Find a category by name or create it."""
        resp = self._retry_request("get", "products/categories", params={"search": name, "per_page": 10})
        if resp and isinstance(resp, list):
            for cat in resp:
                if cat.get("name") == name:
                    return cat["id"]

        resp = self._retry_request("post", "products/categories", data={"name": name})
        if resp and resp.get("id"):
            self.logger.info(f"Created category: {name} (ID: {resp['id']})")
            return resp["id"]
        return None

    def resolve_tag_ids(self, tag_names: list[str]) -> list[dict[str, Any]]:
        """Resolve tag names to WC tag IDs, creating if needed."""
        resolved = []
        for name in tag_names:
            resp = self._retry_request("get", "products/tags", params={"search": name, "per_page": 10})
            tag_id = None
            if resp and isinstance(resp, list):
                for tag in resp:
                    if tag.get("name") == name:
                        tag_id = tag["id"]
                        break
            if tag_id is None:
                resp = self._retry_request("post", "products/tags", data={"name": name})
                if resp and resp.get("id"):
                    tag_id = resp["id"]
                    self.logger.info(f"Created tag: {name} (ID: {tag_id})")
            if tag_id:
                resolved.append({"id": tag_id})
        return resolved

    def _map_product_to_payload(self, product: Product) -> dict[str, Any]:
        """Map a Product model to a WooCommerce API payload."""
        categories = self.resolve_category_ids(product.categories) if product.categories else []
        is_variable = bool(product.attributes)

        # Determine which attributes are used in variations
        variation_attr_names = set()
        for v in product.variations:
            variation_attr_names.update(v.attributes.keys())

        payload = {
            "name": product.post_title,
            "type": "variable" if is_variable else "simple",
            "status": product.post_status,
            "sku": product.sku,
            "description": product.description or "",
            "short_description": product.short_description or "",
            "categories": categories,
            "attributes": [
                {
                    "name": attr_name,
                    "options": attr_values,
                    "visible": True,
                    "variation": attr_name in variation_attr_names,
                }
                for attr_name, attr_values in product.attributes.items()
            ],
        }

        if is_variable:
            payload["manage_stock"] = False
        else:
            payload["regular_price"] = str(product.regular_price)
            payload["sale_price"] = str(product.sale_price) if product.sale_price else ""
            payload["manage_stock"] = product.manage_stock == "yes"
            payload["stock_quantity"] = product.stock_quantity if product.stock_quantity else 0
            payload["stock_status"] = product.stock_status or "instock"

        if product.tags:
            payload["tags"] = self.resolve_tag_ids(product.tags)
        elif product.sale_tag:
            payload["tags"] = self.resolve_tag_ids([product.sale_tag])

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
            "attributes": [
                {"name": attr_name, "option": attr_value}
                for attr_name, attr_value in variation.attributes.items()
            ],
        }
        # NOTE: Images are NOT included in variation creation payload.
        # They are uploaded separately via media API and attached by ID.
        return payload
