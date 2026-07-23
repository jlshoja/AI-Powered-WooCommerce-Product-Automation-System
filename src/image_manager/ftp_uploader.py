"""
FTP Uploader for the WooCommerce Product Automation System.

Handles bulk image uploads via FTP and registers them as WordPress media.
"""

import ftplib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.logger import Logger


class FTPUploader:
    """Upload images via FTP and register as WordPress media."""

    def __init__(
        self,
        host: str,
        port: int = 21,
        user: str = "",
        password: str = "",
        uploads_path: str = "/public_html/wp-content/uploads",
        passive_mode: bool = True,
        media_cache_path: Path | None = None,
    ):
        """Initialize FTPUploader.

        Args:
            host: FTP server hostname
            port: FTP server port
            user: FTP username
            password: FTP password
            uploads_path: Remote path to WordPress uploads directory
            passive_mode: Use passive FTP mode
            media_cache_path: Path to JSON file for caching media IDs
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.uploads_path = uploads_path
        self.passive_mode = passive_mode
        self.logger = Logger(__name__).get_logger()
        self._media_cache: dict[str, int] = {}
        self._cache_path = media_cache_path

        if self._cache_path and self._cache_path.exists():
            self._load_cache()

    def _load_cache(self) -> None:
        """Load media cache from JSON file."""
        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                self._media_cache = json.load(f)
            self.logger.info(f"Loaded media cache: {len(self._media_cache)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to load media cache: {e}")

    def _save_cache(self) -> None:
        """Save media cache to JSON file."""
        if not self._cache_path:
            return
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(self._media_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save media cache: {e}")

    def upload_batch(
        self, image_paths: list[Path], alt_texts: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Upload a batch of images via FTP.

        Args:
            image_paths: List of local image file paths
            alt_texts: Optional dict mapping filename -> alt text

        Returns:
            Dict mapping filename -> remote URL path
        """
        if not image_paths:
            return {}

        alt_texts = alt_texts or {}
        uploaded: dict[str, str] = {}
        to_upload: list[Path] = []

        # Check cache first
        for path in image_paths:
            filename = path.name
            if filename in self._media_cache:
                self.logger.info(f"Already cached: {filename}")
                continue
            to_upload.append(path)

        if not to_upload:
            self.logger.info(f"All {len(image_paths)} images already cached")
            return uploaded

        self.logger.info(f"Uploading {len(to_upload)} images via FTP...")

        # Connect to FTP
        try:
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port, timeout=30)
            ftp.login(self.user, self.password)
            if self.passive_mode:
                ftp.set_pasv(True)
            self.logger.info(f"Connected to FTP: {self.host}")

            # Ensure year/month directory exists
            now = datetime.now()
            remote_dir = f"{self.uploads_path}/{now.year}/{now.month:02d}"
            try:
                ftp.mkd(remote_dir)
            except ftplib.error_perm:
                pass  # Directory already exists

            # Upload files
            for path in to_upload:
                filename = path.name
                remote_path = f"{remote_dir}/{filename}"
                try:
                    with open(path, "rb") as f:
                        ftp.storbinary(f"STOR {remote_path}", f)
                    # Construct the URL path (relative to WordPress root)
                    url_path = f"/wp-content/uploads/{now.year}/{now.month:02d}/{filename}"
                    uploaded[filename] = url_path
                    self.logger.info(f"Uploaded: {filename} -> {remote_path}")
                except Exception as e:
                    self.logger.error(f"Failed to upload {filename}: {e}")

            ftp.quit()
            self.logger.info(f"FTP upload complete: {len(uploaded)} images")

        except Exception as e:
            self.logger.error(f"FTP connection failed: {e}")

        return uploaded

    def register_media(self, uploaded_files: dict[str, str]) -> dict[str, int]:
        """Register FTP-uploaded files as WordPress media via PHP script.

        Args:
            uploaded_files: Dict mapping filename -> remote URL path

        Returns:
            Dict mapping filename -> media ID
        """
        if not uploaded_files:
            return {}

        self.logger.info(f"Registering {len(uploaded_files)} images as WordPress media...")

        # Build the list of files to register
        files_to_register = []
        for filename, url_path in uploaded_files.items():
            # Check if already registered
            if filename in self._media_cache:
                continue
            files_to_register.append({"filename": filename, "url_path": url_path})

        if not files_to_register:
            self.logger.info("All files already registered")
            return {}

        # Write the file list to a JSON file for the PHP script
        now = datetime.now()
        list_file = Path(f"output/ftp_register_{now.strftime('%Y%m%d_%H%M%S')}.json")
        list_file.parent.mkdir(parents=True, exist_ok=True)
        with open(list_file, "w", encoding="utf-8") as f:
            json.dump(files_to_register, f, ensure_ascii=False, indent=2)

        self.logger.info(f"File list written to: {list_file}")
        self.logger.info(
            "Please run the PHP registration script on your WordPress server:"
        )
        self.logger.info(
            f"  php wp-content/uploads/ftp-register-media.php {list_file.name}"
        )

        # Try to read back results if they exist
        result_file = list_file.with_suffix(".result.json")
        if result_file.exists():
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    results = json.load(f)
                for item in results:
                    if item.get("media_id"):
                        self._media_cache[item["filename"]] = item["media_id"]
                self._save_cache()
                return {item["filename"]: item["media_id"] for item in results if item.get("media_id")}
            except Exception as e:
                self.logger.warning(f"Failed to read registration results: {e}")

        return {}

    def get_media_id(self, filename: str) -> int | None:
        """Get cached media ID for a filename."""
        return self._media_cache.get(filename)
