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
cd src
python main.py
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

image:
  cache_dir: "${IMAGE_CACHE_DIR}"
  max_size_mb: ${IMAGE_MAX_SIZE_MB:-2}
  allowed_formats: ${IMAGE_ALLOWED_FORMATS:-"JPEG,PNG,WEBP"}
```

### Environment Variables (`.env`)

```bash
# WooCommerce
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# Paths
EXCEL_INPUT_PATH=/path/to/Product_Master.xlsx
EXCEL_OUTPUT_DIR=../output

# Optional
VALIDATION_MIN_PRICE=1000
VALIDATION_MAX_PRICE=10000000
IMAGE_CACHE_DIR=../output/image_cache
```

## Running the System

### Full Import
```bash
cd src
python main.py
```

### With Custom Config
```bash
cd src
python main.py --config ../config/settings.yaml
```

### Dry Run (Not Yet Implemented)
```bash
python main.py --dry-run
```

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