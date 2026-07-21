"""
Unit tests for the AIClient and AIManager classes.

Tests:
- SEO title generation
- SEO description generation
- Product description generation
- Tag generation
- Category suggestion
"""

import pytest
from unittest.mock import MagicMock, patch
from src.ai.client import AIClient
from src.ai.manager import AIManager
from src.excel_parser.models import Product


@pytest.fixture
def ai_client():
    """Fixture to initialize the AIClient."""
    return AIClient(api_key="test_api_key", model="gpt-4o-mini")


@pytest.fixture
def ai_manager(ai_client):
    """Fixture to initialize the AIManager."""
    return AIManager(ai_client)


def test_generate_seo_title_success(ai_client):
    """Test successful SEO title generation."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "عنوان سئو بهینه"
        seo_title = ai_client.generate_seo_title("کیف مردانه", {"رنگ": ["سبز"]})
        assert seo_title == "عنوان سئو بهینه"


def test_generate_seo_title_failure(ai_client):
    """Test failed SEO title generation."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.side_effect = Exception("API Error")
        seo_title = ai_client.generate_seo_title("کیف مردانه", {"رنگ": ["سبز"]})
        assert seo_title is None


def test_generate_seo_description_success(ai_client):
    """Test successful SEO description generation."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "توضیحات سئو بهینه"
        seo_description = ai_client.generate_seo_description("کیف مردانه", "توضیحات محصول")
        assert seo_description == "توضیحات سئو بهینه"


def test_generate_product_description_success(ai_client):
    """Test successful product description generation."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "توضیحات کامل محصول"
        description = ai_client.generate_product_description("کیف مردانه", {"رنگ": ["سبز"]})
        assert description == "توضیحات کامل محصول"


def test_generate_tags_success(ai_client):
    """Test successful tag generation."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "چرم, کیف مردانه, فروش ویژه"
        tags = ai_client.generate_tags("کیف مردانه", {"رنگ": ["سبز"]})
        assert tags == ["چرم", "کیف مردانه", "فروش ویژه"]


def test_suggest_categories_success(ai_client):
    """Test successful category suggestion."""
    with patch.object(ai_client.client.chat.completions, "create") as mock_create:
        mock_create.return_value.choices[0].message.content = "کیف مردانه, کیف اداری, اکسسوری"
        categories = ai_client.suggest_categories("کیف مردانه", {"رنگ": ["سبز"]})
        assert categories == ["کیف مردانه", "کیف اداری", "اکسسوری"]


def test_process_product(ai_manager):
    """Test processing a product with AI."""
    product = Product(
        id="1",
        post_title="کیف مردانه",
        post_status="publish",
        sku="TEST001",
        regular_price=1000,
        stock_quantity=10,
        stock_status="instock",
        categories=[],
        description=None,
        seo_title=None,
        seo_description=None,
        images=[],
        attributes={"رنگ": ["سبز"]},
        variations=[]
    )
    
    with patch.object(ai_manager.ai_client, "generate_seo_title", return_value="عنوان سئو بهینه"), \
         patch.object(ai_manager.ai_client, "generate_seo_description", return_value="توضیحات سئو بهینه"), \
         patch.object(ai_manager.ai_client, "generate_product_description", return_value="توضیحات کامل محصول"), \
         patch.object(ai_manager.ai_client, "generate_tags", return_value=["چرم", "کیف مردانه"]), \
         patch.object(ai_manager.ai_client, "suggest_categories", return_value=["کیف مردانه", "اکسسوری"]):
        
        processed_product = ai_manager.process_product(product)
        
        assert processed_product.seo_title == "عنوان سئو بهینه"
        assert processed_product.seo_description == "توضیحات سئو بهینه"
        assert processed_product.description == "توضیحات کامل محصول"
        assert processed_product.tags == ["چرم", "کیف مردانه"]
        assert processed_product.categories == ["کیف مردانه", "اکسسوری"]