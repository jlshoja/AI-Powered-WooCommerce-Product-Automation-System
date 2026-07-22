#!/usr/bin/env python3
"""
Entry point for the AI-Powered WooCommerce Product Automation System.
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.ai.manager import AIManager
from src.automation.importer import BatchImporter
from src.excel_parser.reader import ExcelReader
from src.image_manager.manager import ImageManager
from src.utils.credentials import CredentialsManager
from src.utils.logger import Logger
from src.validator.validator import Validator
from src.woocommerce.client import WooCommerceClient


def load_settings(credentials_path: Path | None = None):
    """Load settings from config/settings.yaml, environment variables, and credentials Excel.

    Priority order (highest to lowest):
    1. Environment variables
    2. External credentials Excel file (providers.xlsx)
    3. config/settings.yaml
    """
    load_dotenv()

    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    # Load credentials from external Excel file (if exists)
    creds_manager = CredentialsManager(credentials_path)
    external_creds = creds_manager.load_credentials()

    # Apply external credentials (lower priority than env vars)
    if external_creds:
        # WooCommerce credentials
        wc_creds = external_creds.get("woocommerce")
        if wc_creds:
            if wc_creds.get("api_url"):
                settings.setdefault("woocommerce", {})["api_url"] = wc_creds["api_url"]
            if wc_creds.get("consumer_key"):
                settings.setdefault("woocommerce", {})["consumer_key"] = wc_creds["consumer_key"]
            if wc_creds.get("consumer_secret"):
                settings.setdefault("woocommerce", {})["consumer_secret"] = wc_creds["consumer_secret"]

        # AI credentials (try openai first, then fallback to others)
        for provider in ["openai", "openrouter", "mimo", "minimax"]:
            ai_creds = external_creds.get(f"ai_{provider}")
            if ai_creds and ai_creds.get("api_key"):
                settings.setdefault("ai", {})["api_key"] = ai_creds["api_key"]
                if ai_creds.get("model"):
                    settings["ai"]["model"] = ai_creds["model"]
                if ai_creds.get("base_url"):
                    settings["ai"]["base_url"] = ai_creds["base_url"]
                break  # Use first valid provider found

    # Override with environment variables (highest priority)
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
    if os.getenv("OPENAI_BASE_URL"):
        settings.setdefault("ai", {})["base_url"] = os.getenv("OPENAI_BASE_URL")
    if os.getenv("EXCEL_INPUT_PATH"):
        settings.setdefault("excel", {})["input_path"] = os.getenv("EXCEL_INPUT_PATH")
    if os.getenv("OUTPUT_DIR"):
        settings.setdefault("excel", {})["output_dir"] = os.getenv("OUTPUT_DIR")

    return settings


def ensure_excel_exists(settings, logger):
    """Auto-restructure CSV to XLSX if needed.

    If input is a CSV file, runs the restructure script to create XLSX.
    If input is already XLSX, does nothing.
    """
    input_path = Path(settings["excel"]["input_path"])

    if input_path.suffix.lower() == ".xlsx":
        if input_path.exists():
            logger.info(f"Excel file found: {input_path}")
            return input_path
        else:
            logger.error(f"Excel file not found: {input_path}")
            return None

    if input_path.suffix.lower() == ".csv":
        if not input_path.exists():
            logger.error(f"CSV input file not found: {input_path}")
            return None

        # Determine output path
        output_dir = Path(settings["excel"].get("output_dir", "../output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_xlsx = output_dir / "Product_Master.xlsx"

        logger.info(f"Converting CSV to XLSX: {input_path} -> {output_xlsx}")
        try:
            from scripts.restructure_excel import main as restructure_main

            # Override the paths in the restructure script
            import scripts.restructure_excel as restructure_module

            restructure_module.INPUT_PATH = input_path
            restructure_module.OUTPUT_PATH = output_xlsx
            restructure_main()
            logger.info("CSV to XLSX conversion completed successfully")
        except Exception as e:
            logger.error(f"Failed to convert CSV to XLSX: {e}")
            logger.info("Please run manually: python scripts/restructure_excel.py")
            return None

        return output_xlsx

    logger.error(f"Unsupported input format: {input_path.suffix}")
    return None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-Powered WooCommerce Product Automation System"
    )
    parser.add_argument(
        "--test-sku",
        type=str,
        default=None,
        help="Import only a single product by SKU (for testing before full batch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and process products without actually uploading to WooCommerce",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of products per batch (default: 10)",
    )
    parser.add_argument(
        "--credentials",
        type=str,
        default=None,
        help="Path to external credentials Excel file (providers.xlsx)",
    )
    return parser.parse_args()


def main():
    """Main function to run the automation system."""
    logger = Logger("main").get_logger()
    logger.info("Starting WooCommerce Product Automation System...")

    args = parse_args()

    # Load settings with optional external credentials file
    credentials_path = Path(args.credentials) if args.credentials else None
    settings = load_settings(credentials_path)

    # Ensure Excel file exists (auto-convert CSV if needed)
    excel_path = ensure_excel_exists(settings, logger)
    if not excel_path:
        logger.error("Cannot proceed without valid input file.")
        sys.exit(1)

    # Initialize modules
    woocommerce_client = WooCommerceClient(
        api_url=settings["woocommerce"]["api_url"],
        consumer_key=settings["woocommerce"]["consumer_key"],
        consumer_secret=settings["woocommerce"]["consumer_secret"],
        timeout=settings["woocommerce"]["timeout"],
        max_retries=settings["woocommerce"]["max_retries"],
        rate_limit=settings["woocommerce"].get("rate_limit_rps", 1.0),
        rate_burst=settings["woocommerce"].get("rate_burst", 2),
    )

    image_manager = ImageManager(
        woocommerce_client,
        local_images_dir=Path(settings["image"].get("local_folder", "../input/images")),
    )

    ai_manager = None
    ai_settings = settings.get("ai", {})
    if ai_settings.get("api_key") and ai_settings["api_key"] != "your_api_key_here":
        base_url = ai_settings.get("base_url") or None
        ai_manager = AIManager(
            api_key=ai_settings["api_key"],
            model=ai_settings.get("model", "gpt-4o-mini"),
            base_url=base_url,
            rate_limit_rps=ai_settings.get("rate_limit_rps", 3.0),
            rate_limit_burst=ai_settings.get("rate_burst", 5),
        )
        logger.info(f"AI enabled: model={ai_settings.get('model')}, base_url={base_url or 'default'}")
    else:
        logger.info("AI disabled: no valid API key configured")

    validator = Validator(
        min_price=settings["validation"]["min_price"],
        max_price=settings["validation"]["max_price"],
    )

    batch_importer = BatchImporter(
        woocommerce_client=woocommerce_client,
        image_manager=image_manager,
        ai_manager=ai_manager,
        validator=validator,
    )

    # Read products from Excel
    excel_reader = ExcelReader(excel_path)
    products = excel_reader.read_products()
    logger.info(f"Loaded {len(products)} products from Excel")

    # Filter to single SKU if --test-sku is provided
    if args.test_sku:
        products = [p for p in products if p.sku == args.test_sku]
        if not products:
            logger.error(f"No product found with SKU: {args.test_sku}")
            sys.exit(1)
        logger.info(f"Test mode: importing single product with SKU={args.test_sku}")

    # Import products
    if args.dry_run:
        logger.info("DRY RUN: validating products without uploading...")
        report = validator.validate_products(products)
        if report.errors:
            logger.warning(f"Found {len(report.errors)} validation errors")
            for error in report.errors[:10]:
                logger.warning(f"  - {error}")
        else:
            logger.info("All products passed validation")
        logger.info(f"DRY RUN complete: {len(products)} products validated")
    else:
        batch_importer.import_products(products, batch_size=args.batch_size)

    logger.info("Import process completed.")


if __name__ == "__main__":
    main()
