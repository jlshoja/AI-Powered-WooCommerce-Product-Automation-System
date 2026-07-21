"""
Validator for the WooCommerce Product Automation System.

Validates product data and generates reports.
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
import pandas as pd
from src.excel_parser.models import Product, Variation
from src.validator.rules import (
    ValidationRule, RequiredFieldRule, UniqueSKURule, PriceRangeRule,
    StockQuantityRule, ImageValidationRule, CategoryValidationRule, AttributeValidationRule
)


class ValidationReport:
    """Generates a validation report for products and variations."""

    def __init__(self):
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []

    def add_error(self, sku: str, field: str, message: str):
        """Add an error to the report."""
        self.errors.append({
            "sku": sku,
            "field": field,
            "message": message
        })

    def add_warning(self, sku: str, field: str, message: str):
        """Add a warning to the report."""
        self.warnings.append({
            "sku": sku,
            "field": field,
            "message": message
        })

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the report to a pandas DataFrame."""
        return pd.DataFrame(self.errors + self.warnings)

    def save_to_excel(self, file_path: Path):
        """Save the report to an Excel file."""
        df = self.to_dataframe()
        if not df.empty:
            df.to_excel(file_path, index=False)


class Validator:
    """Validates product data against a set of rules."""

    def __init__(self, min_price: float = 1000, max_price: float = 10000000):
        self.min_price = min_price
        self.max_price = max_price
        self.all_skus: Set[str] = set()

    def validate_product(self, product: Product) -> List[ValidationRule]:
        """Validate a single product."""
        rules = []
        
        # Required fields
        rules.append(RequiredFieldRule(field="post_title", value=product.post_title))
        rules.append(RequiredFieldRule(field="sku", value=product.sku))
        rules.append(RequiredFieldRule(field="regular_price", value=str(product.regular_price)))
        rules.append(RequiredFieldRule(field="stock_status", value=product.stock_status))
        
        # SKU uniqueness
        rules.append(UniqueSKURule(sku=product.sku, all_skus=self.all_skus))
        self.all_skus.add(product.sku)
        
        # Price range
        rules.append(PriceRangeRule(
            field="regular_price", 
            value=product.regular_price, 
            min_price=self.min_price, 
            max_price=self.max_price
        ))
        
        # Stock quantity
        rules.append(StockQuantityRule(field="stock_quantity", value=product.stock_quantity))
        
        # Image validation
        if product.images:
            rules.append(ImageValidationRule(field="images", value=product.images[0].image_url))
        
        # Category validation
        rules.append(CategoryValidationRule(field="categories", value=product.categories))
        
        # Attribute validation
        rules.append(AttributeValidationRule(field="attributes", value=product.attributes))
        
        return rules

    def validate_variation(self, variation: Variation) -> List[ValidationRule]:
        """Validate a single variation."""
        rules = []
        
        # Required fields
        rules.append(RequiredFieldRule(field="sku", value=variation.sku))
        rules.append(RequiredFieldRule(field="parent_sku", value=variation.parent_sku))
        rules.append(RequiredFieldRule(field="regular_price", value=str(variation.regular_price)))
        rules.append(RequiredFieldRule(field="stock_status", value=variation.stock_status))
        
        # SKU uniqueness
        rules.append(UniqueSKURule(sku=variation.sku, all_skus=self.all_skus))
        self.all_skus.add(variation.sku)
        
        # Price range
        rules.append(PriceRangeRule(
            field="regular_price", 
            value=variation.regular_price, 
            min_price=self.min_price, 
            max_price=self.max_price
        ))
        
        # Stock quantity
        rules.append(StockQuantityRule(field="stock_quantity", value=variation.stock_quantity))
        
        # Image validation
        if variation.images:
            rules.append(ImageValidationRule(field="images", value=variation.images[0].image_url))
        
        return rules

    def validate_products(self, products: List[Product]) -> ValidationReport:
        """Validate a list of products."""
        report = ValidationReport()
        
        for product in products:
            rules = self.validate_product(product)
            for rule in rules:
                if not rule.is_valid:
                    report.add_error(product.sku, rule.field, rule.message)
        
        return report

    def validate_variations(self, variations: List[Variation]) -> ValidationReport:
        """Validate a list of variations."""
        report = ValidationReport()
        
        for variation in variations:
            rules = self.validate_variation(variation)
            for rule in rules:
                if not rule.is_valid:
                    report.add_error(variation.sku, rule.field, rule.message)
        
        return report

    def validate_all(self, products: List[Product], variations: List[Variation]) -> ValidationReport:
        """Validate both products and variations."""
        report = self.validate_products(products)
        variation_report = self.validate_variations(variations)
        
        # Merge reports
        report.errors.extend(variation_report.errors)
        report.warnings.extend(variation_report.warnings)
        
        return report