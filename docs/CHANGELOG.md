# Changelog

All notable changes to this project will be documented in this format.

## [0.4.0] - 2026-07-23

### Added
- **FTP Bulk Upload**: `--upload-mode ftp` for fast bulk image upload via FTP (for 1000+ images)
- **FTP Media Registration**: `scripts/ftp-register-media.php` auto-registers FTP-uploaded files as WP media
- **Crash Recovery**: Per-stage checkpoints saved to `output/import_checkpoint.json`
- **Resume Flag**: `--resume` skips fully completed products on restart
- **Retry Failed Flag**: `--retry-failed` re-runs only failed products from last import
- **Partial Reports**: `import_report.xlsx` written every 10 products (crash-safe)
- **Idempotent Variations**: `_create_variations()` checks existing SKUs before creating (no duplicates)
- **Configurable AI Prompts**: `config/ai_prompts.yaml` for customizing writing rules without code changes

### Fixed
- **Color Swatches**: Attributes now link to global WC attributes (type=color) instead of creating local ones
- **Attribute Pagination**: `load_attributes()` fetches ALL terms (not just first 100)
- **manage_stock**: Variable products have `manage_stock=false` (variations manage own stock)
- **Attribute Visibility**: Color attribute `visible=false` only, all others `visible=true`
- **Term Resolution**: Fallback search when term creation fails (term_exists error)

### Changed
- **ImageManager**: Supports both REST API and FTP upload modes
- **ProgressTracker**: Writes checkpoints after each stage, periodic report generation
- **BatchImporter**: Uses checkpoints for resume, per-product stage tracking
- **CLI**: Added `--upload-mode`, `--resume`, `--retry-failed` flags

### Configuration
- Added `ftp` section to `settings.yaml` (host, port, user, password, wp_api_url)
- Added `IMAGE_UPLOAD_MODE` to `.env` (restapi/ftp)
- Added `FTP_*` variables to `.env.example`

## [0.3.0] - 2026-07-22

### Added
- **Single Product Test**: `--test-sku` flag to test import with one SKU before full batch
- **Dry Run Mode**: `--dry-run` flag to validate products without uploading
- **AI Provider Fallback**: Multiple AI providers with automatic fallback on failure
- **External Credentials**: `--credentials` flag to read API keys from external Excel file (providers.xlsx)
- **API Key Validation**: Validates API key at startup, logs clearly if invalid
- **CSV Auto-Conversion**: CSV input auto-converts to XLSX on startup (no manual restructure)
- **Windows Menu**: `run.bat` for easy execution (Full import, Test, Dry run, etc.)
- `src/utils/credentials.py` - CredentialsManager for external API key management

### Changed
- **WooCommerce credentials**: Always from settings.yaml (not from Excel)
- **AI credentials**: Can come from settings.yaml, .env, or external providers.xlsx
- **AI Failure handling**: Logs each failure, tries next provider, disables AI if all fail
- **Image URL documentation**: Clarified that image_url is from your own website, not supplier

### Security
- `config/settings.yaml` added to .gitignore (contains API keys)
- External credentials Excel keeps secrets outside project root

## [0.2.0] - 2026-07-22

### Fixed - Critical Security & Runtime Issues
- **Rate Limiting**: Added token bucket rate limiter (`src/utils/rate_limiter.py`) for WooCommerce API (1 req/s) and OpenAI API (3 req/s) to prevent 429 errors
- **SSRF Protection**: ImageDownloader now validates URLs and blocks private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, localhost)
- **HTML Sanitization**: Added `bleach` to sanitize all AI-generated content (SEO titles, descriptions, product descriptions, tags, categories) to prevent XSS
- **Image ID Bug**: ImageManager now uses WooCommerce numeric IDs for image attachment instead of Excel IDs
- **Retry Logic**: Added exponential backoff retry for image downloads (3 attempts)

### Added
- `src/utils/rate_limiter.py` - TokenBucket and RateLimiter classes
- `docs/QUICK_START.md` - Step-by-step setup guide
- Rate limit configuration in `config/settings.yaml` (woocommerce.rate_limit_rps, ai.rate_limit_rps)
- `get_product_variations()` method in WooCommerceClient

### Changed
- `WooCommerceClient`: Added rate limiting to all API calls, handles 429 responses
- `AIClient`: Added rate limiting and HTML sanitization to all generation methods
- `ImageDownloader`: Added URL validation, private IP blocking, retry logic
- `ImageManager`: Accepts WC numeric IDs for product and variations
- `BatchImporter`: Fetches WC variation IDs before image processing
- `main.py`: Passes rate limit config from settings.yaml

### Security
- All AI output now sanitized with bleach (allowed tags: p, br, strong, em, u, b, i, ul, ol, li, span, div)
- Image URLs validated against private IP ranges before download

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
