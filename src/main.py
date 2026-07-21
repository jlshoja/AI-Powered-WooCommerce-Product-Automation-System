#!/usr/bin/env python3
"""
Entry point for the AI-Powered WooCommerce Product Automation System.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.ai.manager import AIManager
from src.automation.importer import BatchImporter
from src.excel_parser.reader import ExcelReader
from src.image_manager.manager import ImageManager
from src.utils.logger import Logger
from src.validator.validator import Validator
from src.woocommerce.client import WooCommerceClient


def load_settings():
    """Load settings from config/settings.yaml and environment variables."""
    # Load .env file
    load_dotenv()

    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    # Override with environment variables if present
    if os.getenv("WOOCOMMERCE_API_URL"):
        settings.setdefault("woocommerce", {})["api_url"] = os.getenv("WOOCOMMERCE_API_URL")
    if os.getenv("WOOCOMMERCE_CONSUMER_KEY"):
        settings.setdefault("woocommerce", {})["consumer_key"] = os.getenv(
            "WOOCOMMERCE_CONSUMER_KEY"
        )
    if os.getenv("WOOCOMMERCE_CONSUMER_SECRET"):
        settings.setdefault("woocommerce", {})["consumer_secret"] = os.getenv(
            "WOOCOMMERCE_CONSUMER_SECRET"
        )
    if os.getenv("OPENAI_API_KEY"):
        settings.setdefault("ai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("OPENAI_MODEL"):
        settings.setdefault("ai", {})["model"] = os.getenv("OPENAI_MODEL")
    if os.getenv("EXCEL_INPUT_PATH"):
        settings.setdefault("excel", {})["input_path"] = os.getenv("EXCEL_INPUT_PATH")
    if os.getenv("OUTPUT_DIR"):
        settings.setdefault("excel", {})["output_dir"] = os.getenv("OUTPUT_DIR")

    return settings


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
        max_retries=settings["woocommerce"]["max_retries"],
    )

    image_manager = ImageManager(
        woocommerce_client,
        local_images_dir=Path(settings["image"].get("local_folder", "../input/images")),
    )

    ai_manager = None
    ai_settings = settings.get("ai", {})
    if ai_settings.get("api_key"):
        ai_manager = AIManager(
            api_key=ai_settings["api_key"], model=ai_settings.get("model", "gpt-4o-mini")
        )

    validator = Validator(
        min_price=settings["validation"]["min_price"], max_price=settings["validation"]["max_price"]
    )

    batch_importer = BatchImporter(
        woocommerce_client=woocommerce_client,
        image_manager=image_manager,
        ai_manager=ai_manager,
        validator=validator,
    )

    # Read products from Excel
    excel_reader = ExcelReader(Path(settings["excel"]["input_path"]))
    products = excel_reader.read_products()

    # Import products
    batch_importer.import_products(products)

    logger.info("Import process completed.")


if __name__ == "__main__":
    main()
