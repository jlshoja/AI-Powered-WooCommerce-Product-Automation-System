"""
Excel Reader for the WooCommerce Product Automation System.

Reads the restructured Excel workbook and parses it into Python data models.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from .models import Product, Variation, Category, Attribute, ProductImage
from datetime import datetime


class ExcelReader:
    """Reads and parses the Excel workbook into data models."""

    def __init__(self, file_path: Path):
        """Initialize the ExcelReader with the file path."""
        self.file_path = file_path
        self.workbook = pd.ExcelFile(file_path)

    def _clean_string(self, value) -> Optional[str]:
        """Convert NaN to None and ensure strings."""
        if pd.isna(value):
            return None
        return str(value)

    def _clean_sku(self, value) -> str:
        """Convert numeric SKUs to strings."""
        if pd.isna(value):
            return ""
        return str(value)

    def _clean_int(self, value) -> Optional[int]:
        """Convert NaN to None and ensure integers."""
        if pd.isna(value):
            return None
        return int(value)

    def _clean_attribute_value(self, value) -> List[str]:
        """Convert attribute values to strings and split by '|'."""
        if pd.isna(value):
            return []
        if isinstance(value, (int, float)):
            return [str(value)]
        return [v.strip() for v in str(value).split("|") if v.strip()]

    def read_products(self) -> List[Product]:
        """Read and parse the Products worksheet."""
        df_products = self.workbook.parse("Products")
        df_variations = self.workbook.parse("Variations")
        products = []
        
        for _, row in df_products.iterrows():
            # Parse images
            main_image = ProductImage(
                id=self._clean_string(row.get("ID", "")),
                product_sku=self._clean_sku(row["sku"]),
                image_url=self._clean_string(row["images"]),
                alt_text=self._clean_string(row.get("image_alt")),
                title=self._clean_string(row["post_title"]),
                is_main=True
            )
            
            gallery_images = []
            if pd.notna(row.get("gallery_images")):
                gallery_urls = row["gallery_images"].split("|")
                gallery_alts = row.get("gallery_image_alt", "").split("|") if pd.notna(row.get("gallery_image_alt")) else []
                gallery_titles = row.get("image_titles", "").split("|") if pd.notna(row.get("image_titles")) else []
                
                for i, url in enumerate(gallery_urls):
                    gallery_images.append(
                        ProductImage(
                            id=self._clean_string(row.get("ID", "")) + f"_gallery_{i}",
                            product_sku=self._clean_sku(row["sku"]),
                            image_url=self._clean_string(url),
                            alt_text=self._clean_string(gallery_alts[i]) if i < len(gallery_alts) else "",
                            title=self._clean_string(gallery_titles[i]) if i < len(gallery_titles) else "",
                            is_main=False
                        )
                    )
            
            # Parse attributes
            attributes = {}
            for col in df_products.columns:
                if col.startswith("attribute:"):
                    attr_name = col.split(":")[1]
                    attr_values = self._clean_attribute_value(row[col])
                    if attr_values:
                        attributes[attr_name] = attr_values
            
            # Parse variations
            variations = []
            for _, var_row in df_variations[df_variations["parent_sku"] == row["sku"]].iterrows():
                var_images = []
                if pd.notna(var_row.get("images")):
                    var_images.append(
                        ProductImage(
                            id=self._clean_string(var_row.get("ID", "")),
                            product_sku=self._clean_sku(var_row["sku"]),
                            image_url=self._clean_string(var_row["images"]),
                            alt_text=self._clean_string(var_row.get("image_alt")),
                            title=self._clean_string(var_row.get("image_titles")),
                            is_main=True
                        )
                    )
                
                var_attributes = {}
                for col in df_variations.columns:
                    if col.startswith("attribute:"):
                        attr_name = col.split(":")[1]
                        attr_value = self._clean_string(var_row[col])
                        if attr_value:
                            var_attributes[attr_name] = attr_value
                
                variation = Variation(
                    id=self._clean_string(var_row["ID"]),
                    post_title=self._clean_string(var_row.get("post_title")),
                    post_status=self._clean_string(var_row["post_status"]),
                    sku=self._clean_sku(var_row["sku"]),
                    parent_sku=self._clean_sku(var_row["parent_sku"]),
                    regular_price=float(var_row["regular_price"]),
                    sale_price=float(var_row["sale_price"]) if pd.notna(var_row["sale_price"]) else None,
                    manage_stock=self._clean_string(var_row["manage_stock"]),
                    stock_quantity=self._clean_int(var_row["stock_quantity"]),
                    stock_status=self._clean_string(var_row["stock_status"]),
                    images=var_images,
                    attributes=var_attributes
                )
                variations.append(variation)
            
            # Create Product model
            product = Product(
                id=self._clean_string(row["ID"]),
                post_title=self._clean_string(row["post_title"]),
                post_status=self._clean_string(row["post_status"]),
                sku=self._clean_sku(row["sku"]),
                regular_price=float(row["regular_price"]),
                sale_price=float(row["sale_price"]) if pd.notna(row["sale_price"]) else None,
                manage_stock=self._clean_string(row["manage_stock"]),
                stock_quantity=self._clean_int(row["stock_quantity"]),
                stock_status=self._clean_string(row["stock_status"]),
                categories=row["categories"].split(">") if pd.notna(row["categories"]) else [],
                description=self._clean_string(row.get("description")),
                short_description=self._clean_string(row.get("short_description")),
                seo_title=self._clean_string(row.get("meta:_yoast_wpseo_title")),
                seo_description=self._clean_string(row.get("meta:_yoast_wpseo_metadesc")),
                seo_focus_keyword=self._clean_string(row.get("meta:_yoast_wpseo_focuskw")),
                canonical_url=self._clean_string(row.get("meta:_yoast_wpseo_canonical")),
                images=[main_image],
                gallery_images=gallery_images,
                attributes=attributes,
                sale_tag=self._clean_string(row.get("sale_tag")),
                variations=variations
            )
            products.append(product)
        
        return products

    def read_variations(self) -> List[Variation]:
        """Read and parse the Variations worksheet."""
        df = self.workbook.parse("Variations")
        variations = []
        
        for _, row in df.iterrows():
            # Parse images
            images = []
            if pd.notna(row.get("images")):
                images.append(
                    ProductImage(
                        id=self._clean_string(row.get("ID", "")),
                        product_sku=self._clean_sku(row["sku"]),
                        image_url=self._clean_string(row["images"]),
                        alt_text=self._clean_string(row.get("image_alt")),
                        title=self._clean_string(row.get("image_titles")),
                        is_main=True
                    )
                )
            
            # Parse attributes
            attributes = {}
            for col in df.columns:
                if col.startswith("attribute:"):
                    attr_name = col.split(":")[1]
                    attr_value = self._clean_string(row[col])
                    if attr_value:
                        attributes[attr_name] = attr_value
            
            # Create Variation model
            variation = Variation(
                id=self._clean_string(row["ID"]),
                post_title=self._clean_string(row.get("post_title")),
                post_status=self._clean_string(row["post_status"]),
                sku=self._clean_sku(row["sku"]),
                parent_sku=self._clean_sku(row["parent_sku"]),
                regular_price=float(row["regular_price"]),
                sale_price=float(row["sale_price"]) if pd.notna(row["sale_price"]) else None,
                manage_stock=self._clean_string(row["manage_stock"]),
                stock_quantity=self._clean_int(row["stock_quantity"]),
                stock_status=self._clean_string(row["stock_status"]),
                images=images,
                attributes=attributes
            )
            variations.append(variation)
        
        return variations

    def read_categories(self) -> List[Category]:
        """Read and parse the Categories worksheet."""
        df = self.workbook.parse("Categories")
        categories = []
        
        for _, row in df.iterrows():
            category = Category(
                id=self._clean_string(row["ID"]),
                name=self._clean_string(row["name"]),
                parent_category=self._clean_string(row.get("parent_category"))
            )
            categories.append(category)
        
        return categories

    def read_attributes(self) -> List[Attribute]:
        """Read and parse the Attributes worksheet."""
        df = self.workbook.parse("Attributes")
        attributes = []
        
        for _, row in df.iterrows():
            attr_values = self._clean_attribute_value(row["values"])
            attribute = Attribute(
                id=self._clean_string(row["ID"]),
                name=self._clean_string(row["name"]),
                values=attr_values
            )
            attributes.append(attribute)
        
        return attributes

    def read_images(self) -> List[ProductImage]:
        """Read and parse the Images worksheet."""
        df = self.workbook.parse("Images")
        images = []
        
        for _, row in df.iterrows():
            image = ProductImage(
                id=self._clean_string(row["ID"]),
                product_sku=self._clean_sku(row["product_sku"]),
                image_url=self._clean_string(row["image_url"]),
                alt_text=self._clean_string(row.get("alt_text")),
                title=self._clean_string(row.get("title")),
                is_main=bool(row.get("is_main", False))
            )
            images.append(image)
        
        return images