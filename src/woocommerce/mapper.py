"""
Product Mapper for the WooCommerce Product Automation System.

Maps Excel data to WooCommerce API payloads.
"""

from typing import Dict, Any
from src.excel_parser.models import Product, Variation


class ProductMapper:
    """Maps Excel data to WooCommerce API payloads."""

    @staticmethod
    def map_product_to_payload(product: Product) -> Dict[str, Any]:
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
                {
                    "src": img.image_url,
                    "alt": img.alt_text or "",
                    "name": img.title or ""
                }
                for img in product.images + product.gallery_images
            ],
            "attributes": [
                {
                    "name": attr_name,
                    "options": attr_values,
                    "visible": True,
                    "variation": True
                }
                for attr_name, attr_values in product.attributes.items()
            ]
        }
        return payload

    @staticmethod
    def map_variation_to_payload(variation: Variation) -> Dict[str, Any]:
        """Map a Variation model to a WooCommerce API payload."""
        payload = {
            "sku": variation.sku,
            "regular_price": str(variation.regular_price),
            "sale_price": str(variation.sale_price) if variation.sale_price else "",
            "manage_stock": variation.manage_stock == "yes",
            "stock_quantity": variation.stock_quantity,
            "stock_status": variation.stock_status,
            "image": [
                {
                    "src": img.image_url,
                    "alt": img.alt_text or "",
                    "name": img.title or ""
                }
                for img in variation.images
            ],
            "attributes": [
                {
                    "name": attr_name,
                    "option": attr_value
                }
                for attr_name, attr_value in variation.attributes.items()
            ]
        }
        return payload