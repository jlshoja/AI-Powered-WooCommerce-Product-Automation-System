# AI-Powered WooCommerce Product Automation System

## Overview
Automate WooCommerce product imports from Excel with **AI-generated SEO content**, **validation**, **FTP bulk upload**, and **crash-recoverable batch processing**.

## Features
- ✅ **Excel to WooCommerce**: Import products, variations, categories, and images
- ✅ **CSV Auto-Conversion**: CSV input auto-converts to XLSX on startup
- ✅ **AI-Powered SEO**: Generate titles, descriptions, tags, and category suggestions
- ✅ **AI Provider Fallback**: Multiple AI providers with automatic fallback on failure
- ✅ **External Credentials**: API keys from external Excel file (security)
- ✅ **Single Product Test**: Test with `--test-sku` before full batch
- ✅ **Dry Run Mode**: Validate without uploading (`--dry-run`)
- ✅ **Validation**: Check for missing fields, duplicate SKUs, and invalid data
- ✅ **Image Management**: Download from local folder or your website, validate, upload
- ✅ **FTP Bulk Upload**: Fast bulk image upload via FTP (`--upload-mode ftp`)
- ✅ **REST API Upload**: Default image upload via WordPress REST API
- ✅ **Batch Automation**: Schedule imports and track progress
- ✅ **Rate Limiting**: Token bucket algorithm (prevents 429 errors)
- ✅ **SSRF Protection**: Blocks private IPs in image URLs
- ✅ **HTML Sanitization**: Bleach sanitization on AI output
- ✅ **Idempotent Imports**: Upsert by SKU - safe to re-run
- ✅ **Crash Recovery**: Per-stage checkpoints, resume from last good state
- ✅ **Retry Failed**: Re-run only failed products from last import

## Quick Start (0 to 100)

### 1. Prerequisites
- Python 3.10+
- WooCommerce REST API credentials (Consumer Key/Secret)
- WordPress Application Password (for media uploads)
- OpenAI API key (optional, for AI SEO content)
- Excel file or CSV with product data

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
# WOOCOMMERCE_API_URL=https://your-store.com
# WOOCOMMERCE_CONSUMER_KEY=ck_xxx
# WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
# WP_USER=admin
# WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
# OPENAI_API_KEY=sk-xxx (optional)
```

**Or use external credentials Excel** (recommended for security):
See [QUICK_START.md](docs/QUICK_START.md#q13-ai-api-configuration) for format.

### 4. Prepare Input Data

**Option A: From CSV (Recommended)**
Place your CSV at `input/Product_Master.csv`. The project auto-converts to XLSX on startup.

**Option B: From Excel**
Place `Product_Master.xlsx` in `input/` folder with 5 sheets.

### 5. Run Import

**Windows (easiest):** Double-click `run.bat` and select an option.

**Command line:**
```bash
# Full import
python -m src.main

# Test single product first
python -m src.main --test-sku 2106

# Dry run (validate only)
python -m src.main --dry-run

# With external credentials
python -m src.main --credentials C:\path\to\providers.xlsx

# FTP bulk upload mode (for large imports)
python -m src.main --upload-mode ftp

# Resume from last checkpoint (skip completed products)
python -m src.main --resume

# Re-run only failed products from last import
python -m src.main --retry-failed
```

### 6. Check Results
- `import_report.xlsx` - Success/failure per SKU
- `output/import_checkpoint.json` - Per-stage progress (for resume)
- `output/logs/system.log` - Detailed logs

## Image Upload Modes

### REST API Mode (default)
Images uploaded via WordPress REST API. Safe, checks for duplicates.
```bash
python -m src.main --upload-mode restapi
```

### FTP Mode (for 1000+ images)
Fast bulk upload via FTP. Requires one-time PHP script setup.
```bash
# One-time: upload scripts/ftp-register-media.php to WordPress root
# Then:
python -m src.main --upload-mode ftp
```
See [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) for FTP setup details.

## Crash Recovery

The pipeline saves checkpoints after each stage:
1. `product_created` → Product exists in WooCommerce
2. `variations_created` → All variations synced
3. `images_uploaded` → All images attached
4. `completed` → Fully imported

If the process crashes:
```bash
# Resume from last checkpoint (skip completed products)
python -m src.main --resume

# Or re-run only failed products
python -m src.main --retry-failed
```

## WooCommerce Alignment

Imported products match manually-created products:
- **manage_stock**: `true` for simple products, `false` for variable (variations manage own stock)
- **Color attribute**: `visible: false` (matches WP Admin default)
- **Other attributes**: `visible: true` (shown on product page)

## AI Provider Fallback

If you have multiple AI providers in `providers.xlsx`, the project automatically falls back:
1. Try primary provider (e.g., OpenAI)
2. If fails → try next provider (e.g., OpenRouter)
3. All fail → AI disabled, import continues without AI content

## Key Documents

| Priority | Document | Purpose |
|----------|----------|---------|
| **1** | [README.md](README.md) | This file - Quick start |
| **2** | [docs/QUICK_START.md](docs/QUICK_START.md) | Setup guide + FAQ |
| **3** | [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) | Configuration, CLI flags |
| **4** | [docs/SECURITY.md](docs/SECURITY.md) | Security measures |
| **5** | [docs/PROJECT_KNOWLEDGE.md](docs/PROJECT_KNOWLEDGE.md) | Architecture, troubleshooting |

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

## CLI Flags Reference
| Flag | Description |
|------|-------------|
| `--test-sku SKU` | Import only a single product by SKU |
| `--dry-run` | Validate without uploading |
| `--batch-size N` | Products per batch (default: 10) |
| `--credentials PATH` | External credentials Excel file |
| `--upload-mode {restapi,ftp}` | Image upload mode (default: restapi) |
| `--resume` | Skip fully completed products (use checkpoint) |
| `--retry-failed` | Re-run only failed products from last import |

## Troubleshooting
| Issue | Solution |
|-------|----------|
| 429 Rate Limited | Reduce `rate_limit_rps` in config/settings.yaml |
| Images not uploading | Check `input/images/` or verify `image_url` is accessible |
| Validation fails | Check `validation_errors.xlsx` |
| AI not working | Verify API key in .env or providers.xlsx |
| API key invalid | Project logs warning and continues without AI |
| Import hangs | Check `output/logs/system.log` for retries |
| Product out of stock | Check variation stock quantities (parent has manage_stock=false) |
| Colors show as dropdown | Ensure IMAGE_ATTACHMENT_MODE=gallery, color attribute is global |
| Resume not working | Check `output/import_checkpoint.json` exists |
