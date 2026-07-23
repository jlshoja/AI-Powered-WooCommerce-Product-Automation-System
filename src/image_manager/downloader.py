"""
Image Downloader for the WooCommerce Product Automation System.

Downloads images from URLs and caches them locally.
Also supports copying from a local images folder.
Includes SSRF protection and retry logic.
"""

import ipaddress
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from src.utils.logger import Logger


class ImageDownloader:
    """Downloads images from URLs and caches them locally."""

    # Private IP ranges to block for SSRF protection
    _PRIVATE_IP_RANGES = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def __init__(
        self,
        cache_dir: Path = None,
        local_images_dir: Path | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
    ):
        """Initialize the ImageDownloader."""
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "output" / "image_cache"
        self.cache_dir = cache_dir.resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_images_dir = local_images_dir
        if self.local_images_dir:
            self.local_images_dir = Path(self.local_images_dir)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.logger = Logger(__name__).get_logger()

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if a hostname resolves to a private IP address."""
        try:
            # Try to resolve the hostname
            ip = ipaddress.ip_address(hostname)
            return any(ip in network for network in self._PRIVATE_IP_RANGES)
        except ValueError:
            # Not an IP address, could be a domain name
            # In production, you'd want to DNS resolve and check
            # For now, we just check if it's a known local domain
            local_domains = ["localhost", "127.0.0.1", "0.0.0.0"]
            return hostname.lower() in local_domains

    def _validate_url(self, url: str) -> bool:
        """Validate URL for SSRF protection."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                self.logger.warning(f"Blocked URL with invalid scheme: {url}")
                return False

            hostname = parsed.hostname or ""
            if self._is_private_ip(hostname):
                self.logger.warning(f"Blocked URL with private IP/localhost: {url}")
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Invalid URL format: {url} - {e}")
            return False

    def download_image(self, image_url: str, local_filename: str | None = None) -> Path | None:
        """Download an image from a URL and cache it locally.

        If local_filename is provided and local_images_dir is set,
        tries to copy from local folder first.
        """
        # Validate URL for SSRF protection
        if not self._validate_url(image_url):
            return None

        # Determine filename
        url_filename = image_url.split("/")[-1]
        if local_filename:
            # If local_filename has no extension, append the extension from the URL
            if "." not in local_filename.split("/")[-1]:
                url_ext = Path(url_filename).suffix
                if url_ext:
                    filename = f"{local_filename}{url_ext}"
                else:
                    filename = local_filename
            else:
                filename = local_filename
        else:
            filename = url_filename
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

        # Fallback: download from URL with retry logic
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Downloading image from URL (attempt {attempt + 1}): {image_url}")
                response = requests.get(image_url, stream=True, timeout=self.timeout)
                response.raise_for_status()

                with open(cache_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)

                self.logger.info(f"Image downloaded and cached: {filename}")
                return cache_path
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
            except Exception as e:
                self.logger.error(f"Unexpected error downloading image {image_url}: {e}")
                break

        self.logger.error(f"Failed to download image after {self.max_retries} attempts: {image_url}")
        return None
