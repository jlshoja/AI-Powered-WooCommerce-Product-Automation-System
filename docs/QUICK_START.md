# Quick Start Guide - AI-Powered WooCommerce Product Automation

## Overview
This system automates importing products from Excel to WooCommerce with AI-generated SEO content, image management, and validation.

## Prerequisites
- Python 3.10+
- WooCommerce store with REST API enabled
- OpenAI API key (optional, for AI content generation)

## Step-by-Step Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd AI-Powered-WooCommerce-Product-Automation-System
pip install -e .
```

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# WooCommerce (Required)
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxx

# OpenAI (Optional - for AI content generation)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

### 3. Prepare Input Data

#### Excel Format (Required)
Place your product data in `input/Product_Master.xlsx` with 5 sheets:

| Sheet | Required Columns |
|-------|-----------------|
| **Products** | sku, post_title, regular_price, stock_status, post_status, categories, attributes, description, short_description, seo_title, seo_description, tags |
| **Variations** | sku, parent_sku, regular_price, sale_price, stock_quantity, stock_status, manage_stock, attributes, images |
| **Categories** | name, parent, description |
| **Attributes** | name, values (pipe-separated) |
| **Images** | product_sku, image_url, local_filename, alt_text, title, is_main |

See [Excel Data Dictionary](Excel_Data_Dictionary.md) for full schema.

#### Images (Optional)
Place product images in `input/images/` as `.webp` files. Reference them via `local_filename` column in Images sheet.

### 4. Generate Excel (if starting from CSV)
```bash
python scripts/restructure_excel.py
```

### 5. Run Import
```bash
cd src
python main.py
```

## What Happens During Import

1. **Validation** - Checks required fields, SKU uniqueness, price ranges, stock
2. **AI Enhancement** - Generates SEO titles, descriptions, tags, categories (if enabled)
3. **WC Upsert** - Creates/updates products by SKU (idempotent)
4. **Images** - Downloads/copies → validates → uploads to WP Media → attaches
5. **Report** - Generates `output/reports/import_report.xlsx` with status per SKU

## Resume After Failure
Simply re-run `python main.py`. The system:
- Uses SKU lookup to update existing products
- Skips already-cached images
- Reports failures in `import_report.xlsx`

## Key Configuration Options

| Setting | File | Description |
|---------|------|-------------|
| Batch size | `main.py` | Products per batch (default: 10) |
| Rate limits | `settings.yaml` | WC: 1 req/s, AI: 3 req/s |
| Price range | `settings.yaml` | 1000 - 10,000,000 |
| Image size | `settings.yaml` | Max 2MB, JPEG/PNG/WEBP |

## Output Files

| File | Purpose |
|------|---------|
| `output/reports/import_report.xlsx` | Per-SKU success/failure |
| `output/reports/validation_errors.xlsx` | Validation failures |
| `output/logs/system.log` | Detailed logs |
| `output/image_cache/` | Cached images |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 429 Rate Limited | Reduce `rate_limit_rps` in settings.yaml |
| Images not attaching | Check `local_filename` matches file in `input/images/` |
| Validation fails | Check `validation_errors.xlsx` for details |
| AI not working | Verify `OPENAI_API_KEY` in .env |

## Document Reading Order (0 to 100)

| Order | Document | Purpose |
|-------|----------|---------|
| 1 | **This file** | Quick start |
| 2 | [Excel Data Dictionary](Excel_Data_Dictionary.md) | Input format details |
| 3 | [Configuration Guide](CONFIGURATION.md) | All settings explained |
| 4 | [Architecture](Architecture.md) | System design |
| 5 | [Development Guide](DEVELOPMENT_GUIDE.md) | Extending the system |
| 6 | [Security](SECURITY.md) | Security considerations |
| 7 | [Deployment](DEPLOYMENT_GUIDE.md) | Production deployment |
| 8 | [Project Knowledge](PROJECT_KNOWLEDGE.md) | Complete technical reference |

## Support
- Check logs in `output/logs/system.log`
- Review reports in `output/reports/`
- Run tests: `pytest -v`