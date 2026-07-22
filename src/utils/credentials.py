"""
Credentials Manager for the WooCommerce Product Automation System.

Reads API credentials from an external Excel file for security.
The Excel file should be located OUTSIDE the project root.
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import Logger


class CredentialsManager:
    """Reads API credentials from an external Excel file."""

    def __init__(self, credentials_path: Path | None = None):
        """Initialize the CredentialsManager.

        Args:
            credentials_path: Path to the credentials Excel file.
                             If None, tries default locations.
        """
        self.logger = Logger(__name__).get_logger()
        self.credentials_path = credentials_path
        self._credentials = None

    def _find_credentials_file(self) -> Path | None:
        """Find the credentials Excel file in common locations."""
        # Check if explicitly provided
        if self.credentials_path and self.credentials_path.exists():
            return self.credentials_path

        # Try common locations (outside project root)
        possible_paths = [
            # Same directory as project parent
            Path(__file__).parent.parent.parent.parent / "providers.xlsx",
            # User's home directory
            Path.home() / "providers.xlsx",
            # Desktop
            Path.home() / "Desktop" / "providers.xlsx",
            # Documents
            Path.home() / "Documents" / "providers.xlsx",
        ]

        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Found credentials file: {path}")
                return path

        return None

    def load_credentials(self) -> dict[str, dict[str, str]]:
        """Load credentials from Excel file.

        Expected Excel format:
        | provider    | api_key           | model        | base_url                    |
        |-------------|-------------------|--------------|-----------------------------|
        | openai      | sk-xxx...         | gpt-4o-mini  | https://api.openai.com/v1   |
        | openrouter  | sk-or-xxx...      | gpt-4o-mini  | https://openrouter.ai/api/v1|
        | woocommerce | ck_xxx...         |              | https://your-store.com/...  |

        For WooCommerce, also expects columns:
        | consumer_key | consumer_secret |

        Returns:
            Dictionary mapping provider name to its credentials
        """
        if self._credentials is not None:
            return self._credentials

        credentials_file = self._find_credentials_file()
        if not credentials_file:
            self.logger.info("No credentials file found. Using settings.yaml/.env")
            return {}

        try:
            self.logger.info(f"Loading credentials from: {credentials_file}")

            # Read all sheets
            excel = pd.ExcelFile(credentials_file)
            credentials = {}

            # Read AI providers sheet
            if "ai" in excel.sheet_names:
                df_ai = excel.parse("ai")
                for _, row in df_ai.iterrows():
                    provider = str(row.get("provider", "")).strip().lower()
                    if provider:
                        credentials[f"ai_{provider}"] = {
                            "api_key": str(row.get("api_key", "")),
                            "model": str(row.get("model", "")),
                            "base_url": str(row.get("base_url", "")),
                        }

            # Read WooCommerce sheet
            if "woocommerce" in excel.sheet_names:
                df_wc = excel.parse("woocommerce")
                for _, row in df_wc.iterrows():
                    credentials["woocommerce"] = {
                        "api_url": str(row.get("api_url", "")),
                        "consumer_key": str(row.get("consumer_key", "")),
                        "consumer_secret": str(row.get("consumer_secret", "")),
                    }

            # If no named sheets, try reading as flat structure
            if not credentials:
                df = excel.parse(0)  # Read first sheet
                for _, row in df.iterrows():
                    provider = str(row.get("provider", "")).strip().lower()
                    if provider.startswith("ai_") or provider in ("openai", "openrouter", "mimo"):
                        credentials[f"ai_{provider.replace('ai_', '')}"] = {
                            "api_key": str(row.get("api_key", "")),
                            "model": str(row.get("model", "")),
                            "base_url": str(row.get("base_url", "")),
                        }
                    elif provider == "woocommerce":
                        credentials["woocommerce"] = {
                            "api_url": str(row.get("api_url", "")),
                            "consumer_key": str(row.get("consumer_key", "")),
                            "consumer_secret": str(row.get("consumer_secret", "")),
                        }

            self._credentials = credentials
            self.logger.info(f"Loaded credentials for: {list(credentials.keys())}")
            return credentials

        except Exception as e:
            self.logger.error(f"Failed to load credentials from {credentials_file}: {e}")
            return {}

    def get_ai_credentials(self, provider: str = "openai") -> dict[str, str] | None:
        """Get AI provider credentials.

        Args:
            provider: Provider name (openai, openrouter, mimo, etc.)

        Returns:
            Dictionary with api_key, model, base_url or None
        """
        credentials = self.load_credentials()
        key = f"ai_{provider.lower()}"
        return credentials.get(key)

    def get_woocommerce_credentials(self) -> dict[str, str] | None:
        """Get WooCommerce credentials.

        Returns:
            Dictionary with api_url, consumer_key, consumer_secret or None
        """
        credentials = self.load_credentials()
        return credentials.get("woocommerce")
