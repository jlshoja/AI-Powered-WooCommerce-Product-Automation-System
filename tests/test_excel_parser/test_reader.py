"""
Unit tests for the ExcelReader class.

Tests:
- Reading Products worksheet
- Reading Variations worksheet
- Reading Categories worksheet
- Reading Attributes worksheet
- Reading Images worksheet
"""

from pathlib import Path

import pytest

from src.excel_parser.models import Attribute, Category, Product, ProductImage, Variation
from src.excel_parser.reader import ExcelReader

# Path to the test Excel file (relative to project root)
TEST_EXCEL_PATH = Path(__file__).parent.parent.parent / "output" / "Product_Master.xlsx"


@pytest.fixture
def excel_reader():
    """Fixture to initialize the ExcelReader."""
    if not TEST_EXCEL_PATH.exists():
        pytest.skip(f"Test file not found: {TEST_EXCEL_PATH}")
    return ExcelReader(TEST_EXCEL_PATH)


def test_read_products(excel_reader):
    """Test reading the Products worksheet."""
    products = excel_reader.read_products()
    assert len(products) > 0

    # Check the first product
    product = products[0]
    assert isinstance(product, Product)
    assert isinstance(product.sku, str)
    assert isinstance(product.post_title, str)
    assert isinstance(product.regular_price, float)
    assert product.stock_status in ["instock", "outofstock"]
    assert len(product.images) >= 1
    assert product.images[0].is_main is True
    assert "/uploads/" in product.images[0].image_url


def test_read_variations(excel_reader):
    """Test reading the Variations worksheet."""
    variations = excel_reader.read_variations()
    assert len(variations) > 0

    # Check the first variation
    variation = variations[0]
    assert isinstance(variation, Variation)
    assert isinstance(variation.sku, str)
    assert isinstance(variation.parent_sku, str)
    assert isinstance(variation.regular_price, float)
    assert variation.stock_status in ["instock", "outofstock"]
    assert len(variation.images) >= 0
    if variation.images:
        assert "/uploads/" in variation.images[0].image_url


def test_read_categories(excel_reader):
    """Test reading the Categories worksheet."""
    categories = excel_reader.read_categories()
    assert len(categories) > 0

    # Check the first category
    category = categories[0]
    assert isinstance(category, Category)
    assert isinstance(category.name, str)
    assert category.parent_category is None or isinstance(category.parent_category, str)


def test_read_attributes(excel_reader):
    """Test reading the Attributes worksheet."""
    attributes = excel_reader.read_attributes()
    assert len(attributes) > 0

    # Check the first attribute
    attribute = attributes[0]
    assert isinstance(attribute, Attribute)
    assert isinstance(attribute.name, str)
    assert isinstance(attribute.values, list)


def test_read_images(excel_reader):
    """Test reading the Images worksheet."""
    images = excel_reader.read_images()
    assert len(images) > 0

    # Check the first image
    image = images[0]
    assert isinstance(image, ProductImage)
    assert isinstance(image.product_sku, str)
    assert "/uploads/" in image.image_url
