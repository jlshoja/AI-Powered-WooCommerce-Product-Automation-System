"""
Unit tests for the Validator class.

Tests:
- Required field validation
- SKU uniqueness validation
- Price range validation
- Stock quantity validation
- Image validation
- Category validation
- Attribute validation
"""

import pytest

from src.excel_parser.models import Product, ProductAttribute, ProductImage, Variation, VariationAttribute
from src.validator.rules import (
    AttributeValidationRule,
    CategoryValidationRule,
    ImageValidationRule,
    PriceRangeRule,
    RequiredFieldRule,
    StockQuantityRule,
    UniqueSKURule,
)
from src.validator.validator import Validator


@pytest.fixture
def validator():
    """Fixture to initialize the Validator."""
    return Validator(min_price=1000, max_price=10000000)


def test_required_field_rule():
    """Test RequiredFieldRule."""
    rule = RequiredFieldRule(field="post_title", value="کیف مردانه")
    assert rule.is_valid is True

    rule = RequiredFieldRule(field="post_title", value=None)
    assert rule.is_valid is False


def test_unique_sku_rule():
    """Test UniqueSKURule."""
    all_skus = {"2106"}
    rule = UniqueSKURule(sku="2107", all_skus=all_skus)
    assert rule.is_valid is True

    rule = UniqueSKURule(sku="2106", all_skus=all_skus)
    assert rule.is_valid is False


def test_price_range_rule():
    """Test PriceRangeRule."""
    rule = PriceRangeRule(field="regular_price", value=5000, min_price=1000, max_price=10000)
    assert rule.is_valid is True

    rule = PriceRangeRule(field="regular_price", value=500, min_price=1000, max_price=10000)
    assert rule.is_valid is False


def test_stock_quantity_rule():
    """Test StockQuantityRule."""
    rule = StockQuantityRule(field="stock_quantity", value=10)
    assert rule.is_valid is True

    rule = StockQuantityRule(field="stock_quantity", value=-1)
    assert rule.is_valid is False


def test_image_validation_rule():
    """Test ImageValidationRule."""
    rule = ImageValidationRule(field="images", value="/uploads/2026/07/men-bag-2106-main.webp")
    assert rule.is_valid is True

    rule = ImageValidationRule(field="images", value="invalid-url")
    assert rule.is_valid is False


def test_category_validation_rule():
    """Test CategoryValidationRule."""
    rule = CategoryValidationRule(field="categories", value=["کیف مردانه", "کیف روزمره مردانه"])
    assert rule.is_valid is True

    rule = CategoryValidationRule(field="categories", value=[])
    assert rule.is_valid is False


def test_attribute_validation_rule():
    """Test AttributeValidationRule."""
    rule = AttributeValidationRule(field="attributes", value={"رنگ": ["سبز", "سرمه ای"]})
    assert rule.is_valid is True

    rule = AttributeValidationRule(field="attributes", value={})
    assert rule.is_valid is False


def test_validate_product(validator):
    """Test validating a product."""
    product = Product(
        id="1",
        post_title="کیف مردانه کد ۲۱۰۶",
        post_status="publish",
        sku="2106",
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه", "کیف روزمره مردانه"],
        images=[
            ProductImage(
                id="1",
                product_sku="2106",
                image_url="/uploads/2026/07/men-bag-2106-main.webp",
                is_main=True,
            )
        ],
        attributes={
            "color": ProductAttribute(key="color", display_name="رنگ", values=["سبز", "سرمه ای"]),
        },
    )

    rules = validator.validate_product(product)
    assert all(rule.is_valid for rule in rules)


def test_validate_variation(validator):
    """Test validating a variation."""
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
            "color": VariationAttribute(key="color", display_name="رنگ", value="سبز"),
        },
    )

    rules = validator.validate_variation(variation)
    assert all(rule.is_valid for rule in rules)


def test_validation_report(validator):
    """Test generating a validation report."""
    product = Product(
        id="1",
        post_title="",  # Invalid: empty post_title
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
            "color": ProductAttribute(key="color", display_name="رنگ", values=["سبز"])
        },
    )

    report = validator.validate_products([product])
    assert len(report.errors) == 1
    assert report.errors[0]["field"] == "post_title"


def test_duplicate_sku(validator):
    """Test duplicate SKU detection."""
    product1 = Product(
        id="1",
        post_title="کیف مردانه کد ۲۱۰۶",
        post_status="publish",
        sku="2106",
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[],
        attributes={
            "color": ProductAttribute(key="color", display_name="رنگ", values=["سبز"])
        },  # Valid attributes to avoid extra errors
    )

    product2 = Product(
        id="2",
        post_title="کیف مردانه کد ۲۱۰۷",
        post_status="publish",
        sku="2106",  # Duplicate SKU
        regular_price=342000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[],
        attributes={
            "color": ProductAttribute(key="color", display_name="رنگ", values=["سرمه ای"])
        },  # Valid attributes to avoid extra errors
    )

    report = validator.validate_products([product1, product2])
    # Expect 1 error: duplicate SKU
    assert len([error for error in report.errors if error["field"] == "sku"]) == 1
