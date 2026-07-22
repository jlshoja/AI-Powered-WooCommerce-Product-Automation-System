#!/usr/bin/env python3
"""
Restructure Product_Master_Input.csv into Product_Master.xlsx with multiple sheets.
"""

import pandas as pd
from pathlib import Path


def extract_filename(url):
    """Extract filename from URL."""
    if pd.isna(url):
        return ""
    return url.split("/")[-1]


def main():
    input_csv = Path(__file__).parent.parent / "input" / "Product_Master.csv"
    output_xlsx = Path(__file__).parent.parent / "output" / "Product_Master.xlsx"

    # Read the updated CSV
    df = pd.read_csv(input_csv)

    # Process parent products
    products = df[df["post_type"] == "product"].copy()
    products["ID"] = [f"prod_{i}" for i in range(len(products))]

    # Add stock_status
    products["stock_status"] = "instock"

    # Add local_image and local_gallery_images columns for the reader
    # Parse from image_filename column
    def get_main_local(val):
        filenames = str(val).split("|") if pd.notna(val) else []
        return filenames[0] if filenames else ""

    def get_gallery_locals(val):
        filenames = str(val).split("|") if pd.notna(val) else []
        return "|".join(filenames[1:]) if len(filenames) > 1 else ""

    products["local_image"] = products["image_filename"].apply(get_main_local)
    products["local_gallery_images"] = products["image_filename"].apply(get_gallery_locals)

    # Keep original URLs in images/gallery_images columns
    # local_image and local_gallery_images columns already have filenames

    # Process variations
    variations = df[df["post_type"] == "product_variation"].copy()
    variations["ID"] = [f"var_{i}" for i in range(len(variations))]
    variations["stock_status"] = "instock"

    # Create categories sheet
    categories = products["categories"].str.split(">", expand=True).stack().reset_index(drop=True).unique()
    categories_df = pd.DataFrame({
        "ID": [f"cat_{i}" for i in range(len(categories))],
        "name": categories,
        "parent_category": ""
    })

    # Create attributes sheet
    attrs = {}
    for col in df.columns:
        if col.startswith("attribute:"):
            attr_name = col.split(":")[1]
            values = df[col].dropna().unique()
            attrs[attr_name] = [str(v) for v in values]

    attributes_df = pd.DataFrame([
        {"ID": f"attr_{i}", "name": k, "values": "|".join(v)}
        for i, (k, v) in enumerate(attrs.items())
    ])

    # Create images sheet
    images_list = []

    # Product main images
    for _, row in products.iterrows():
        # Parse local filenames from image_filename column (first entry = main, rest = gallery)
        local_filenames = str(row.get("image_filename", "")).split("|") if pd.notna(row.get("image_filename", "")) else []
        main_local = local_filenames[0] if local_filenames else ""
        gal_locals = local_filenames[1:] if len(local_filenames) > 1 else []

        if pd.notna(row["images"]) and row["images"] != "":
            images_list.append({
                "ID": f"img_{row['ID']}_main",
                "product_sku": row["sku"],
                "image_url": row["images"],  # Keep full URL
                "alt_text": row.get("image_alt", ""),
                "title": row.get("image_titles", ""),
                "is_main": True,
                "local_filename": main_local
            })

        # Gallery images
        if pd.notna(row["gallery_images"]) and row["gallery_images"] != "":
            gal_urls = row["gallery_images"].split("|")
            gal_alts = str(row.get("gallery_image_alt", "")).split("|") if pd.notna(row.get("gallery_image_alt", "")) else []
            gal_titles = str(row.get("image_titles", "")).split("|") if pd.notna(row.get("image_titles", "")) else []

            # Skip first gallery URL if it duplicates the main image
            main_url = row.get("images", "")
            if gal_urls and gal_urls[0] == main_url:
                gal_urls = gal_urls[1:]
                gal_alts = gal_alts[1:] if gal_alts else []
                gal_titles = gal_titles[1:] if gal_titles else []

            for i, url in enumerate(gal_urls):
                images_list.append({
                    "ID": f"img_{row['ID']}_gal_{i}",
                    "product_sku": row["sku"],
                    "image_url": url,  # Keep full URL
                    "alt_text": gal_alts[i] if i < len(gal_alts) else "",
                    "title": gal_titles[i] if i < len(gal_titles) else "",
                    "is_main": False,
                    "local_filename": gal_locals[i] if i < len(gal_locals) else ""
                })

    # Variation images
    for _, row in variations.iterrows():
        if pd.notna(row["images"]) and row["images"] != "":
            images_list.append({
                "ID": f"img_{row['ID']}_main",
                "product_sku": row["sku"],
                "image_url": row["images"],  # Keep full URL
                "alt_text": row.get("image_alt", ""),
                "title": row.get("image_titles", ""),
                "is_main": True,
                "local_filename": ""  # Variations don't have local_image column in CSV yet
            })

    images_df = pd.DataFrame(images_list)

    # Write Excel
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        products.to_excel(writer, sheet_name="Products", index=False)
        variations.to_excel(writer, sheet_name="Variations", index=False)
        categories_df.to_excel(writer, sheet_name="Categories", index=False)
        attributes_df.to_excel(writer, sheet_name="Attributes", index=False)
        pd.DataFrame(images_list).to_excel(writer, sheet_name="Images", index=False)

    print("Product_Master.xlsx created successfully!")
    print(f"Products: {len(products)}")
    print(f"Variations: {len(variations)}")
    print(f"Categories: {len(categories_df)}")
    print(f"Attributes: {len(attributes_df)}")
    print(f"Images: {len(images_list)}")


if __name__ == "__main__":
    main()