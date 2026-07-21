#!/usr/bin/env python3
"""
Excel Restructuring Script for WooCommerce Product Automation System.

Converts the input CSV into an Excel workbook with 6 worksheets:
1. Products (parent products)
2. Variations (child products)
3. Categories (hierarchical list)
4. Attributes (attribute names + values)
5. Suppliers (supplier information)
6. Images (image metadata)

Adds:
- stock_status (instock/outofstock)
- Unique IDs for all records
- Data validation for post_status, manage_stock, stock_status
- Relative image paths with current system date (e.g., /uploads/2026/07/...)
"""

import pandas as pd
import re
import uuid
from pathlib import Path
from datetime import datetime

# Constants
INPUT_PATH = Path("../input/Product_Master_Input.csv")
OUTPUT_PATH = Path("../output/Product_Master.xlsx")

# Data Validation Rules
VALID_POST_STATUS = ["publish", "draft"]
VALID_MANAGE_STOCK = ["yes", "no"]
VALID_STOCK_STATUS = ["instock", "outofstock"]


def extract_relative_path(url: str) -> str:
    """Extract relative path from a hardcoded URL and replace year/month with current system date."""
    if not url:
        return ""
    # Extract the filename (e.g., men-bag-2106-main.webp)
    filename = url.split("/")[-1]
    # Get current year/month (e.g., 2026/07)
    current_date = datetime.now()
    year_month = f"{current_date.year}/{current_date.month:02d}"
    # Construct new relative path (e.g., /uploads/2026/07/men-bag-2106-main.webp)
    return f"/uploads/{year_month}/{filename}"


def split_categories(category_str: str) -> list:
    """Split hierarchical categories into a list."""
    if not category_str:
        return []
    return [cat.strip() for cat in category_str.split(">")]


def process_products(df: pd.DataFrame) -> pd.DataFrame:
    """Process parent products (post_type = product)."""
    products = df[df["post_type"] == "product"].copy()
    
    # Add unique ID
    products["ID"] = [str(uuid.uuid4()) for _ in range(len(products))]
    
    # Add stock_status (default: instock)
    products["stock_status"] = "instock"
    
    # Replace hardcoded URLs with relative paths (dynamic year/month)
    products["images"] = products["images"].apply(extract_relative_path)
    products["gallery_images"] = products["gallery_images"].apply(
        lambda x: "|".join([extract_relative_path(url) for url in x.split("|")]) if pd.notna(x) else ""
    )
    
    # Define base columns (excluding dynamic attributes)
    base_columns = [
        "ID", "post_title", "post_status", "sku", "regular_price", "sale_price",
        "manage_stock", "stock_quantity", "stock_status", "categories", "description",
        "short_description", "meta:_yoast_wpseo_title", "meta:_yoast_wpseo_metadesc",
        "meta:_yoast_wpseo_focuskw", "meta:_yoast_wpseo_canonical", "images",
        "gallery_images", "gallery_image_alt", "image_filename", "image_titles",
        "image_alt", "sale_tag"
    ]
    
    # Filter base_columns to only those present in the DataFrame
    base_columns = [col for col in base_columns if col in products.columns]
    
    # Add dynamic attribute columns
    attribute_columns = [col for col in df.columns if col.startswith("attribute:") or col.startswith("attribute_name:")]
    columns = base_columns + attribute_columns
    
    return products[columns]


def process_variations(df: pd.DataFrame) -> pd.DataFrame:
    """Process product variations (post_type = product_variation)."""
    variations = df[df["post_type"] == "product_variation"].copy()
    
    # Add unique ID
    variations["ID"] = [str(uuid.uuid4()) for _ in range(len(variations))]
    
    # Add stock_status (default: instock)
    variations["stock_status"] = "instock"
    
    # Replace hardcoded URLs with relative paths (dynamic year/month)
    variations["images"] = variations["images"].apply(extract_relative_path)
    
    # Define base columns (excluding dynamic attributes)
    base_columns = [
        "ID", "post_title", "post_status", "sku", "parent_sku", "regular_price",
        "sale_price", "manage_stock", "stock_quantity", "stock_status", "images",
        "image_filename", "image_titles", "image_alt"
    ]
    
    # Filter base_columns to only those present in the DataFrame
    base_columns = [col for col in base_columns if col in variations.columns]
    
    # Add dynamic attribute columns
    attribute_columns = [col for col in df.columns if col.startswith("attribute:") or col.startswith("attribute_name:")]
    columns = base_columns + attribute_columns
    
    return variations[columns]


def process_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Process categories (hierarchical list)."""
    # Extract all categories from the "categories" column
    categories = set()
    for category_str in df["categories"].dropna():
        categories.update(split_categories(category_str))
    
    # Create a DataFrame with unique categories
    categories_df = pd.DataFrame({
        "ID": [str(uuid.uuid4()) for _ in range(len(categories))],
        "name": list(categories),
        "parent_category": ""
    })
    
    # Infer parent-child relationships (e.g., "کیف مردانه" is parent of "کیف روزمره مردانه")
    parent_map = {}
    for _, row in categories_df.iterrows():
        for _, other_row in categories_df.iterrows():
            if row["name"] != other_row["name"] and other_row["name"].startswith(row["name"] + ">"):
                parent_map[other_row["name"]] = row["name"]
    
    categories_df["parent_category"] = categories_df["name"].map(parent_map)
    return categories_df


def process_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Process attributes (attribute names + values)."""
    attributes = {}
    
    # Extract attribute names and values
    for col in df.columns:
        if col.startswith("attribute:"):
            attr_name = col.split(":")[1]
            attr_values = set()
            for values in df[col].dropna():
                attr_values.update([v.strip() for v in values.split("|")])
            attributes[attr_name] = list(attr_values)
        elif col.startswith("attribute_name:"):
            attr_name = col.split(":")[1]
            if attr_name not in attributes:
                attributes[attr_name] = []
    
    # Create DataFrame
    rows = []
    for attr_name, values in attributes.items():
        rows.append({
            "ID": str(uuid.uuid4()),
            "name": attr_name,
            "values": "|".join(values) if values else ""
        })
    
    return pd.DataFrame(rows)


def process_suppliers() -> pd.DataFrame:
    """Process suppliers (placeholder, as supplier data is missing)."""
    return pd.DataFrame({
        "ID": [str(uuid.uuid4())],
        "name": ["Default Supplier"],
        "contact": [""],
        "email": [""],
        "cost_price": [""]
    })


def process_images(df: pd.DataFrame) -> pd.DataFrame:
    """Process images (image metadata)."""
    images = []
    
    # Extract images from parent products
    for _, row in df[df["post_type"] == "product"].iterrows():
        main_image = row["images"]
        gallery_images = row["gallery_images"].split("|") if pd.notna(row["gallery_images"]) else []
        image_titles = row["image_titles"].split("|") if pd.notna(row["image_titles"]) else []
        image_alts = row["gallery_image_alt"].split("|") if pd.notna(row["gallery_image_alt"]) else []
        
        # Main image
        if main_image:
            images.append({
                "ID": str(uuid.uuid4()),
                "product_sku": row["sku"],
                "image_url": extract_relative_path(main_image),
                "alt_text": row["image_alt"] if pd.notna(row["image_alt"]) else "",
                "title": row["post_title"] if pd.notna(row["post_title"]) else "",
                "is_main": True
            })
        
        # Gallery images
        for i, img_url in enumerate(gallery_images):
            images.append({
                "ID": str(uuid.uuid4()),
                "product_sku": row["sku"],
                "image_url": extract_relative_path(img_url),
                "alt_text": image_alts[i] if i < len(image_alts) else "",
                "title": image_titles[i] if i < len(image_titles) else "",
                "is_main": False
            })
    
    # Extract images from variations
    for _, row in df[df["post_type"] == "product_variation"].iterrows():
        if pd.notna(row["images"]):
            images.append({
                "ID": str(uuid.uuid4()),
                "product_sku": row["sku"],
                "image_url": extract_relative_path(row["images"]),
                "alt_text": row["image_alt"] if pd.notna(row["image_alt"]) else "",
                "title": row["image_titles"] if pd.notna(row["image_titles"]) else "",
                "is_main": True
            })
    
    return pd.DataFrame(images)


def add_data_validation(writer: pd.ExcelWriter):
    """Add data validation to the Excel workbook."""
    workbook = writer.book
    
    # Add data validation to Products sheet
    if "Products" in writer.sheets:
        worksheet = writer.sheets["Products"]
        
        # Data validation for post_status
        post_status_rule = {
            "validate": "list",
            "source": VALID_POST_STATUS
        }
        worksheet.data_validation(
            "C2:C10000",  # post_status column (assuming column C)
            post_status_rule
        )
        
        # Data validation for manage_stock
        manage_stock_rule = {
            "validate": "list",
            "source": VALID_MANAGE_STOCK
        }
        worksheet.data_validation(
            "G2:G10000",  # manage_stock column (assuming column G)
            manage_stock_rule
        )
        
        # Data validation for stock_status
        stock_status_rule = {
            "validate": "list",
            "source": VALID_STOCK_STATUS
        }
        worksheet.data_validation(
            "I2:I10000",  # stock_status column (assuming column I)
            stock_status_rule
        )


def main():
    """Main function to restructure the CSV into an Excel workbook."""
    # Read the input CSV
    df = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)
    
    # Create Excel writer
    with pd.ExcelWriter(OUTPUT_PATH, engine="xlsxwriter") as writer:
        # Process each worksheet
        process_products(df).to_excel(writer, sheet_name="Products", index=False)
        process_variations(df).to_excel(writer, sheet_name="Variations", index=False)
        process_categories(df).to_excel(writer, sheet_name="Categories", index=False)
        process_attributes(df).to_excel(writer, sheet_name="Attributes", index=False)
        process_suppliers().to_excel(writer, sheet_name="Suppliers", index=False)
        process_images(df).to_excel(writer, sheet_name="Images", index=False)
        
        # Add data validation
        add_data_validation(writer)
    
    print(f"Excel workbook created at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()