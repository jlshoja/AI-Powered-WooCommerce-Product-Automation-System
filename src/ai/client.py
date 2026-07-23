"""
AI Client for the WooCommerce Product Automation System.

Integrates with AI models (e.g., OpenAI) to generate:
- SEO titles and descriptions
- Product descriptions
- Tags and keywords
- Category suggestions
"""

import time
import threading
import bleach
from openai import OpenAI

from src.utils.logger import Logger


def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS.

    Args:
        text: Input text that may contain HTML

    Returns:
        Sanitized text with only safe HTML tags allowed
    """
    if not text:
        return text
    # Allow only safe tags for WooCommerce content
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'b', 'i', 'ul', 'ol', 'li', 'span', 'div']
    allowed_attrs = {
        '*': ['class', 'style'],
        'span': ['style'],
        'div': ['style'],
    }
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)


class TokenBucket:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate: float, burst: int):
        """Initialize token bucket.

        Args:
            rate: Tokens per second (refill rate)
            burst: Maximum tokens (bucket size)
        """
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> float:
        """Consume tokens from the bucket, blocking until available.

        Returns:
            Time waited in seconds
        """
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
                self._last_refill = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return waited

                # Calculate wait time for next token
                needed = tokens - self._tokens
                wait_time = needed / self.rate

            time.sleep(min(wait_time, 0.1))
            waited += min(wait_time, 0.1)


def sanitize_html(text: str | None) -> str | None:
    """Sanitize HTML content to prevent XSS attacks.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text with only safe HTML tags
    """
    if not text:
        return text

    # Allow only safe tags for WooCommerce content
    allowed_tags = [
        "p", "br", "strong", "em", "u", "i", "b",
        "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
        "a", "img", "span", "div", "table", "tr", "td", "th", "tbody", "thead"
    ]
    allowed_attributes = {
        "a": ["href", "title", "target", "rel"],
        "img": ["src", "alt", "title", "width", "height"],
        "span": ["style", "class"],
        "div": ["style", "class"],
        "table": ["class"],
    }
    allowed_protocols = ["http", "https", "mailto"]

    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True,
    )


class AIClient:
    """Client for interacting with AI models."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        rate_limit_rps: float = 3.0,
        rate_limit_burst: int = 5,
        prompts_config: dict | None = None,
    ):
        """Initialize the AI client.

        Args:
            api_key: API key for the AI provider
            model: Model name to use
            base_url: Optional base URL for non-OpenAI providers (e.g., OpenRouter, Mimo)
            rate_limit_rps: Requests per second limit
            rate_limit_burst: Burst capacity
            prompts_config: Optional dict with custom prompts from ai_prompts.yaml
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.logger = Logger(__name__).get_logger()
        self._rate_limiter = TokenBucket(rate_limit_rps, rate_limit_burst)
        self._is_valid = None  # Cache validation result
        self._prompts = prompts_config or {}

    def _get_prompt(self, name: str, **kwargs) -> tuple[str, int]:
        """Get prompt template and max_tokens from config, with fallback to defaults.

        Returns:
            Tuple of (formatted_prompt, max_tokens)
        """
        defaults = {
            "seo_title": {
                "prompt": "Generate an SEO-optimized title in Persian for a product named '{product_name}' with the following attributes: {attributes}. The title should be concise, include relevant keywords, and be under 60 characters.",
                "max_tokens": 60,
            },
            "seo_description": {
                "prompt": "Generate an SEO-optimized description in Persian for a product named '{product_name}'. Here is the current description: '{description}'. The description should be concise, include relevant keywords, and be under 160 characters.",
                "max_tokens": 160,
            },
            "product_description": {
                "prompt": "Generate a detailed product description in Persian for a product named '{product_name}' with the following attributes: {attributes}. The description should highlight key features, benefits, and use cases.",
                "max_tokens": 300,
            },
            "tags": {
                "prompt": "Generate 5 relevant tags in Persian for a product named '{product_name}' with the following attributes: {attributes}. The tags should be comma-separated.",
                "max_tokens": 50,
            },
            "categories": {
                "prompt": "Suggest 3 relevant categories in Persian for a product named '{product_name}' with the following attributes: {attributes}. The categories should be comma-separated.",
                "max_tokens": 50,
            },
        }

        cfg = self._prompts.get(name, defaults.get(name, {}))
        template = cfg.get("prompt", defaults.get(name, {}).get("prompt", ""))
        max_tokens = cfg.get("max_tokens", defaults.get(name, {}).get("max_tokens", 100))

        try:
            return template.format(**kwargs), max_tokens
        except KeyError as e:
            self.logger.warning(f"Missing variable {e} in prompt template for {name}")
            return template, max_tokens

    def validate_api_key(self) -> bool:
        """Validate the API key by making a minimal API call.

        Returns:
            True if API key is valid, False otherwise
        """
        if self._is_valid is not None:
            return self._is_valid

        try:
            self.logger.info(f"Validating API key for model={self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            self._is_valid = True
            self.logger.info(f"API key validated successfully for {self.base_url or 'OpenAI'}")
            return True
        except Exception as e:
            self._is_valid = False
            self.logger.warning(f"API key validation failed: {e}")
            return False

    def _rate_limited_call(self, func, *args, **kwargs):
        """Execute a function with rate limiting."""
        self._rate_limiter.consume()
        return func(*args, **kwargs)

    def generate_seo_title(self, product_name: str, attributes: dict[str, list[str]]) -> str | None:
        """Generate an SEO title for a product."""
        try:
            prompt, max_tokens = self._get_prompt("seo_title", product_name=product_name, attributes=attributes)

            response = self._rate_limited_call(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            seo_title = sanitize_html(response.choices[0].message.content.strip())
            self.logger.info(f"Generated SEO title for {product_name}: {seo_title}")
            return seo_title
        except Exception as e:
            self.logger.error(f"Failed to generate SEO title for {product_name}: {e}")
            return None

    def generate_seo_description(self, product_name: str, description: str) -> str | None:
        """Generate an SEO description for a product."""
        try:
            prompt, max_tokens = self._get_prompt("seo_description", product_name=product_name, description=description)

            response = self._rate_limited_call(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            seo_description = sanitize_html(response.choices[0].message.content.strip())
            self.logger.info(f"Generated SEO description for {product_name}: {seo_description}")
            return seo_description
        except Exception as e:
            self.logger.error(f"Failed to generate SEO description for {product_name}: {e}")
            return None

    def generate_product_description(
        self, product_name: str, attributes: dict[str, list[str]]
    ) -> str | None:
        """Generate a product description."""
        try:
            prompt, max_tokens = self._get_prompt("product_description", product_name=product_name, attributes=attributes)

            response = self._rate_limited_call(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            product_description = sanitize_html(response.choices[0].message.content.strip())
            self.logger.info(
                f"Generated product description for {product_name}: {product_description}"
            )
            return product_description
        except Exception as e:
            self.logger.error(f"Failed to generate product description for {product_name}: {e}")
            return None

    def generate_tags(
        self, product_name: str, attributes: dict[str, list[str]]
    ) -> list[str] | None:
        """Generate tags for a product."""
        try:
            prompt, max_tokens = self._get_prompt("tags", product_name=product_name, attributes=attributes)

            response = self._rate_limited_call(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            tags = [sanitize_html(tag.strip()) for tag in response.choices[0].message.content.split(",") if tag.strip()]
            self.logger.info(f"Generated tags for {product_name}: {tags}")
            return tags
        except Exception as e:
            self.logger.error(f"Failed to generate tags for {product_name}: {e}")
            return None

    def suggest_categories(
        self, product_name: str, attributes: dict[str, list[str]]
    ) -> list[str] | None:
        """Suggest categories for a product."""
        try:
            prompt, max_tokens = self._get_prompt("categories", product_name=product_name, attributes=attributes)

            response = self._rate_limited_call(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

            categories = [sanitize_html(cat.strip()) for cat in response.choices[0].message.content.split(",") if cat.strip()]
            self.logger.info(f"Suggested categories for {product_name}: {categories}")
            return categories
        except Exception as e:
            self.logger.error(f"Failed to suggest categories for {product_name}: {e}")
            return None
