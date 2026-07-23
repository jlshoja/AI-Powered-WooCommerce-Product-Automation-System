# RUNBOOK — WooCommerce Product Automation System

Step-by-step checklist for running the import from scratch.

---

## Step 1: One-time setup

```bash
cd AI-Powered-WooCommerce-Product-Automation-System
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Verify:
```
(.venv) > python --version
Python 3.10+
(.venv) > pytest -v
46 passed
```

---

## Step 2: Configure credentials

Copy and edit `.env`:
```bash
cp .env.example .env
```

Fill in these values:

```
WOOCOMMERCE_API_URL=https://luxbaz.com
WOOCOMMERCE_CONSUMER_KEY=ck_xxx        # from WP Admin > WooCommerce > Settings > Advanced > REST API
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
WP_USER=admin                           # WordPress username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx     # from WP Admin > Users > Edit > Application Passwords
IMAGE_ATTACHMENT_MODE=gallery
IMAGE_UPLOAD_MODE=restapi
```

Optional (for AI SEO content):
```
OPENAI_API_KEY=sk-xxx
```

---

## Step 2b: Configure AI prompts (optional)

Edit `config/ai_prompts.yaml` to customize writing rules:

```yaml
seo_title:
  prompt: >
    Generate an SEO-optimized title in Persian for a product named '{product_name}'
    with the following attributes: {attributes}.
    Rules: Use formal tone. Include brand name. Under 60 characters.
  max_tokens: 60
```

Available variables: `{product_name}`, `{attributes}`, `{description}`

Available prompts: `seo_title`, `seo_description`, `product_description`, `tags`, `categories`

Leave a prompt empty to skip AI generation for that field.

---

## Step 3: Prepare input data

Place your CSV at `input/Product_Master.csv`.

Minimum required columns:
| Column | Example |
|--------|---------|
| sku | 5718 |
| post_title | کیف زنانه کد ۵۷۱۸ |
| regular_price | 1799000 |
| attribute:color | مشکی طرح 1\|مشکی طرح 2 |
| attribute_name:color | رنگ |

Optional columns:
| Column | Purpose |
|--------|---------|
| image_filename | main.webp\|gallery1.webp (pipe-separated) |
| gallery_images | URLs for images |
| categories | کیف زنانه>کیف روزمره زنانه (hierarchical) |
| description | Product description |
| meta:_yoast_wpseo_title | SEO title |

Place local images in `input/images/` folder.

---

## Step 4: Test with single product

Always test one product before full batch:
```bash
python -m src.main --test-sku 5718
```

Expected output:
```
Starting WooCommerce Product Automation System...
Loading existing WooCommerce attributes and terms...
  Attribute 'رنگ' (ID:1): 268 terms
  ...
Loaded 10 attributes with terms
Loaded media cache: 6 entries
Loaded 33 products from Excel
Test mode: importing single product with SKU=5718
Product created: 5718
Variation created: 5718-Black - Design 1
Variation created: 5718-Black - Design 2
Image attached to product 13558 (gallery size: 1)
...
Successfully imported product: 5718
```

Verify on website: check that color swatches show (not dropdown), stock is correct.

---

## Step 5: Run full import

```bash
python -m src.main
```

Expected output:
```
Starting WooCommerce Product Automation System...
Loaded 33 products from Excel
Processing batch 1: 10 products
Successfully imported product: 5718
Successfully imported product: 5719
...
Import process completed.
```

Check results:
- Open `import_report.xlsx` — shows success/failure per SKU
- Open `output/logs/system.log` — detailed log

---

## Step 6: Handle failures

If some products failed:
```bash
python -m src.main --retry-failed
```

This reads `import_report.xlsx` and re-runs only the failed products.

---

## Step 7: Resume after crash

If the process was killed mid-run:
```bash
python -m src.main --resume
```

This skips products marked as "completed" in `output/import_checkpoint.json`.

---

## FTP Mode (for 1000+ images)

### One-time setup:
1. Upload `scripts/ftp-register-media.php` to WordPress root directory
2. Add FTP credentials to `.env`:
```
FTP_HOST=your-host.com
FTP_USER=your-user
FTP_PASSWORD=***
FTP_WP_API_URL=https://luxbaz.com
IMAGE_UPLOAD_MODE=ftp
```

### Run:
```bash
python -m src.main --upload-mode ftp
```

---

## Common Failures and Fixes

### "No product found with SKU: XXXX"

**Cause:** SKU in CSV doesn't exist in input file.

**Fix:** Check the SKU column in your CSV. Run without --test-sku to see all SKUs.

### "401 Unauthorized"

**Cause:** WooCommerce API keys are wrong.

**Fix:**
1. Go to WP Admin > WooCommerce > Settings > Advanced > REST API
2. Generate new keys with Read/Write permissions
3. Update `.env` with new keys

### "429 Rate limited"

**Cause:** Too many API requests.

**Fix:** Reduce rate in config/settings.yaml:
```yaml
woocommerce:
  rate_limit_rps: 0.5    # slower
```

### "Images not uploading"

**Cause:** Images not in `input/images/` or URLs not accessible.

**Fix:**
1. Check `input/images/` folder has the files
2. Verify `image_filename` column matches actual filenames
3. Check image URLs are publicly accessible

### "Color shows as dropdown instead of swatches"

**Cause:** Color attribute not linked to global WC attribute.

**Fix:** This should be automatic now. If still happening:
1. Check WP Admin > Products > Attributes — color attribute should have Type: color
2. Re-run import: `python -m src.main --test-sku SKU`

### "Product shows out of stock"

**Cause:** Parent stock quantity mismatch.

**Fix:** This should be automatic now (parent manage_stock=false, variations manage own stock). If still happening:
1. Check variation stock quantities in WP Admin
2. Re-run import

### "Resume not working / re-processing everything"

**Cause:** Checkpoint file missing or corrupted.

**Fix:**
1. Check `output/import_checkpoint.json` exists
2. If corrupted, delete it and re-run
3. Use `--retry-failed` instead of `--resume` for targeted re-run

### "AI not generating content"

**Cause:** OpenAI API key invalid or missing.

**Fix:**
1. Check `.env` has valid `OPENAI_API_KEY`
2. Import continues without AI if key is invalid (just logs warning)

---

## Where to Look if Something Goes Wrong

| What | Where |
|------|-------|
| Real-time progress | Terminal output |
| Success/failure report | `import_report.xlsx` |
| Crash recovery data | `output/import_checkpoint.json` |
| Image upload cache | `output/media_cache.json` |
| Detailed logs | `output/logs/system.log` |
| WooCommerce config | `config/settings.yaml` |
| API keys | `.env` |
| Product data | `input/Product_Master.csv` |
| Local images | `input/images/` |

---

## Quick Reference Commands

```bash
# First-time setup
python -m venv .venv && .venv\Scripts\activate && pip install -e .

# Test single product
python -m src.main --test-sku 5718

# Full import
python -m src.main

# Dry run (validate only)
python -m src.main --dry-run

# Retry failed only
python -m src.main --retry-failed

# Resume from checkpoint
python -m src.main --resume

# FTP bulk upload
python -m src.main --upload-mode ftp

# Run tests
pytest -v
```
