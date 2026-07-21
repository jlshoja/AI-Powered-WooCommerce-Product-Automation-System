# Changelog

All notable changes to this project will be documented in this format.

## [Unreleased]

### Fixed
- **Critical Security & Runtime Fixes**
- Moved all secrets from `config/settings.yaml` to `.env` (gitignored)
- Added `.env.example` template for safe onboarding
- Fixed `AIManager` constructor mismatch (`main.py` passed `api_key`/`model`, but `__init__` expected `AIClient`)
- Implemented idempotent `upsert_product` via SKU lookup (`get_product_by_sku` → update or create)
- Added compensating transactions: `delete_product`, `delete_variation`, `rollback_product_creation`
- Removed duplicate `ProductMapper` class (`src/woocommerce/mapper.py`)

### Added
- `pyproject.toml` with ruff, mypy, pytest, pre-commit, coverage config
- `TESTING_STRATEGY.md`, `SECURITY.md`, `DEVELOPMENT_GUIDE.md`, `DEPLOYMENT_GUIDE.md`
- Portable test paths (relative `Path(__file__).parent.parent` instead of absolute)

### Changed
- `main.py`: Loads `.env` via `python-dotenv`, resolves paths relative to file
- `BatchImporter`: Uses `upsert_product` instead of `create_product`
- `WooCommerceClient`: Returns variation IDs for rollback tracking

### Tests
- Updated `test_ai.py` fixture for new `AIManager(api_key, model)` signature
- Updated `test_automation.py` mocks to use `upsert_product`
- Fixed `test_excel_parser/test_reader.py` portable path

## [0.1.0] - 2026-07-21

### Added
- Initial modular architecture: Excel Parser, Validator, WC Client, Image Manager, AI, Automation, Reporter
- Pydantic models for Product, Variation, Category, Attribute, Image
- ExcelReader with multi-sheet parsing (Products, Variations, Categories, Attributes, Images)
- Validation rules: required fields, SKU uniqueness, price range, stock, images, categories, attributes
- WooCommerceClient with retry logic, product/variation CRUD
- ImageManager: download → validate → upload → attach workflow
- AIClient (OpenAI): SEO title/description, product description, tags, categories
- AIManager: orchestrates AI processing per product
- BatchImporter: batched imports with progress tracking
- Scheduler: time-based and incremental imports
- Reporter: Excel validation/import reports
- Unit tests for all 6 modules (pytest + mocks)
- Documentation: Architecture, Excel Dictionary, WC API, Audit Report

---

## Release Format

```
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes
```