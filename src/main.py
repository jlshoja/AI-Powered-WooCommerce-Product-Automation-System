#!/usr/bin/env python3
"""
Entry point for the AI-Powered WooCommerce Product Automation System.
"""

import yaml
from pathlib import Path
from src.excel_parser.reader import ExcelReader
from src.validator.validator import Validator
from src.woocommerce.client import WooCommerceClient
from src.image_manager.manager import ImageManager
from src.ai.manager import AIManager
from src.automation.importer import BatchImporter
from src.utils.logger import Logger

def load_settings():
    """Load settings from config/settings.yaml."""
    with open(Path("../config/settings.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """Main function to run the automation system."""
    logger = Logger("main").get_logger()
    logger.info("Starting WooCommerce Product Automation System...")

    # Load settings
    settings = load_settings()

    # Initialize modules
    woocommerce_client = WooCommerceClient(
        api_url=settings["woocommerce"]["api_url"],
        consumer_key=settings["woocommerce"]["consumer_key"],
        consumer_secret=settings["woocommerce"]["consumer_secret"],
        timeout=settings["woocommerce"]["timeout"],
        max_retries=settings["woocommerce"]["max_retries"]
    )

    image_manager = ImageManager(woocommerce_client)

    ai_manager = None
    if settings.get("ai", {}).get("api_key"):
        ai_manager = AIManager(
            api_key=settings["ai"]["api_key"],
            model=settings["ai"]["model"]
        )

    validator = Validator(
        min_price=settings["validation"]["min_price"],
        max_price=settings["validation"]["max_price"]
    )

    batch_importer = BatchImporter(
        woocommerce_client=woocommerce_client,
        image_manager=image_manager,
        ai_manager=ai_manager,
        validator=validator
    )

    # Read products from Excel
    excel_reader = ExcelReader(Path(settings["excel"]["input_path"]))
    products = excel_reader.read_products()

    # Import products
    batch_importer.import_products(products)

    logger.info("Import process completed.")

if __name__ == "__main__":
    main()