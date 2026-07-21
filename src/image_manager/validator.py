"""
Image Validator for the WooCommerce Product Automation System.

Validates image files (format, size, etc.).
"""

from pathlib import Path
from typing import Optional
from PIL import Image
from src.utils.logger import Logger


class ImageValidator:
    """Validates image files."""

    def __init__(self, max_size_mb: int = 2, allowed_formats: list = None):
        """Initialize the ImageValidator."""
        self.max_size_mb = max_size_mb
        self.allowed_formats = allowed_formats or ["JPEG", "PNG", "WEBP"]
        self.logger = Logger(__name__).get_logger()

    def validate_image(self, image_path: Path) -> bool:
        """Validate an image file."""
        try:
            # Check file size
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                self.logger.error(f"Image {image_path.name} exceeds max size: {file_size_mb:.2f} MB")
                return False
            
            # Check file format
            with Image.open(image_path) as img:
                if img.format not in self.allowed_formats:
                    self.logger.error(f"Image {image_path.name} has invalid format: {img.format}")
                    return False
            
            self.logger.info(f"Image validated: {image_path.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to validate image {image_path.name}: {e}")
            return False