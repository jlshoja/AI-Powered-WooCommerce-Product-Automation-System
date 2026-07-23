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
    """Load settings from config/settings.yaml and environment variables.

    Priority order (highest to lowest):
    1. Environment variables
    2. External credentials Excel file (providers.xlsx) - AI only
    3. config/settings.yaml

    Note: WooCommerce credentials are ALWAYS from settings.yaml only.
    """
    load_dotenv()

    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(config_path, encoding="utf-8") as f:
        raw_content = f.read()

    # Substitute ${VAR:-default} placeholders with environment variables
    import re
    def replace_placeholder(match):
        var_expr = match.group(1)
        if ":-" in var_expr:
            var_name, default = var_expr.split(":-", 1)
            return os.getenv(var_name, default)
        else:
            return os.getenv(var_expr, match.group(0))

    substituted = re.sub(r'\$\{([^}]+)\}', replace_placeholder, raw_content)
    settings = yaml.safe_load(substituted)

    # Load AI credentials from external Excel file (if exists)
    creds_manager = CredentialsManager(credentials_path)
    primary_provider = creds_manager.get_primary_provider()

    if primary_provider:
        settings.setdefault("ai", {})["api_key"] = primary_provider["api_key"]
        if primary_provider.get("model"):
            settings["ai"]["model"] = primary_provider["model"]
        if primary_provider.get("base_url"):
            settings["ai"]["base_url"] = primary_provider["base_url"]

    # Store all providers for fallback
    all_providers = creds_manager.get_all_providers()
    if all_providers:
        settings["ai"]["_providers"] = all_providers

    # Override with environment variables (highest priority)
    if os.getenv("WOOCOMMERCE_API_URL"):
        settings.setdefault("woocommerce", {})["api_url"] = os.getenv("WOOCOMMERCE_API_URL")
    if os.getenv("WOOCOMMERCE_CONSUMER_KEY"):
        settings.setdefault("woocommerce", {})["consumer_key"] = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
    if os.getenv("WOOCOMMERCE_CONSUMER_SECRET"):
        settings.setdefault("woocommerce", {})["consumer_secret"] = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
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

    # Convert numeric settings
    wc = settings.setdefault("woocommerce", {})
    wc["rate_limit_rps"] = float(wc.get("rate_limit_rps", 1.0))
    wc["rate_burst"] = int(wc.get("rate_burst", 2))
    ai = settings.setdefault("ai", {})
    ai["rate_limit_rps"] = float(ai.get("rate_limit_rps", 3.0))
    ai["rate_burst"] = int(ai.get("rate_burst", 5))

    return settings


def ensure_excel_exists(settings, logger):
    """Auto-restructure CSV to XLSX if needed.

    If input is a CSV file, runs the restructure script to create XLSX.
    If input is already XLSX, does nothing.
    """
    input_path = Path(settings["excel"]["input_path"])
    # Resolve relative paths against project root
    if not input_path.is_absolute():
        input_path = (Path(__file__).parent.parent / input_path).resolve()

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

        # Determine output path (resolve relative to project root)
        output_dir = Path(settings["excel"].get("output_dir", "../output"))
        output_dir = (Path(__file__).parent.parent / output_dir).resolve()
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

    # Load existing WC attributes and terms at startup
    # This enables reuse of global attributes (e.g. color swatches)
    woocommerce_client.load_attributes()

    image_manager = ImageManager(
        woocommerce_client,
        local_images_dir=(Path(__file__).parent.parent / settings["image"].get("local_folder", "../input/images")).resolve(),
        wp_user=settings.get("wordpress", {}).get("user", ""),
        wp_app_password=settings.get("wordpress", {}).get("app_password", ""),
        attachment_mode=settings["image"].get("attachment_mode", "gallery"),
        media_cache_path=(Path(__file__).parent.parent / "output" / "media_cache.json").resolve(),
    )

    ai_manager = None
    ai_settings = settings.get("ai", {})
    providers_list = ai_settings.get("_providers")  # From credentials Excel

    # Build providers list for AIManager
    ai_providers = []
    if providers_list:
        # From external Excel file (multiple providers for fallback)
        ai_providers = providers_list
    elif ai_settings.get("api_key") and ai_settings["api_key"] != "your_api_key_here":
        # From settings.yaml / env vars (single provider)
        ai_providers = [{
            "name": "primary",
            "api_key": ai_settings["api_key"],
            "model": ai_settings.get("model", "gpt-4o-mini"),
            "base_url": ai_settings.get("base_url"),
        }]

    if ai_providers:
        ai_manager = AIManager(
            providers=ai_providers,
            rate_limit_rps=ai_settings.get("rate_limit_rps", 3.0),
            rate_limit_burst=ai_settings.get("rate_burst", 5),
        )
        # Validate API key before starting
        if ai_manager.validate_current_provider():
            logger.info(
                f"AI enabled: provider={ai_manager.current_provider_name}, "
                f"fallback_providers={len(ai_providers) - 1}"
            )
        else:
            logger.warning("AI API key validation failed. AI will be disabled.")
            ai_manager = None
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
