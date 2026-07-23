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
│   ├── utils/              # Logger
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
  max_size_mb: ${IMAGE_MAX_SIZE_MB:-2}
  allowed_formats: ${IMAGE_ALLOWED_FORMATS:-"JPEG,PNG,WEBP"}
  ssrf_protection: ${IMAGE_SSRF_PROTECTION:-true}
```

### Environment Variables (`.env`)

```bash
# WooCommerce
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
WOOCOMMERCE_RATE_LIMIT_RPS=1.0
WOOCOMMERCE_RATE_BURST=2

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_RATE_LIMIT_RPS=3.0
OPENAI_RATE_BURST=5

# Paths
EXCEL_INPUT_PATH=/path/to/Product_Master.csv
EXCEL_OUTPUT_DIR=../output

# Optional
VALIDATION_MIN_PRICE=1000
VALIDATION_MAX_PRICE=10000000
IMAGE_CACHE_DIR=../output/image_cache
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

### FTP Bulk Upload
```bash
python -m src.main --upload-mode ftp
```

### Resume from Checkpoint
```bash
python -m src.main --resume
```

### Retry Failed Products
```bash
python -m src.main --retry-failed
```

### Windows Menu
Double-click `run.bat` for a menu-based interface.

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

## AI Prompt Configuration

Edit `config/ai_prompts.yaml` to customize AI-generated content:

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
Token bucket algorithm implemented in `src/utils/rate_limiter.py`:

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
rate_limiter.acquire("products")  # blocks until token available
```

Configuration in `settings.yaml`:
```yaml
woocommerce:
  rate_limit_rps: 1.0
  rate_burst: 2
ai:
  rate_limit_rps: 3.0
  rate_burst: 5
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

---

## Adding Features

### New Validation Rule
1. Add rule class in `src/validator/rules.py`:
```python
class MyCustomRule(ValidationRule):
    def __init__(self, field: str, value: Any, **kwargs):
        is_valid = my_validation_logic(value)
        message = "Custom error" if not is_valid else ""
        super().__init__(field=field, message=message, is_valid=is_valid)
```

2. Import and use in `src/validator/validator.py`:
```python
from .rules import MyCustomRule

def validate_product(self, product):
    rules = [...]
    rules.append(MyCustomRule(field="my_field", value=product.my_field))
    return rules
```

3. Add test in `tests/test_validator/test_validator.py`

### New Excel Field
1. Add to Pydantic model in `src/excel_parser/models.py`
2. Update parser in `src/excel_parser/reader.py`
3. Update WC mapper in `src/woocommerce/client.py` (`_map_product_to_payload`)
4. Add validation if needed
5. Update `docs/Excel_Data_Dictionary.md`

### New AI Prompt
1. Add method in `src/ai/client.py` (`AIClient`)
2. Call from `src/ai/manager.py` (`AIManager.process_product`)
3. Add test in `tests/test_ai/test_ai.py`

### New WC Endpoint
1. Add method in `src/woocommerce/client.py` (`WooCommerceClient`)
2. Use `_retry_request` for consistency
3. Add test in `tests/test_woocommerce/`

## Code Style

### Python
- **Line length**: 100 chars
- **Quotes**: Double
- **Imports**: Sorted (isort via ruff)
- **Types**: Use built-in generics (`list`, `dict`, `X | None`)
- **Docstrings**: Google style for public APIs

### Commits
```
feat: add upsert product logic
fix: handle missing gallery images
docs: update Excel dictionary
refactor: extract image validator
test: add upsert test cases
chore: update dependencies
```

### Branch Naming
```
feat/upsert-products
fix/image-download-timeout
docs/excel-dictionary
refactor/validator-rules
```

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
- Attributes: `attribute:Color`, `attribute:Size`
- SEO: `meta:_yoast_wpseo_title`, `meta:_yoast_wpseo_metadesc`
- Images: `images`, `gallery_images`, `image_alt`, `image_titles`

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
- `loguru` - Logging (optional, currently using stdlib)

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
3. Tag: `git tag v0.2.0`
4. Push: `git push origin v0.2.0`
5. GitHub Actions builds & publishes (when configured)

## Troubleshooting Checklist

- [ ] `.env` exists with valid credentials
- [ ] `input/Product_Master.xlsx` exists
- [ ] WC API accessible (test in browser)
- [ ] OpenAI key valid and has quota
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -e ".[dev]"`)
- [ ] Tests pass (`pytest`)
- [ ] Lint clean (`ruff check src/ tests/`)