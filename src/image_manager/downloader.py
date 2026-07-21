"""
Image Downloader for the WooCommerce Product Automation System.

Downloads images from URLs and caches them locally.
Also supports copying from a local images folder.
"""

import shutil
from pathlib import Path

import requests

from src.utils.logger import Logger


class ImageDownloader:
    """Downloads images from URLs and caches them locally."""

    def __init__(
        self,
        cache_dir: Path = Path("../output/image_cache"),
        local_images_dir: Path | None = None,
    ):
        """Initialize the ImageDownloader."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_images_dir = local_images_dir
        if self.local_images_dir:
            self.local_images_dir = Path(self.local_images_dir)
        self.logger = Logger(__name__).get_logger()

    def download_image(self, image_url: str, local_filename: str | None = None) -> Path | None:
        """Download an image from a URL and cache it locally.

        If local_filename is provided and local_images_dir is set,
        tries to copy from local folder first.
        """
        # Determine filename
        if local_filename:
            filename = local_filename
        else:
            filename = image_url.split("/")[-1]
        cache_path = self.cache_dir / filename

        # Skip if already cached
        if cache_path.exists():
            self.logger.info(f"Image already cached: {filename}")
            return cache_path

        # Try local images folder first
        if self.local_images_dir and local_filename:
            local_path = self.local_images_dir / local_filename
            if local_path.exists():
                self.logger.info(f"Copying image from local folder: {local_filename}")
                try:
                    shutil.copy2(local_path, cache_path)
                    return cache_path
                except Exception as e:
                    self.logger.warning(f"Failed to copy local image {local_filename}: {e}")

        # Fallback: download from URL
        try:
            self.logger.info(f"Downloading image from URL: {image_url}")
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(cache_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Image downloaded and cached: {filename}")
            return cache_path
        except Exception as e:
            self.logger.error(f"Failed to download image {image_url}: {e}")
            return None
