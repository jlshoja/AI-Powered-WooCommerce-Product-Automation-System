"""
Unit tests for the WooCommerceClient class (Variable Products).

Tests:
- Variable product creation
- Variation creation
"""

from unittest.mock import patch

import pytest

from src.excel_parser.models import Product, ProductAttribute, ProductImage, Variation, VariationAttribute
from src.woocommerce.client import WooCommerceClient


@pytest.fixture
def client():
    """Fixture to initialize the WooCommerceClient."""
    return WooCommerceClient(
        api_url="https://luxbaz.com/wp-json/wc/v3",
        consumer_key="ck_test",
        consumer_secret="cs_test",
        timeout=30,
        max_retries=3,
    )


def test_create_variable_product(client):
    """Test creating a variable product with variations."""
    product = Product(
        id="1",
        post_title="کیف مردانه کد ۲۱۰۶",
        post_status="publish",
        sku="2106",
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[
            ProductImage(
                id="1",
                product_sku="2106",
                image_url="/uploads/2026/07/men-bag-2106-main.webp",
                is_main=True,
            )
        ],
        attributes={
            "color": ProductAttribute(key="color", display_name="رنگ", values=["سبز", "سرمه ای"])
        },
        variations=[
            Variation(
                id="1",
                sku="2106-green",
                parent_sku="2106",
                regular_price=342000,
                stock_quantity=10,
                stock_status="instock",
                images=[
                    ProductImage(
                        id="1",
                        product_sku="2106-green",
                        image_url="/uploads/2026/07/men-bag-2106-green.webp",
                        is_main=True,
                    )
                ],
                attributes={
                    "color": VariationAttribute(key="color", display_name="رنگ", value="سبز")
                },
            )
        ],
    )

    with patch.object(client, "_retry_request") as mock_retry:
        mock_retry.side_effect = [
            [{"id": 100, "name": "کیف مردانه"}],  # Category resolution (GET)
            {"id": 123, "sku": "2106"},  # Product creation (POST)
            [],  # get_product_variations (empty = no existing)
            {"id": 456, "sku": "2106-green"},  # Variation creation (POST)
        ]
        response = client.create_product(product)
        assert response["id"] == 123
        assert mock_retry.call_count == 4  # Category + Product + Get variations + Create variation


def test_create_variation_failure(client):
    """Test variation creation failure."""
    variation = Variation(
        id="1",
        sku="2106-green",
        parent_sku="2106",
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        images=[],
        attributes={
            "color": VariationAttribute(key="color", display_name="رنگ", value="سبز")
        },
    )

    with patch.object(client, "_retry_request") as mock_retry:
        mock_retry.return_value = None  # Simulate failure
        response = client.create_variation(123, variation)
        assert response is None
