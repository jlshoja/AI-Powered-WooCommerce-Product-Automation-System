#!/usr/bin/env python3
"""
Ad-hoc verification script for the AI-Powered WooCommerce Product Automation System.

Verifies:
1. AI Client: SEO title and description generation.
2. Batch Importer: Product import and progress tracking.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch
from ai.client import AIClient
from ai.manager import AIManager
from automation.importer import BatchImporter
from automation.tracker import ProgressTracker
from excel_parser.models import Product


def test_ai_client():
    """Test AI Client: SEO title and description generation."""
    print("Testing AI Client...")
    ai_client = AIClient(api_key="test_api_key", model="gpt-4o-mini")
    
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "عنوان سئو بهینه"
        seo_title = ai_client.generate_seo_title("کیف مردانه", {"رنگ": ["سبز"]})
        assert seo_title == "عنوان سئو بهینه", f"Expected 'عنوان سئو بهینه', got {seo_title}"
        
        mock_create.return_value.choices[0].message.content = "توضیحات سئو بهینه"
        seo_description = ai_client.generate_seo_description("کیف مردانه", "توضیحات محصول")
        assert seo_description == "توضیحات سئو بهینه", f"Expected 'توضیحات سئو بهینه', got {seo_description}"
    
    print("✅ AI Client: PASSED")


def test_ai_manager():
    """Test AI Manager: Product processing."""
    print("Testing AI Manager...")
    ai_manager = AIManager(api_key="test_api_key", model="gpt-4o-mini")
    
    product = Product(
        id="1",
        post_title="کیف مردانه",
        post_status="publish",
        sku="TEST001",
        regular_price=1000,
        stock_quantity=10,
        stock_status="instock",
        categories=[],
        description=None,
        seo_title=None,
        seo_description=None,
        images=[],
        attributes={"رنگ": ["سبز"]},
        variations=[]
    )
    
    with patch.object(ai_manager.ai_client, "generate_seo_title", return_value="عنوان سئو بهینه"), \
         patch.object(ai_manager.ai_client, "generate_seo_description", return_value="توضیحات سئو بهینه"), \
         patch.object(ai_manager.ai_client, "generate_product_description", return_value="توضیحات کامل محصول"), \
         patch.object(ai_manager.ai_client, "generate_tags", return_value=["چرم", "کیف مردانه"]), \
         patch.object(ai_manager.ai_client, "suggest_categories", return_value=["کیف مردانه", "اکسسوری"]):
        
        processed_product = ai_manager.process_product(product)
        
        assert processed_product.seo_title == "عنوان سئو بهینه", f"Expected 'عنوان سئو بهینه', got {processed_product.seo_title}"
        assert processed_product.seo_description == "توضیحات سئو بهینه", f"Expected 'توضیحات سئو بهینه', got {processed_product.seo_description}"
        assert processed_product.description == "توضیحات کامل محصول", f"Expected 'توضیحات کامل محصول', got {processed_product.description}"
        assert processed_product.tags == ["چرم", "کیف مردانه"], f"Expected ['چرم', 'کیف مردانه'], got {processed_product.tags}"
        assert processed_product.categories == ["کیف مردانه", "اکسسوری"], f"Expected ['کیف مردانه', 'اکسسوری'], got {processed_product.categories}"
    
    print("✅ AI Manager: PASSED")


def test_batch_importer():
    """Test Batch Importer: Product import and progress tracking."""
    print("Testing Batch Importer...")
    woocommerce_client = MagicMock()
    image_manager = MagicMock()
    batch_importer = BatchImporter(woocommerce_client, image_manager)
    
    product = Product(
        id="1",
        post_title="کیف مردانه",
        post_status="publish",
        sku="TEST001",
        regular_price=1000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[],
        attributes={},
        variations=[]
    )
    
    woocommerce_client.create_product.return_value = {"id": 123}
    batch_importer.import_products([product])
    
    assert len(batch_importer.tracker.imported_products) == 1, f"Expected 1 imported product, got {len(batch_importer.tracker.imported_products)}"
    assert batch_importer.tracker.imported_products[0]["sku"] == "TEST001", f"Expected 'TEST001', got {batch_importer.tracker.imported_products[0]['sku']}"
    
    print("✅ Batch Importer: PASSED")


def test_progress_tracker():
    """Test Progress Tracker: Success and failure tracking."""
    print("Testing Progress Tracker...")
    tracker = ProgressTracker()
    
    product = Product(
        id="1",
        post_title="کیف مردانه",
        post_status="publish",
        sku="TEST001",
        regular_price=1000,
        stock_quantity=10,
        stock_status="instock",
        categories=["کیف مردانه"],
        images=[],
        attributes={},
        variations=[]
    )
    
    tracker.track_success(product)
    tracker.track_failure(product, "Test error")
    
    assert len(tracker.imported_products) == 1, f"Expected 1 imported product, got {len(tracker.imported_products)}"
    assert len(tracker.failed_products) == 1, f"Expected 1 failed product, got {len(tracker.failed_products)}"
    
    # Test report generation
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
        tracker.generate_report(tmp_file.name)
        assert Path(tmp_file.name).exists(), f"Expected report at {tmp_file.name}, but file does not exist"
        Path(tmp_file.name).unlink()
    
    print("✅ Progress Tracker: PASSED")


if __name__ == "__main__":
    print("🔍 Running ad-hoc verification for AI Processing and Automation modules...")
    test_ai_client()
    test_ai_manager()
    test_batch_importer()
    test_progress_tracker()
    print("✅ All verifications PASSED!")