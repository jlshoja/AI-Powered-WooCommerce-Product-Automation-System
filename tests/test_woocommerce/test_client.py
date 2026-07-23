"""
Unit tests for the WooCommerceClient class.

Tests:
- Connection testing
- Product creation/updates
- Variation creation
- Retry logic
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


def test_test_connection_success(client):
    """Test successful connection to WooCommerce API."""
    with patch.object(client.client, "get") as mock_get:
        mock_get.return_value.status_code = 200
        assert client.test_connection() is True


def test_test_connection_failure(client):
    """Test failed connection to WooCommerce API."""
    with patch.object(client.client, "get") as mock_get:
        mock_get.return_value.status_code = 404
        assert client.test_connection() is False


def test_create_product_success(client):
    """Test successful product creation."""
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
    )

    with patch.object(client, "_retry_request") as mock_retry:
        mock_retry.return_value = {"id": 123, "sku": "2106"}
        response = client.create_product(product)
        assert response["id"] == 123


def test_update_product_success(client):
    """Test successful product update."""
    product = Product(
        id="1",
        post_title="کیف مردانه کد ۲۱۰۶",
        post_status="publish",
        sku="2106",
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[],
        attributes={},
    )

    with patch.object(client, "_retry_request") as mock_retry:
        mock_retry.return_value = {"id": 123, "sku": "2106"}
        response = client.update_product(123, product)
        assert response["id"] == 123


def test_create_variation_success(client):
    """Test successful variation creation."""
    variation = Variation(
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

    with patch.object(client, "_retry_request") as mock_retry:
        mock_retry.return_value = {"id": 456, "sku": "2106-green"}
        response = client.create_variation(123, variation)
        assert response["id"] == 456


def test_retry_request_success(client):
    """Test retry logic for successful requests."""
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"id": 123}
        response = client._retry_request("post", "products", data={})
        assert response["id"] == 123


def test_retry_request_failure(client):
    """Test retry logic for failed requests."""
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.status_code = 500
        response = client._retry_request("post", "products", data={})
        assert response is None
