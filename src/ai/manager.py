"""
AI Manager for the WooCommerce Product Automation System.

Orchestrates AI processing for products with provider fallback:
- Tries primary provider first
- Falls back to secondary providers on failure
- Logs all failures clearly
"""

from src.ai.client import AIClient
from src.excel_parser.models import Product
from src.utils.logger import Logger


class AIManager:
    """Orchestrates AI processing for products with provider fallback."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        rate_limit_rps: float = 3.0,
        rate_limit_burst: int = 5,
        providers: list[dict] | None = None,
        ai_client: AIClient = None,
        prompts_config: dict | None = None,
    ):
        """Initialize the AIManager.

        Args:
            api_key: API key for primary provider
            model: Model name for primary provider
            base_url: Base URL for primary provider
            rate_limit_rps: Rate limit for primary provider
            rate_limit_burst: Burst limit for primary provider
            providers: List of provider configs for fallback (from credentials Excel)
            ai_client: Pre-built AIClient instance (overrides other params)
            prompts_config: Optional dict with custom prompts from ai_prompts.yaml
        """
        self.logger = Logger(__name__).get_logger()
        self._providers = []
        self._current_provider_index = 0
        self._prompts_config = prompts_config or {}

        if ai_client is not None:
            # Pre-built client provided
            self._providers = [ai_client]
        elif providers:
            # Build clients from providers list (for fallback)
            for p in providers:
                try:
                    client = AIClient(
                        api_key=p["api_key"],
                        model=p.get("model", "gpt-4o-mini"),
                        base_url=p.get("base_url"),
                        rate_limit_rps=rate_limit_rps,
                        rate_limit_burst=rate_limit_burst,
                        prompts_config=self._prompts_config,
                    )
                    self._providers.append(client)
                except Exception as e:
                    self.logger.warning(f"Failed to init provider {p.get('name', 'unknown')}: {e}")
        elif api_key:
            # Single provider from settings
            client = AIClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                rate_limit_rps=rate_limit_rps,
                rate_limit_burst=rate_limit_burst,
                prompts_config=self._prompts_config,
            )
            self._providers = [client]
        else:
            raise ValueError("Either ai_client, api_key, or providers must be provided")

        self.ai_client = self._providers[0] if self._providers else None

    @property
    def current_provider_name(self) -> str:
        """Get name of current active provider."""
        if self._current_provider_index < len(self._providers):
            client = self._providers[self._current_provider_index]
            return f"{client.base_url or 'OpenAI'}/{client.model}"
        return "none"

    def validate_current_provider(self) -> bool:
        """Validate the current provider's API key.

        Returns:
            True if valid, False otherwise
        """
        if not self.ai_client:
            return False
        return self.ai_client.validate_api_key()

    def _try_next_provider(self) -> bool:
        """Try the next provider in the fallback list.

        Returns:
            True if a new provider was activated, False if no more providers
        """
        self._current_provider_index += 1
        if self._current_provider_index < len(self._providers):
            self.ai_client = self._providers[self._current_provider_index]
            self.logger.warning(
                f"Falling back to provider {self._current_provider_index + 1}/{len(self._providers)}: "
                f"{self.current_provider_name}"
            )
            return True
        return False

    def _call_with_fallback(self, func_name: str, *args, **kwargs):
        """Call an AI function with automatic fallback on failure.

        Args:
            func_name: Name of the method to call (e.g., 'generate_seo_title')
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result from the function, or None if all providers failed
        """
        attempts = 0
        max_attempts = len(self._providers)

        while attempts < max_attempts:
            try:
                func = getattr(self.ai_client, func_name)
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(
                    f"Provider {self.current_provider_name} failed on {func_name}: {e}"
                )
                if not self._try_next_provider():
                    self.logger.error(
                        f"All {max_attempts} AI providers failed for {func_name}. "
                        f"Giving up."
                    )
                    return None
                attempts += 1

        return None

    def process_product(self, product: Product) -> Product:
        """Process a product with AI (with automatic fallback)."""
        # Generate SEO title
        if not product.seo_title:
            product.seo_title = self._call_with_fallback(
                "generate_seo_title", product.post_title, product.attributes
            )

        # Generate SEO description
        if not product.seo_description:
            product.seo_description = self._call_with_fallback(
                "generate_seo_description", product.post_title, product.description or ""
            )

        # Generate product description
        if not product.description:
            product.description = self._call_with_fallback(
                "generate_product_description", product.post_title, product.attributes
            )

        # Generate tags
        if not product.tags:
            product.tags = self._call_with_fallback(
                "generate_tags", product.post_title, product.attributes
            )

        # Suggest categories
        if not product.categories:
            suggested = self._call_with_fallback(
                "suggest_categories", product.post_title, product.attributes
            )
            if suggested:
                product.categories = suggested

        return product
