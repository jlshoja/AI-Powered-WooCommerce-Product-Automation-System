# AI-Powered WooCommerce Product Automation System

Import products from CSV/Excel into WooCommerce with AI-generated SEO content, image management, and crash recovery.

## What It Does

1. Reads product data from CSV/Excel (products, variations, categories, attributes, images)
2. Optionally generates SEO titles, descriptions, tags via OpenAI
3. Creates/updates products in WooCommerce via REST API
4. Downloads and uploads images (via REST API or FTP bulk upload)
5. Syncs variations, attributes, stock, and gallery

## Prerequisites

- Python 3.10+
- WooCommerce REST API credentials (Consumer Key/Secret)
- WordPress Application Password (for media uploads)
- OpenAI API key (optional, for AI SEO content)
- CSV or Excel file with product data

## Installation

```bash
git clone https://github.com/jlshoja/AI-Powered-WooCommerce-Product-Automation-System
cd AI-Powered-WooCommerce-Product-Automation-System
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Key settings in `.env`:
```
WOOCOMMERCE_API_URL=https://luxbaz.com
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
WP_USER=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx
IMAGE_ATTACHMENT_MODE=gallery
IMAGE_UPLOAD_MODE=restapi
OPENAI_API_KEY=sk-xxx          # optional
```

## Input Data

Place your CSV at `input/Product_Master.csv`. Required columns:

| Column | Description |
|--------|-------------|
| `sku` | Unique product identifier |
| `post_title` | Product name |
| `regular_price` | Price |
| `attribute:color` | Color values (pipe-separated) |
| `attribute_name:color` | Persian label (e.g., رنگ) |
| `image_filename` | Local image filenames (pipe-separated) |
| `gallery_images` | Image URLs (pipe-separated) |

See `docs/Excel_Data_Dictionary.md` for full schema.

## Running

### Full import
```bash
python -m src.main
```

### Test single product
```bash
python -m src.main --test-sku 5718
```

### Dry run (validate only)
```bash
python -m src.main --dry-run
```

### FTP bulk upload (for 1000+ images)
```bash
python -m src.main --upload-mode ftp
```

### Resume from checkpoint
```bash
python -m src.main --resume
```

### Retry failed products only
```bash
python -m src.main --retry-failed
```

### With external credentials
```bash
python -m src.main --credentials C:\path\to\providers.xlsx
```

### Windows menu
Double-click `run.bat`.

## CLI Flags

| Flag | Description |
|------|-------------|
| `--test-sku SKU` | Import only one product by SKU |
| `--dry-run` | Validate without uploading |
| `--batch-size N` | Products per batch (default: 10) |
| `--credentials PATH` | External credentials Excel file |
| `--upload-mode {restapi,ftp}` | Image upload mode (default: restapi) |
| `--resume` | Skip completed products (use checkpoint) |
| `--retry-failed` | Re-run only failed products from last import |

## Image Upload Modes

**REST API (default):** Images uploaded via WordPress REST API. Checks for duplicates by filename.

**FTP (for large imports):** Bulk upload via FTP, then auto-register as WordPress media. One-time setup: upload `scripts/ftp-register-media.php` to WordPress root.

## Crash Recovery

The pipeline saves checkpoints after each stage:
1. `product_created` — Product exists in WooCommerce
2. `variations_created` — All variations synced
3. `images_uploaded` — All images attached
4. `completed` — Fully imported

If the process crashes:
```bash
python -m src.main --resume        # skip completed products
python -m src.main --retry-failed  # re-run only failures
```

## Output Files

| File | Description |
|------|-------------|
| `import_report.xlsx` | Success/failure per SKU |
| `output/import_checkpoint.json` | Per-stage progress (for resume) |
| `output/media_cache.json` | Uploaded image IDs (avoids re-upload) |
| `output/logs/system.log` | Detailed logs |

## Folder Structure

```
├── input/
│   ├── Product_Master.csv     # Your product data
│   └── images/                # Local product images
├── output/
│   ├── logs/                  # System logs
│   ├── media_cache.json       # Image upload cache
│   └── import_checkpoint.json # Crash recovery checkpoints
├── config/
│   └── settings.yaml          # App configuration
├── scripts/
│   └── ftp-register-media.php # WordPress FTP media registration
├── src/
│   ├── main.py                # Entry point
│   ├── automation/            # Batch import, tracking, checkpoints
│   ├── woocommerce/           # WC API client
│   ├── image_manager/         # Image download, upload, attach
│   ├── excel_parser/          # CSV/Excel parsing
│   ├── ai/                    # AI SEO content generation
│   └── validator/             # Data validation
├── tests/                     # Unit tests
├── .env.example               # Config template
└── run.bat                    # Windows launcher
```

## Testing

```bash
pytest -v                      # Run all 46 tests
pytest tests/test_woocommerce/ # WooCommerce tests only
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Product out of stock | Check variation stock (parent has manage_stock=false) |
| Colors show as dropdown | Ensure IMAGE_ATTACHMENT_MODE=gallery, color attribute is global |
| Images not uploading | Check `input/images/` or verify image URLs are accessible |
| 429 Rate Limited | Reduce rate_limit_rps in config/settings.yaml |
| Resume not working | Check `output/import_checkpoint.json` exists |
| AI not working | Verify OpenAI API key in .env |
