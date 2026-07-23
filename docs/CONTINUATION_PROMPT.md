# Development Guide

## Quick Start

```bash
# Clone
git clone https://github.com/jlshoja/AI-Powered-WooCommerce-Product-Automation-System
cd AI-Powered-WooCommerce-Product-Automation-System

# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your credentials

# Run
python -m src.main
```

## Project Structure

```
├── config/
│   ├── settings.yaml       # Config template (uses ${ENV_VAR})
│   ├── logging.yaml        # Logging config
│   └── .gitignore          # Ignores settings.yaml
├── docs/                   # Documentation
├── input/                  # Excel input files
├── output/                 # Generated reports, logs, image cache
├── scripts/                # One-off scripts (Excel restructuring)
├── src/
│   ├── ai/                 # AI client & manager
│   ├── automation/         # Batch import, scheduling, tracking
│   ├── excel_parser/       # Excel → Pydantic models
│   ├── image_manager/      # Download, validate, upload, attach
│   ├── reporter/           # Validation reports
│   ├── tests/              # Ad-hoc verification
│   ├── utils/              # Logger, rate limiter, credentials
│   ├── validator/          # Validation rules & reports
│   ├── woocommerce/        # WC API client
│   └── main.py             # Entry point
├── tests/                  # pytest unit tests
├── .env.example            # Secrets template
├── .gitignore
├── pyproject.toml          # Build, deps, tools config
├── README.md
└── requirements.txt        # Legacy (use pyproject.toml)
```

## Configuration

### Settings (`config/settings.yaml`)

All values use `${ENV_VAR}` placeholders. Override via `.env`:

```yaml
woocommerce:
  api_url: "${WOOCOMMERCE_API_URL}"
  consumer_key: "${WOOCOMMERCE_CONSUMER_KEY}"
  consumer_secret: "${WOOCOMMERCE_CONSUMER_SECRET}"
  timeout: ${WOOCOMMERCE_TIMEOUT:-30}
  max_retries: ${WOOCOMMERCE_MAX_RETRIES:-3}
  rate_limit_rps: ${WOOCOMMERCE_RATE_LIMIT_RPS:-1.0}
  rate_burst: ${WOOCOMMERCE_RATE_BURST:-2}

wordpress:
  user: "${WP_USER}"
  app_password: "${WP_APP_PASSWORD}"

excel:
  input_path: "${EXCEL_INPUT_PATH}"
  output_dir: "${EXCEL_OUTPUT_DIR}"

validation:
  min_price: ${VALIDATION_MIN_PRICE:-1000}
  max_price: ${VALIDATION_MAX_PRICE:-10000000}
  required_fields: ${VALIDATION_REQUIRED_FIELDS:-"sku,post_title,regular_price"}

ai:
  api_key: "${OPENAI_API_KEY}"
  model: "${OPENAI_MODEL:-gpt-4o-mini}"
  rate_limit_rps: ${OPENAI_RATE_LIMIT_RPS:-3.0}
  rate_burst: ${OPENAI_RATE_BURST:-5}

image:
  cache_dir: "${IMAGE_CACHE_DIR}"
  local_folder: "${IMAGE_LOCAL_FOLDER}"
  max_size_mb: ${IMAGE_MAX_SIZE_MB:-2}
  allowed_formats: ${IMAGE_ALLOWED_FORMATS:-"JPEG,PNG,WEBP"}
  ssrf_protection: ${IMAGE_SSRF_PROTECTION:-true}
  attachment_mode: "${IMAGE_ATTACHMENT_MODE:-gallery}"
```

### Environment Variables (`.env`)

```bash
# WooCommerce
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
WOOCOMMERCE_RATE_LIMIT_RPS=1.0
WOOCOMMERCE_RATE_BURST=2

# WordPress (for media uploads - REQUIRED)
# Go to: WordPress Admin > Users > Edit your user > Application Passwords
WP_USER=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_RATE_LIMIT_RPS=3.0
OPENAI_RATE_BURST=5

# Paths
EXCEL_INPUT_PATH=input/Product_Master.csv
EXCEL_OUTPUT_DIR=../output
IMAGE_LOCAL_FOLDER=input/images
IMAGE_CACHE_DIR=output/image_cache

# Image attachment mode: "gallery" (featured + gallery, no variation images) or "variation"
IMAGE_ATTACHMENT_MODE=gallery

# Optional
VALIDATION_MIN_PRICE=1000
VALIDATION_MAX_PRICE=10000000
IMAGE_MAX_SIZE_MB=2
IMAGE_ALLOWED_FORMATS="JPEG,PNG,WEBP"
IMAGE_SSRF_PROTECTION=true
```

## Running the System

### Full Import
```bash
python -m src.main
```

### Test Single Product
```bash
python -m src.main --test-sku 2106
```

### Dry Run (Validate Only)
```bash
python -m src.main --dry-run
```

### With External Credentials
```bash
python -m src.main --credentials C:\path\to\providers.xlsx
```

### Windows Menu
Double-click `run.bat` for a menu-based interface.

## Features (v0.3+)

### 1. Configurable Image Attachment Mode
Set `IMAGE_ATTACHMENT_MODE` in `.env`:
- **`gallery` (default)**: Featured image + product gallery. No variation-specific images.
- **`variation`**: Legacy behavior - each variation gets its own image attached.

### 2. Existing WooCommerce Attributes Reuse
At startup, fetches all existing WC attributes and their terms.
- Matches by Persian display name (e.g., "رنگ" for Color)
- Reuses existing attribute IDs instead of creating duplicates
- Resolves term names to existing term IDs; creates missing terms under the correct attribute
- Enables color swatch plugins to work (if hex codes are configured in WC term meta)

### 3. Persian Attribute Labels
Reads `attribute_name:*` columns from CSV (e.g., `attribute_name:color` → "رنگ")
- Uses Persian display names in WC API payloads
- Fixes frontend showing "Color" instead of "رنگ"

### 4. Media Cache (Avoid Re-uploads)
- Local cache: `output/media_cache.json` maps filename → WC media ID
- Before upload, searches WC media library by filename
- Reuses existing media IDs, preventing duplicate uploads
- Works across import runs

### 5. Variation Stock Management
- Variable products: parent has `manage_stock=false`
- Variations handle their own stock quantities
- Updates sync variations (create missing, update existing, delete stale)

### 6. MIME Type Detection
- Detects PNG/JPEG/WEBP/GIF from file signatures
- No longer hardcodes `image/webp`

### 7. Attribute Variation Filtering
- Only attributes actually used in variations get `"variation": true`
- Other attributes (dimensions, materials, etc.) are specifications only

## Testing

### Unit Tests
```bash
# All
pytest

# Specific module
pytest tests/test_ai/
pytest tests/test_woocommerce/test_client.py

# With coverage
pytest --cov=src --cov-report=term-missing

# Watch mode
pytest-watch
```

### Linting & Type Checking
```bash
# Lint
ruff check src/ tests/

# Auto-fix
ruff check --fix src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Security Features (v0.2+)

### Rate Limiting
Token bucket algorithm in `src/utils/rate_limiter.py`:

```python
from src.utils.rate_limiter import TokenBucket, RateLimiter

# Per-endpoint limits
rate_limiter = RateLimiter(
    default_rate=1.0,      # 1 req/s
    default_burst=2,       # burst of 2
    endpoint_limits={
        "products": (1.0, 2),
        "media": (0.5, 1),  # slower for uploads
    }
)

# In your code
rate_limiter.acquire("products")
```

### SSRF Protection
`ImageDownloader` blocks private IP ranges:
- 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- 127.0.0.0/8 (localhost)
- 169.254.0.0/16 (link-local)
- IPv6: ::1/128, fc00::/7, fe80::/10
- Hostnames: localhost, 0.0.0.0

Configurable via `image.ssrf_protection` in settings.yaml.

### HTML Sanitization
All AI-generated content sanitized with `bleach` in `AIClient`:
- Allowed tags: p, br, strong, em, u, b, i, ul, ol, li, span, div
- Allowed attributes: class, style on span/div
- Strips: script, iframe, onload, onclick, etc.

## Debugging

### Logs
```bash
# Main log
tail -f output/logs/system.log

# Module-specific
tail -f output/logs/src.woocommerce.client.log
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: src` | Run from project root, not `src/` |
| `FileNotFoundError: settings.yaml` | Check `.env` paths, use absolute paths |
| `401 Unauthorized` | Verify WC keys in `.env` |
| `Rate limit (429)` | Add delay, implement rate limiter |
| `Image download fails` | Check URL accessibility, size limit |
| `Duplicate SKU` | Enable upsert, or clean WC first |
| `Images not in gallery` | Ensure `IMAGE_ATTACHMENT_MODE=gallery` |
| `Color swatches not showing` | Add hex codes to color terms in WP Admin |

### Debug Mode
```bash
# Verbose logging
LOG_LEVEL=DEBUG python main.py

# Single product test
python -c "
from src.excel_parser.reader import ExcelReader
from pathlib import Path
reader = ExcelReader(Path('../output/Product_Master.xlsx'))
products = reader.read_products()
print(products[0].model_dump_json(indent=2))
"
```

## Excel Data Format

### Required Sheets
- **Products**: Parent products
- **Variations**: Child products (linked by `parent_sku`)
- **Categories**: Hierarchical (`name`, `parent_category`)
- **Attributes**: Global attributes (`name`, `values` pipe-separated)
- **Images**: Metadata (`product_sku`, `image_url`, `alt_text`, `is_main`)

### Column Naming
- WC fields: `post_title`, `sku`, `regular_price`, `post_status`
- Attributes: `attribute:Color`, `attribute:Size` (values pipe-separated)
- Attribute labels: `attribute_name:Color` → "رنگ" (Persian display name)
- SEO: `meta:_yoast_wpseo_title`, `meta:_yoast_wpseo_metadesc`
- Images: `images`, `gallery_images`, `image_alt`, `image_titles`
- Local images: `image_filename` (pipe-separated filenames from `input/images/`)

See `docs/Excel_Data_Dictionary.md` for full schema.

## Dependencies

### Core
- `pandas`, `openpyxl` - Excel processing
- `woocommerce` - WC REST API
- `pydantic` - Data validation
- `openai` - AI generation
- `pillow` - Image validation
- `requests` - Image download
- `pyyaml` - Config
- `python-dotenv` - Env loading

### Dev
- `pytest`, `pytest-mock`, `pytest-cov`
- `ruff` - Linting + formatting
- `mypy` - Type checking
- `pre-commit` - Git hooks

## CI/CD (Planned)

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: mypy src/
      - run: pytest --cov=src --cov-fail-under=80
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag: `git tag v0.3.0`
4. Push: `git push origin v0.3.0`
5. GitHub Actions builds & publishes (when configured)

## Troubleshooting Checklist

- [ ] `.env` exists with valid credentials
- [ ] `input/Product_Master.csv` exists
- [ ] WC API accessible (test in browser)
- [ ] OpenAI key valid and has quota
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -e ".[dev]"`)
- [ ] Tests pass (`pytest`)
- [ ] Lint clean (`ruff check src/ tests/`)

---

## Key Implementation Files

| Feature | Files |
|---------|-------|
| Image attachment modes | `src/image_manager/manager.py`, `src/image_manager/uploader.py` |
| WC attribute reuse | `src/woocommerce/client.py` (`load_attributes`, `resolve_attribute_id`, `resolve_term_ids`) |
| Persian labels | `src/excel_parser/reader.py` (parses `attribute_name:*`), `src/woocommerce/client.py` |
| Media cache | `src/image_manager/uploader.py` (`_media_cache`, `_find_media_by_filename`) |
| Gallery building | `src/image_manager/uploader.py` (`attach_image_to_product`) |
| Attribute variation filter | `src/woocommerce/client.py` (`_map_product_to_payload` checks `variation_attr_names`) |
| MIME detection | `src/image_manager/uploader.py` (`upload_image` uses file signatures) |

<tool_call>
<function=write>
<parameter=content>
# AI-Powered WooCommerce Product Automation System

## Project Overview
Automated product import pipeline: **CSV/Excel → Pydantic Models → AI SEO Enrichment → WooCommerce REST API → Image Upload & Attachment**

**Run command**: `python -m src.main` (from project root)

---

## Completed Features (v0.3.0)

### 1. Configurable Image Attachment Mode
- **gallery** (default): Featured image + product gallery thumbnails. No variation-specific images.
- **variation**: Legacy behavior - each variation gets its own image attached.
- Set via `IMAGE_ATTACHMENT_MODE` in `.env` or `image.attachment_mode` in `settings.yaml`

### 2. Existing WooCommerce Attributes Reuse
- Fetches all WC attributes + terms at startup (`load_attributes()`)
- Matches by Persian display name (e.g., "رنگ" → color attribute)
- Reuses existing attribute IDs and term IDs
- Creates missing terms under the correct existing attribute
- Enables color swatch plugins (requires hex codes in WC term meta)

### 3. Persian Attribute Labels
- Parses `attribute_name:*` columns from CSV (e.g., `attribute_name:color` → "رنگ")
- Uses Persian names in WC API payloads
- Fixes frontend showing English keys instead of Persian labels

### 4. Media Cache (Avoid Re-uploads)
- Local JSON cache: `output/media_cache.json` (filename → media_id)
- Before upload: searches WP media library by filename
- Reuses existing media IDs, prevents duplicate uploads

### 5. Gallery Building Logic
- `attach_image_to_product()` fetches existing images, adds new one, re-indexes positions
- Main image at position 0, gallery images at 1, 2, ...
- No duplicates, no overwrites

### 6. Variation Stock Management
- Variable products: parent `manage_stock=false`
- Variations: handle own stock quantities
- Sync on update: create missing, update existing, delete stale variations

### 7. MIME Type Detection
- File signature sniffing: PNG/JPEG/WEBP/GIF
- No longer hardcoded `image/webp`

### 8. Attribute Variation Filtering
- Only attributes used in variations get `"variation": true`
- Others (dimensions, materials, etc.) are specifications only

### 9. Variation Images Fixed (v0.3.1)
- Variations no longer get their own images in gallery mode
- Gallery images attached to parent product only

---

## Configuration (`.env`)

```bash
# WooCommerce
WOOCOMMERCE_API_URL=https://luxbaz.com
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx

# WordPress (REQUIRED for media uploads)
# WP Admin > Users > Edit > Application Passwords
WP_USER=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Image mode: gallery | variation
IMAGE_ATTACHMENT_MODE=gallery

# Paths (absolute paths recommended)
EXCEL_INPUT_PATH=E:/.../input/Product_Master.csv
IMAGE_LOCAL_FOLDER=E:/.../input/images
IMAGE_CACHE_DIR=E:/.../output/image_cache
```

---

## Input Data Format

**CSV columns:**
- `attribute:color` → values like `مشکی طرح 1|مشکی طرح 2`
- `attribute_name:color` → Persian label `رنگ`
- `image_filename` → pipe-separated local filenames: `main.webp|gallery1.webp|gallery2.webp`
- `gallery_images` → pipe-separated URLs (first = main if duplicated)
- `sale_tag` → used as tag if `tags` not provided

---

## Key Implementation Files

| Feature | Files |
|---------|-------|
| Image modes | `src/image_manager/manager.py`, `src/image_manager/uploader.py` |
| WC attribute reuse | `src/woocommerce/client.py` (`load_attributes`, `resolve_attribute_id`, `resolve_term_ids`) |
| Persian labels | `src/excel_parser/reader.py` (parses `attribute_name:*`), `src/woocommerce/client.py` |
| Media cache | `src/image_manager/uploader.py` (`_media_cache`, `_find_media_by_filename`) |
| Gallery building | `src/image_manager/uploader.py` (`attach_image_to_product`) |
| Attribute variation filter | `src/woocommerce/client.py` (`_map_product_to_payload`) |
| MIME detection | `src/image_manager/uploader.py` (`upload_image` file signatures) |

---

## Tests
```bash
pytest tests/ -v
# 46 tests pass
```

---

## Remaining Manual Steps

1. **Color Swatches**: Add hex codes to color terms in WP Admin > Products > Attributes > رنگ > Configure terms
2. **FTP Bulk Upload** (Issue 5): Low priority, not implemented

---

## For Next AI Session

Start with:
```bash
cd E:\Luxbaz\All Codes\Projects\AI-Powered-WooCommerce-Product-Automation-System
python -m src.main --test-sku 5718
```

All 46 tests pass. System is production-ready.