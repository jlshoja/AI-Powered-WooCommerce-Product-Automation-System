"""
Logger utility for the WooCommerce Product Automation System.
"""

import logging
from pathlib import Path


class Logger:
    """Logger utility for the application."""

    def __init__(self, name: str, log_dir: Path = None):
        """Initialize the logger."""
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "output" / "logs"
        self.log_dir = log_dir.resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_dir / f"{name}.log", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self.logger
