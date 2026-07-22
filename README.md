# AI-Powered WooCommerce Product Automation System

## Overview
Automate WooCommerce product imports from Excel with **AI-generated SEO content**, **validation**, and **batch processing**.

## Features
- ✅ **Excel to WooCommerce**: Import products, variations, categories, and images.
- ✅ **AI-Powered SEO**: Generate titles, descriptions, tags, and category suggestions.
- ✅ **Validation**: Check for missing fields, duplicate SKUs, and invalid data.
- ✅ **Image Management**: Download, validate, and upload images to WordPress.
- ✅ **Batch Automation**: Schedule imports and track progress.
- ✅ **Rate Limiting**: Token bucket algorithm for WC API and OpenAI API (prevents 429 errors).
- ✅ **SSRF Protection**: Blocks private IPs in image URLs.
- ✅ **HTML Sanitization**: Bleach sanitization on AI output to prevent XSS.
- ✅ **Idempotent Imports**: Upsert by SKU - safe to re-run.

## Quick Start (0 to 100)

### 1. Prerequisites
- Python 3.10+
- WooCommerce REST API credentials (Consumer Key/Secret)
- OpenAI API key (optional, for AI SEO content)
- Excel file: `Product_Master.xlsx` with 5 sheets (Products, Variations, Categories, Attributes, Images)

### 2. Installation
```bash
git clone <repo-url>
cd AI-Powered-WooCommerce-Product-Automation-System
pip install -e .
```

### 3. Configuration
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
# WOOCOMMERCE_CONSUMER_KEY=ck_xxx
# WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
# OPENAI_API_KEY=sk-xxx (optional)
```

### 4. Prepare Input Data
Place your Excel file at: `input/Product_Master.xlsx`

Required sheets:
- **Products** - Parent products with SKU, title, price, stock, categories, attributes
- **Variations** - Child variations linked by `parent_sku`
- **Categories** - Category names
- **Attributes** - Attribute names and values
- **Images** - Image URLs and optional `local_filename` for local images

Put local images in: `input/images/`

### 5. Run Import
```bash
cd src
python main.py
```

### 6. Check Results
- `output/reports/import_report.xlsx` - Success/failure per SKU
- `output/reports/validation_errors.xlsx` - Validation failures (if any)
- `output/logs/system.log` - Detailed logs

## Key Documents (Read in Order)

| Priority | Document | Purpose |
|----------|----------|---------|
| **1** | [README.md](README.md) | This file - Quick start |
| **2** | [docs/Excel_Data_Dictionary.md](docs/Excel_Data_Dictionary.md) | Excel format, required columns, examples |
| **3** | [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) | Configuration details, environment variables |
| **4** | [docs/SECURITY.md](docs/SECURITY.md) | Rate limiting, SSRF, HTML sanitization details |
| **5** | [docs/PROJECT_KNOWLEDGE.md](docs/PROJECT_KNOWLEDGE.md) | Deep architecture, workflows, troubleshooting |
| **6** | [docs/Architecture.md](docs/Architecture.md) | System architecture diagram |
| **7** | [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Production deployment, monitoring |
| **8** | [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | Running tests, CI/CD |

## Outputs
- **Reports**: `output/reports/validation_report.xlsx`, `output/reports/import_report.xlsx`
- **Logs**: `output/logs/system.log`
- **Image Cache**: `output/image_cache/`

## Commands
```bash
# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Restructure Excel (if starting from CSV)
python scripts/restructure_excel.py
```

## Troubleshooting
| Issue | Solution |
|-------|----------|
| 429 Rate Limited | Increase `rate_limit_rps` in `config/settings.yaml` |
| Images not uploading | Check `input/images/` has files matching `local_filename` |
| Validation fails | Check `output/reports/validation_errors.xlsx` |
| AI not working | Verify `OPENAI_API_KEY` in `.env` |
| Import hangs | Check `output/logs/system.log` for retries |