"""
Data models for the Excel Parser module.

Defines Pydantic models for:
- Product (parent product)
- Variation (child product)
- Category (hierarchical categories)
- Attribute (product attributes)
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime


class Category(BaseModel):
    """Model for product categories."""
    id: str = Field(..., description="Unique identifier for the category")
    name: str = Field(..., description="Category name (Persian)")
    parent_category: Optional[str] = Field(
        None, description="Parent category name (if hierarchical)"
    )


class Attribute(BaseModel):
    """Model for product attributes."""
    id: str = Field(..., description="Unique identifier for the attribute")
    name: str = Field(..., description="Attribute name (Persian or English)")
    values: List[str] = Field(
        ..., description="List of attribute values (e.g., ['سبز', 'سرمه ای'])"
    )


class ProductImage(BaseModel):
    """Model for product images."""
    id: str = Field(..., description="Unique identifier for the image")
    product_sku: str = Field(..., description="SKU of the product")
    image_url: str = Field(..., description="Relative image path (e.g., /uploads/2026/07/filename.webp)")
    alt_text: Optional[str] = Field(None, description="Alt text for the image")
    title: Optional[str] = Field(None, description="Title for the image")
    is_main: bool = Field(False, description="Whether the image is the main image")


class Variation(BaseModel):
    """Model for product variations."""
    id: str = Field(..., description="Unique identifier for the variation")
    post_title: Optional[str] = Field(None, description="Variation name (Persian)")
    post_status: str = Field("publish", description="Variation status (publish/draft)")
    sku: str = Field(..., description="Unique SKU for the variation")
    parent_sku: str = Field(..., description="SKU of the parent product")
    regular_price: float = Field(..., description="Base price of the variation")
    sale_price: Optional[float] = Field(None, description="Discounted price (if on sale)")
    manage_stock: str = Field("yes", description="Whether stock is managed (yes/no)")
    stock_quantity: Optional[int] = Field(None, description="Stock count (default: 0 if NaN)")
    stock_status: str = Field("instock", description="Stock status (instock/outofstock)")
    images: List[ProductImage] = Field(
        [], description="List of variation images"
    )
    attributes: Dict[str, str] = Field(
        {}, description="Variation attributes (e.g., {'رنگ': 'سبز'})"
    )


class Product(BaseModel):
    """Model for parent products."""
    id: str = Field(..., description="Unique identifier for the product")
    post_title: str = Field(..., description="Product name (Persian)")
    post_status: str = Field("publish", description="Product status (publish/draft)")
    sku: str = Field(..., description="Unique SKU for the product")
    regular_price: float = Field(..., description="Base price of the product")
    sale_price: Optional[float] = Field(None, description="Discounted price (if on sale)")
    manage_stock: str = Field("yes", description="Whether stock is managed (yes/no)")
    stock_quantity: Optional[int] = Field(None, description="Stock count (default: 0 if NaN)")
    stock_status: str = Field("instock", description="Stock status (instock/outofstock)")
    categories: List[str] = Field(
        ..., description="List of categories (e.g., ['کیف مردانه', 'کیف روزمره مردانه'])"
    )
    description: Optional[str] = Field(None, description="Full product description")
    short_description: Optional[str] = Field(None, description="Short product description")
    seo_title: Optional[str] = Field(None, description="SEO title (Yoast)")
    seo_description: Optional[str] = Field(None, description="SEO meta description (Yoast)")
    seo_focus_keyword: Optional[str] = Field(None, description="SEO focus keyword (Yoast)")
    canonical_url: Optional[str] = Field(None, description="Canonical URL (Yoast)")
    images: List[ProductImage] = Field(
        [], description="List of product images"
    )
    gallery_images: List[ProductImage] = Field(
        [], description="List of gallery images"
    )
    attributes: Dict[str, List[str]] = Field(
        {}, description="Product attributes (e.g., {'رنگ': ['سبز', 'سرمه ای']})"
    )
    sale_tag: Optional[str] = Field(None, description="Sale tag text (e.g., 'تخفیف')")
    variations: List[Variation] = Field(
        [], description="List of product variations"
    )
    tags: Optional[List[str]] = Field(
        None, description="List of product tags (e.g., ['چرم', 'فروش ویژه'])"
    )