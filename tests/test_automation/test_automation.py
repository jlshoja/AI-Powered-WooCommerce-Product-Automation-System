"""
Unit tests for the Automation module.

Tests:
- Batch import
- Scheduling
- Progress tracking
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.automation.importer import BatchImporter
from src.automation.scheduler import Scheduler
from src.automation.tracker import ProgressTracker
from src.excel_parser.models import Product


@pytest.fixture
def batch_importer():
    """Fixture to initialize the BatchImporter."""
    woocommerce_client = MagicMock()
    image_manager = MagicMock()
    return BatchImporter(woocommerce_client, image_manager)


@pytest.fixture
def scheduler(batch_importer):
    """Fixture to initialize the Scheduler."""
    return Scheduler(batch_importer)


@pytest.fixture
def progress_tracker():
    """Fixture to initialize the ProgressTracker."""
    return ProgressTracker()


def test_import_products_success(batch_importer):
    """Test successful batch import."""
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
    
    with patch.object(batch_importer.woocommerce_client, "upsert_product") as mock_create:
        mock_create.return_value = {"id": 123}
        batch_importer.import_products([product])
        
        assert len(batch_importer.tracker.imported_products) == 1
        assert batch_importer.tracker.imported_products[0]["sku"] == "TEST001"


def test_import_products_failure(batch_importer):
    """Test failed batch import."""
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
    
    with patch.object(batch_importer.woocommerce_client, "upsert_product") as mock_create:
        mock_create.return_value = None
        batch_importer.import_products([product])
        
        assert len(batch_importer.tracker.failed_products) == 1
        assert batch_importer.tracker.failed_products[0]["sku"] == "TEST001"


def test_schedule_import(scheduler):
    """Test scheduling an import."""
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
    
    with patch.object(scheduler.importer, "import_products") as mock_import:
        schedule_time = datetime.now() + timedelta(seconds=1)
        scheduler.schedule_import([product], schedule_time)
        
        mock_import.assert_called_once_with([product])


def test_incremental_import(scheduler):
    """Test incremental import."""
    product1 = Product(
        id=(datetime.now() - timedelta(days=1)).strftime("%Y%m%d%H%M%S"),
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
    
    product2 = Product(
        id=datetime.now().strftime("%Y%m%d%H%M%S"),
        post_title="کیف زنانه",
        post_status="publish",
        sku="TEST002",
        regular_price=2000,
        stock_quantity=20,
        stock_status="instock",
        categories=["کیف زنانه"],
        images=[],
        attributes={},
        variations=[]
    )
    
    with patch.object(scheduler.importer, "import_products") as mock_import:
        last_import_time = datetime.now() - timedelta(hours=1)
        scheduler.incremental_import([product1, product2], last_import_time)
        
        mock_import.assert_called_once_with([product2])


def test_progress_tracker(progress_tracker):
    """Test progress tracking."""
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
    
    progress_tracker.track_success(product)
    progress_tracker.track_failure(product, "Test error")
    
    assert len(progress_tracker.imported_products) == 1
    assert len(progress_tracker.failed_products) == 1
    
    with patch("pandas.DataFrame.to_excel") as mock_to_excel:
        progress_tracker.generate_report("test_report.xlsx")
        mock_to_excel.assert_called_once()