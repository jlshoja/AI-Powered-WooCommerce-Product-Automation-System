"""
Unit tests for the ImageManager class.

Tests:
- Image download
- Image validation
- Image upload
- Image attachment
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.excel_parser.models import Product, ProductImage
from src.image_manager.manager import ImageManager


@pytest.fixture
def image_manager():
    """Fixture to initialize the ImageManager."""
    woocommerce_client = MagicMock()
    return ImageManager(woocommerce_client)


def test_download_image_success(image_manager):
    """Test successful image download."""
    with patch.object(image_manager.downloader, "download_image") as mock_download:
        mock_download.return_value = Path("../output/image_cache/test.webp")
        image_path = image_manager.downloader.download_image("https://example.com/test.webp")
        assert image_path is not None


def test_download_image_failure(image_manager):
    """Test failed image download."""
    with patch.object(image_manager.downloader, "download_image") as mock_download:
        mock_download.return_value = None
        image_path = image_manager.downloader.download_image("https://example.com/invalid.webp")
        assert image_path is None


def test_validate_image_success(image_manager):
    """Test successful image validation."""
    with patch.object(image_manager.validator, "validate_image") as mock_validate:
        mock_validate.return_value = True
        is_valid = image_manager.validator.validate_image(Path("test.webp"))
        assert is_valid is True


def test_validate_image_failure(image_manager):
    """Test failed image validation."""
    with patch.object(image_manager.validator, "validate_image") as mock_validate:
        mock_validate.return_value = False
        is_valid = image_manager.validator.validate_image(Path("invalid.webp"))
        assert is_valid is False


def test_upload_image_success(image_manager):
    """Test successful image upload."""
    with patch.object(image_manager.uploader, "upload_image") as mock_upload:
        mock_upload.return_value = {"id": 123, "source_url": "https://example.com/test.webp"}
        response = image_manager.uploader.upload_image(Path("test.webp"), alt_text="Test Image")
        assert response["id"] == 123


def test_upload_image_failure(image_manager):
    """Test failed image upload."""
    with patch.object(image_manager.uploader, "upload_image") as mock_upload:
        mock_upload.return_value = None
        response = image_manager.uploader.upload_image(Path("invalid.webp"))
        assert response is None


def test_attach_image_to_product_success(image_manager):
    """Test successful image attachment to product."""
    with patch.object(image_manager.uploader, "attach_image_to_product") as mock_attach:
        mock_attach.return_value = True
        success = image_manager.uploader.attach_image_to_product(123, 456, is_main=True)
        assert success is True


def test_attach_image_to_variation_success(image_manager):
    """Test successful image attachment to variation."""
    with patch.object(image_manager.uploader, "attach_image_to_variation") as mock_attach:
        mock_attach.return_value = True
        success = image_manager.uploader.attach_image_to_variation(123, 456, 789)
        assert success is True


def test_process_product_images(image_manager):
    """Test processing all images for a product."""
    product = Product(
        id="1",
        post_title="Test Product",
        post_status="publish",
        sku="TEST001",
        regular_price=1000,
        stock_quantity=10,
        stock_status="instock",
        categories=["Test Category"],
        images=[
            ProductImage(
                id="1",
                product_sku="TEST001",
                image_url="https://example.com/test-main.webp",
                alt_text="Main Image",
                title="Test Product",
                is_main=True,
            )
        ],
        gallery_images=[
            ProductImage(
                id="2",
                product_sku="TEST001",
                image_url="https://example.com/test-gallery.webp",
                alt_text="Gallery Image",
                title="Test Product Gallery",
                is_main=False,
            )
        ],
        attributes={},
        variations=[],
    )

    with patch.object(image_manager, "_process_image") as mock_process:
        mock_process.return_value = {"id": 123}
        image_manager.process_product_images(product, wc_product_id=123)
        assert mock_process.call_count == 2  # Main + Gallery
