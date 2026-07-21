"""
AI Client for the WooCommerce Product Automation System.

Integrates with AI models (e.g., OpenAI) to generate:
- SEO titles and descriptions
- Product descriptions
- Tags and keywords
- Category suggestions
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from src.utils.logger import Logger


class AIClient:
    """Client for interacting with AI models."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the AI client."""
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.logger = Logger(__name__).get_logger()

    def generate_seo_title(self, product_name: str, attributes: Dict[str, List[str]]) -> Optional[str]:
        """Generate an SEO title for a product."""
        try:
            prompt = (
                f"Generate an SEO-optimized title in Persian for a product named '{product_name}' "
                f"with the following attributes: {attributes}. "
                "The title should be concise, include relevant keywords, and be under 60 characters."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60
            )
            
            seo_title = response.choices[0].message.content.strip()
            self.logger.info(f"Generated SEO title for {product_name}: {seo_title}")
            return seo_title
        except Exception as e:
            self.logger.error(f"Failed to generate SEO title for {product_name}: {e}")
            return None

    def generate_seo_description(self, product_name: str, description: str) -> Optional[str]:
        """Generate an SEO description for a product."""
        try:
            prompt = (
                f"Generate an SEO-optimized description in Persian for a product named '{product_name}'. "
                f"Here is the current description: '{description}'. "
                "The description should be concise, include relevant keywords, and be under 160 characters."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=160
            )
            
            seo_description = response.choices[0].message.content.strip()
            self.logger.info(f"Generated SEO description for {product_name}: {seo_description}")
            return seo_description
        except Exception as e:
            self.logger.error(f"Failed to generate SEO description for {product_name}: {e}")
            return None

    def generate_product_description(self, product_name: str, attributes: Dict[str, List[str]]) -> Optional[str]:
        """Generate a product description."""
        try:
            prompt = (
                f"Generate a detailed product description in Persian for a product named '{product_name}' "
                f"with the following attributes: {attributes}. "
                "The description should highlight key features, benefits, and use cases."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            product_description = response.choices[0].message.content.strip()
            self.logger.info(f"Generated product description for {product_name}: {product_description}")
            return product_description
        except Exception as e:
            self.logger.error(f"Failed to generate product description for {product_name}: {e}")
            return None

    def generate_tags(self, product_name: str, attributes: Dict[str, List[str]]) -> Optional[List[str]]:
        """Generate tags for a product."""
        try:
            prompt = (
                f"Generate 5 relevant tags in Persian for a product named '{product_name}' "
                f"with the following attributes: {attributes}. "
                "The tags should be comma-separated."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            
            tags = [tag.strip() for tag in response.choices[0].message.content.split(",")]
            self.logger.info(f"Generated tags for {product_name}: {tags}")
            return tags
        except Exception as e:
            self.logger.error(f"Failed to generate tags for {product_name}: {e}")
            return None

    def suggest_categories(self, product_name: str, attributes: Dict[str, List[str]]) -> Optional[List[str]]:
        """Suggest categories for a product."""
        try:
            prompt = (
                f"Suggest 3 relevant categories in Persian for a product named '{product_name}' "
                f"with the following attributes: {attributes}. "
                "The categories should be comma-separated."
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            
            categories = [cat.strip() for cat in response.choices[0].message.content.split(",")]
            self.logger.info(f"Suggested categories for {product_name}: {categories}")
            return categories
        except Exception as e:
            self.logger.error(f"Failed to suggest categories for {product_name}: {e}")
            return None