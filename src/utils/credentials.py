"""
Credentials Manager for the WooCommerce Product Automation System.

Reads AI API credentials from an external Excel file for security.
WooCommerce credentials are ALWAYS read from settings.yaml (not Excel).
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import Logger


class CredentialsManager:
    """Reads AI API credentials from an external Excel file."""

    def __init__(self, credentials_path: Path | None = None):
        """Initialize the CredentialsManager.

        Args:
            credentials_path: Path to the credentials Excel file.
                             If None, tries default locations.
        """
        self.logger = Logger(__name__).get_logger()
        self.credentials_path = credentials_path
        self._providers = None

    def _find_credentials_file(self) -> Path | None:
        """Find the credentials Excel file in common locations."""
        if self.credentials_path and self.credentials_path.exists():
            return self.credentials_path

        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "providers.xlsx",
            Path.home() / "providers.xlsx",
            Path.home() / "Desktop" / "providers.xlsx",
            Path.home() / "Documents" / "providers.xlsx",
        ]

        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Found credentials file: {path}")
                return path

        return None

    def load_providers(self) -> list[dict[str, str]]:
        """Load AI providers from Excel file.

        Expected Excel format:
        | provider   | api_key           | model        | base_url                    |
        |------------|-------------------|--------------|-----------------------------|
        | openai     | sk-xxx...         | gpt-4o-mini  | https://api.openai.com/v1   |
        | openrouter | sk-or-xxx...      | gpt-4o-mini  | https://openrouter.ai/api/v1|
        | mimo       | sk-mimo...        | gpt-4o-mini  | https://api.mimo.com/v1     |

        Returns:
            List of provider configs, ordered by priority (first = primary)
        """
        if self._providers is not None:
            return self._providers

        credentials_file = self._find_credentials_file()
        if not credentials_file:
            self.logger.info("No credentials file found. Using settings.yaml/.env")
            return []

        try:
            self.logger.info(f"Loading AI providers from: {credentials_file}")
            excel = pd.ExcelFile(credentials_file)

            # Try "ai" sheet first, then first sheet
            sheet_name = "ai" if "ai" in excel.sheet_names else 0
            df = excel.parse(sheet_name)

            providers = []
            for _, row in df.iterrows():
                api_key = str(row.get("api_key", "")).strip()
                if not api_key or api_key == "nan":
                    continue

                provider = {
                    "name": str(row.get("provider", "unknown")).strip(),
                    "api_key": api_key,
                    "model": str(row.get("model", "gpt-4o-mini")).strip(),
                    "base_url": str(row.get("base_url", "")).strip() or None,
                }
                providers.append(provider)

            self._providers = providers
            self.logger.info(f"Loaded {len(providers)} AI providers: {[p['name'] for p in providers]}")
            return providers

        except Exception as e:
            self.logger.error(f"Failed to load credentials from {credentials_file}: {e}")
            return []

    def get_primary_provider(self) -> dict[str, str] | None:
        """Get the first (primary) AI provider."""
        providers = self.load_providers()
        return providers[0] if providers else None

    def get_all_providers(self) -> list[dict[str, str]]:
        """Get all AI providers for fallback."""
        return self.load_providers()
