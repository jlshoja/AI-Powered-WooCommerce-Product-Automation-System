"""
Data models for the Excel Parser module.

Defines Pydantic models for:
- Product (parent product)
- Variation (child product)
- Category (hierarchical categories)
- Attribute (product attributes)
"""

from pydantic import BaseModel, Field


class ProductAttribute(BaseModel):
    """Model for product attributes with Persian display name."""

    key: str = Field(..., description="Attribute key (e.g., 'color')")
    display_name: str = Field(..., description="Attribute display name (Persian, e.g., 'رنگ')")
    values: list[str] = Field(
        ..., description="List of attribute values (e.g., ['سبز', 'سرمه ای'])"
    )


class VariationAttribute(BaseModel):
    """Model for variation attributes."""

    key: str = Field(..., description="Attribute key (e.g., 'color')")
    display_name: str = Field(..., description="Attribute display name (Persian, e.g., 'رنگ')")
    value: str = Field(..., description="Attribute value (e.g., 'سبز')")


class Category(BaseModel):
    """Model for product categories."""

    id: str = Field(..., description="Unique identifier for the category")
    name: str = Field(..., description="Category name (Persian)")
    parent_category: str | None = Field(None, description="Parent category name (if hierarchical)")


class Attribute(BaseModel):
    """Model for product attributes."""

    id: str = Field(..., description="Unique identifier for the attribute")
    name: str = Field(..., description="Attribute name (Persian or English)")
    values: list[str] = Field(
        ..., description="List of attribute values (e.g., ['سبز', 'سرمه ای'])"
    )


class ProductImage(BaseModel):
    """Model for product images."""

    id: str = Field(..., description="Unique identifier for the image")
    product_sku: str = Field(..., description="SKU of the product")
    image_url: str = Field(
        ..., description="Relative image path (e.g., /uploads/2026/07/filename.webp)"
    )
    alt_text: str | None = Field(None, description="Alt text for the image")
    title: str | None = Field(None, description="Title for the image")
    is_main: bool = Field(False, description="Whether the image is the main image")
    local_filename: str | None = Field(
        None, description="Local filename for images in local folder (e.g., 2106/main.webp)"
    )


class Variation(BaseModel):
    """Model for product variations."""

    id: str = Field(..., description="Unique identifier for the variation")
    post_title: str | None = Field(None, description="Variation name (Persian)")
    post_status: str = Field("publish", description="Variation status (publish/draft)")
    sku: str = Field(..., description="Unique SKU for the variation")
    parent_sku: str = Field(..., description="SKU of the parent product")
    regular_price: float = Field(..., description="Base price of the variation")
    sale_price: float | None = Field(None, description="Discounted price (if on sale)")
    manage_stock: str = Field("yes", description="Whether stock is managed (yes/no)")
    stock_quantity: int | None = Field(None, description="Stock count (default: 0 if NaN)")
    stock_status: str = Field("instock", description="Stock status (instock/outofstock)")
    images: list[ProductImage] = Field([], description="List of variation images")
    attributes: dict[str, VariationAttribute] = Field(
        {}, description="Variation attributes (e.g., {'رنگ': VariationAttribute(key='color', display_name='رنگ', value='سبز')})"
    )


class Product(BaseModel):
    """Model for parent products."""

    id: str = Field(..., description="Unique identifier for the product")
    post_title: str = Field(..., description="Product name (Persian)")
    post_status: str = Field("publish", description="Product status (publish/draft)")
    sku: str = Field(..., description="Unique SKU for the product")
    regular_price: float = Field(..., description="Base price of the product")
    sale_price: float | None = Field(None, description="Discounted price (if on sale)")
    manage_stock: str = Field("yes", description="Whether stock is managed (yes/no)")
    stock_quantity: int | None = Field(None, description="Stock count (default: 0 if NaN)")
    stock_status: str = Field("instock", description="Stock status (instock/outofstock)")
    categories: list[str] = Field(
        ..., description="List of categories (e.g., ['کیف مردانه', 'کیف روزمره مردانه'])"
    )
    description: str | None = Field(None, description="Full product description")
    short_description: str | None = Field(None, description="Short product description")
    seo_title: str | None = Field(None, description="SEO title (Yoast)")
    seo_description: str | None = Field(None, description="SEO meta description (Yoast)")
    seo_focus_keyword: str | None = Field(None, description="SEO focus keyword (Yoast)")
    canonical_url: str | None = Field(None, description="Canonical URL (Yoast)")
    images: list[ProductImage] = Field([], description="List of product images")
    gallery_images: list[ProductImage] = Field([], description="List of gallery images")
    attributes: dict[str, ProductAttribute] = Field(
        {}, description="Product attributes (e.g., {'color': ProductAttribute(key='color', display_name='رنگ', values=['سبز', 'سرمه ای'])})"
    )
    sale_tag: str | None = Field(None, description="Sale tag text (e.g., 'تخفیف')")
    variations: list[Variation] = Field([], description="List of product variations")
    tags: list[str] | None = Field(
        None, description="List of product tags (e.g., ['چرم', 'فروش ویژه'])"
    )
