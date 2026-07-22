# Quick Start Guide - AI-Powered WooCommerce Product Automation

## Overview
This system automates importing products from Excel/CSV to WooCommerce with AI-generated SEO content, image management, and validation.

## Prerequisites
- Python 3.10+
- WooCommerce store with REST API enabled
- OpenAI API key (optional, for AI content generation)

## Quick Start (Windows)
Double-click `run.bat` and select an option:
1. **Full import** — Import all products
2. **Test single product** — Test with one SKU before full batch
3. **Dry run** — Validate only, no upload
4. **Restructure CSV** — Convert CSV to XLSX format
5. **Run tests** — Run test suite

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

# AI (Optional - for AI content generation)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1  # Leave empty for OpenAI, or set for other providers
```

### 3. Prepare Input Data

#### Option A: From CSV (Recommended)
Place your CSV file at `input/Product_Master.csv` and run:
```bash
python -m src.main
```
This automatically converts CSV to XLSX format with 5 sheets on first run.

#### Option B: From Excel
Place `Product_Master.xlsx` directly in `input/` folder.

### 4. Run Import
```bash
# Full import
python -m src.main

# Test single product first
python -m src.main --test-sku 2106

# Dry run (validate only)
python -m src.main --dry-run
```

---

## Frequently Asked Questions

### Q1: Input Excel Format
**A:** The project handles this automatically. If you have a CSV file, the restructure script converts it to the required 5-sheet XLSX format. You don't need to manually create the Excel.

### Q2: Image Upload - Automatic or Manual?
**A:** **Fully automatic.** The project:
1. Reads image filenames from `local_image` and `local_gallery_images` columns
2. Finds images in `input/images/` folder
3. If not found locally → downloads from URL
4. Validates (size ≤ 2MB, format: JPEG/PNG/WEBP)
5. Uploads to WordPress Media Library
6. Attaches to product with correct position (main vs gallery)

### Q3: How Are Images Matched to Products?
**A:** By filename convention in the CSV:
- `local_image` column: e.g., `men-bag-2106-main.webp` → looks in `input/images/men-bag-2106-main.webp`
- `local_gallery_images` column: pipe-separated filenames → looks in `input/images/{filename}`
- Extra images in the folder are **ignored** — only those listed in CSV are processed

**Important:** The `image_url` column contains URLs from **your own website** (e.g., `https://luxbaz.com/wp-content/uploads/...`). These are NOT supplier URLs. If images aren't found locally, the project downloads from your website to use as the source.

### Q4: What If Images Are Missing?
**A:** Fallback chain:
1. Local folder (`input/images/{filename}`) → copy to cache
2. URL download (from `image_url` column) → save to cache
3. If both fail → product is still imported, image failure logged in `import_report.xlsx`

### Q5: Manual Image Upload Requirements
**A:** If uploading images manually:
- **Location:** `input/images/` folder
- **Naming:** Any name, but must match the `local_image` / `local_gallery_images` column in CSV
- **Format:** JPEG, PNG, or WEBP
- **Max size:** 2MB per image
- **Main image:** Set `local_image` column to the main image filename
- **Gallery images:** Set `local_gallery_images` column to pipe-separated filenames

### Q6: FTP vs Automatic Upload?
**A:**
| Method | Best For |
|--------|----------|
| **Automatic (project)** | Reliability, retry on failure, progress tracking |
| **Manual FTP** | Initial bulk upload of thousands of images |

**Recommendation:** Use automatic for most cases. Use FTP only for initial bulk upload, then let the project handle attachment.

### Q7: Resume Support?
**A:** **Yes.** The system uses **idempotent upsert**:
- If SKU exists → product is **updated** (not duplicated)
- If interrupted → re-run safely processes all products
- Failed products logged in `import_report.xlsx`
- Images already in cache are skipped (no re-download)

### Q8: Batch Size, Rate Limit, Price Range
**A:**
| Setting | Default | Purpose |
|---------|---------|---------|
| **Batch size** | 10 | Products per batch (for logging/progress) |
| **WC rate limit** | 1 req/s | Prevents WooCommerce API throttling |
| **AI rate limit** | 3 req/s | Prevents OpenAI API throttling |
| **Price range** | 10,000 - 100,000,000 | Validation: rejects products outside this range (IRR currency) |

**Why price range?** Catches data entry errors (e.g., price = 100 instead of 100,000).

### Q9: Image Cache
**A:** **Location:** `output/image_cache/`

**Purpose:** Stores downloaded/copied images to avoid re-downloading on re-runs. If an image is already in cache, the download step is skipped entirely.

**When to clear:** Only if you want to force re-download all images.

### Q10: Run from .bat File?
**A:** **Yes!** Use `run.bat` in the project root. It provides a menu:
1. Full import
2. Test single product
3. Dry run
4. Restructure CSV
5. Run tests

### Q11: Auto Retry on Failure?
**A:**
- **API calls:** 3 retries with exponential backoff
- **Image downloads:** 3 retries with exponential backoff
- **Product import:** Continues to next product on failure (doesn't stop batch)
- **Full resume:** Re-run `python -m src.main` — all products are re-processed safely via upsert

### Q12: Duplicate Product Detection?
**A:**
| Scenario | Behavior |
|----------|----------|
| **Same SKU exists, no changes** | Product skipped (updated with same data) |
| **Same SKU exists, price/color changed** | Product **updated** with new values |
| **Same SKU doesn't exist** | New product created |
| **Duplicate SKU in Excel** | Validation error before import |

**No fuzzy matching** — only exact SKU match. If you need to match by name, that's a future feature.

### Q13: AI API Configuration
**A:**
```yaml
ai:
  api_key: "your_api_key_here"
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"  # Or any OpenAI-compatible API
```

**Supported providers:**
- OpenAI (default, no base_url needed)
- OpenRouter (`https://openrouter.ai/api/v1`)
- Mimo (`https://api.mimo.com/v1`)
- MiniMax (`https://api.minimax.chat/v1`)
- Any OpenAI-compatible API

**Alternative: External Credentials File (Recommended for Security)**

Instead of hardcoding keys in settings.yaml, create `providers.xlsx` OUTSIDE the project root:

| provider | api_key | model | base_url |
|----------|---------|-------|----------|
| openai | sk-xxx... | gpt-4o-mini | https://api.openai.com/v1 |
| openrouter | sk-or-xxx... | gpt-4o-mini | https://openrouter.ai/api/v1 |
| woocommerce | | | https://your-store.com/wp-json/wc/v3 |

For WooCommerce, add columns: `consumer_key`, `consumer_secret`

Then run:
```bash
python -m src.main --credentials C:\path\to\providers.xlsx
```

Or use `run.bat` option 6.

### Q14: What If API Key Is Invalid?
**A:** The system logs the error and **continues without AI**. Products are still imported, just without AI-generated SEO content. You'll see in logs:
```
AI disabled: no valid API key configured
```

### Q15: Single Product Test?
**A:** **Yes!** Use the `--test-sku` flag:
```bash
python -m src.main --test-sku 2106
```
This imports only that SKU, useful for testing before full batch.

### Q16: What Does "is_main" Mean?
**A:** Only **ONE** image per product should be `is_main=True`:
- **Main image** (`is_main=True`): The featured product image shown on shop pages
- **Gallery images** (`is_main=False`): Secondary images in the product page carousel
- **Variation images**: Each variation has its own single main image

In the code, `product.images[0]` is always main, `product.gallery_images` are always non-main.

---

## Key Configuration Options

| Setting | File | Description |
|---------|------|-------------|
| Batch size | `main.py` | Products per batch (default: 10) |
| Rate limits | `settings.yaml` | WC: 1 req/s, AI: 3 req/s |
| Price range | `settings.yaml` | 10,000 - 100,000,000 (IRR) |
| Image size | `settings.yaml` | Max 2MB, JPEG/PNG/WEBP |
| AI base URL | `settings.yaml` | For non-OpenAI providers |
| Local images | `settings.yaml` | `input/images/` folder |

## Output Files

| File | Purpose |
|------|---------|
| `output/reports/import_report.xlsx` | Per-SKU success/failure |
| `output/reports/validation_errors.xlsx` | Validation failures |
| `output/logs/system.log` | Detailed logs |
| `output/image_cache/` | Cached images |
| `output/Product_Master.xlsx` | Generated Excel (from CSV) |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 429 Rate Limited | Reduce `rate_limit_rps` in settings.yaml |
| Images not attaching | Check `local_filename` matches file in `input/images/` |
| Validation fails | Check `validation_errors.xlsx` for details |
| AI not working | Verify `OPENAI_API_KEY` in .env |
| API connection failed | Check `base_url` in settings.yaml |
| Resume not working | Just re-run — system uses idempotent upsert |
