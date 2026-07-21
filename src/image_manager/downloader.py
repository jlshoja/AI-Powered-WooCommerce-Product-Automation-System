"""
Image Downloader for the WooCommerce Product Automation System.

Downloads images from URLs and caches them locally.
"""

import requests
from pathlib import Path
from typing import Optional
from src.utils.logger import Logger


class ImageDownloader:
    """Downloads images from URLs and caches them locally."""

    def __init__(self, cache_dir: Path = Path("../output/image_cache")):
        """Initialize the ImageDownloader."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = Logger(__name__).get_logger()

    def download_image(self, image_url: str) -> Optional[Path]:
        """Download an image from a URL and cache it locally."""
        try:
            # Extract filename from URL
            filename = image_url.split("/")[-1]
            cache_path = self.cache_dir / filename
            
            # Skip if already cached
            if cache_path.exists():
                self.logger.info(f"Image already cached: {filename}")
                return cache_path
            
            # Download the image
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Image downloaded and cached: {filename}")
            return cache_path
        except Exception as e:
            self.logger.error(f"Failed to download image {image_url}: {e}")
            return None