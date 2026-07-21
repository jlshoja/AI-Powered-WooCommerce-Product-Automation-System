"""
AI Manager for the WooCommerce Product Automation System.

Orchestrates AI processing for products:
- SEO titles and descriptions
- Product descriptions
- Tags and keywords
- Category suggestions
"""

from src.ai.client import AIClient
from src.excel_parser.models import Product
from src.utils.logger import Logger


class AIManager:
    """Orchestrates AI processing for products."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", ai_client: AIClient = None):
        """Initialize the AIManager."""
        if ai_client is not None:
            self.ai_client = ai_client
        elif api_key is not None:
            self.ai_client = AIClient(api_key=api_key, model=model)
        else:
            raise ValueError("Either ai_client or api_key must be provided")
        self.logger = Logger(__name__).get_logger()

    def process_product(self, product: Product) -> Product:
        """Process a product with AI."""
        # Generate SEO title
        if not product.seo_title:
            product.seo_title = self.ai_client.generate_seo_title(
                product.post_title, product.attributes
            )

        # Generate SEO description (always generate if missing)
        if not product.seo_description:
            product.seo_description = self.ai_client.generate_seo_description(
                product.post_title, product.description or ""
            )

        # Generate product description
        if not product.description:
            product.description = self.ai_client.generate_product_description(
                product.post_title, product.attributes
            )

        # Generate tags
        if not product.tags:
            product.tags = self.ai_client.generate_tags(product.post_title, product.attributes)

        # Suggest categories
        if not product.categories:
            suggested_categories = self.ai_client.suggest_categories(
                product.post_title, product.attributes
            )
            if suggested_categories:
                product.categories = suggested_categories

        return product
