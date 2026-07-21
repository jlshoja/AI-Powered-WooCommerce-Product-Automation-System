"""
Validation rules for the WooCommerce Product Automation System.

Defines rules for:
- Required fields
- SKU uniqueness
- Price ranges
- Stock validation
- Image validation
- Category validation
- Attribute validation
"""

from typing import List, Dict, Optional, Set
from pydantic import BaseModel, ValidationError
from src.excel_parser.models import Product, Variation


class ValidationRule(BaseModel):
    """Base class for validation rules."""
    field: str
    message: str
    is_valid: bool = True


class RequiredFieldRule(ValidationRule):
    """Validate that a field is not None or empty."""
    def __init__(self, field: str, value: Optional[str], **kwargs):
        is_valid = value is not None and str(value).strip() != ""
        message = f"Field '{field}' is required but missing or empty." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)


class UniqueSKURule(ValidationRule):
    """Validate that SKUs are unique across products and variations."""
    def __init__(self, sku: str, all_skus: Set[str], **kwargs):
        is_valid = sku not in all_skus
        message = f"SKU '{sku}' is duplicated." if not is_valid else ""
        super().__init__(field="sku", message=message, is_valid=is_valid, **kwargs)


class PriceRangeRule(ValidationRule):
    """Validate that prices are within a specified range."""
    def __init__(self, field: str, value: float, min_price: float, max_price: float, **kwargs):
        is_valid = min_price <= value <= max_price
        message = f"Field '{field}' must be between {min_price} and {max_price}." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)


class StockQuantityRule(ValidationRule):
    """Validate that stock_quantity is non-negative."""
    def __init__(self, field: str, value: Optional[int], **kwargs):
        is_valid = value is None or value >= 0
        message = f"Field '{field}' must be non-negative." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)


class ImageValidationRule(ValidationRule):
    """Validate that image URLs are not empty and use dynamic paths."""
    def __init__(self, field: str, value: Optional[str], **kwargs):
        is_valid = value is not None and "/uploads/" in value
        message = f"Field '{field}' must be a valid image URL with dynamic path (e.g., /uploads/2026/07/...)." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)


class CategoryValidationRule(ValidationRule):
    """Validate that categories are not empty."""
    def __init__(self, field: str, value: List[str], **kwargs):
        is_valid = len(value) > 0
        message = f"Field '{field}' must have at least one category." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)


class AttributeValidationRule(ValidationRule):
    """Validate that attributes are not empty."""
    def __init__(self, field: str, value: Dict[str, List[str]], **kwargs):
        is_valid = len(value) > 0
        message = f"Field '{field}' must have at least one attribute." if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid, **kwargs)