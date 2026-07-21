# Project Knowledge Base

## Overview
**AI-Powered WooCommerce Product Automation System** - A modular Python application that automates product imports from Excel to WooCommerce with AI-generated SEO content.

## Core Purpose
Import products (simple + variable with variations) from a structured Excel workbook into WooCommerce via REST API, with AI-powered SEO optimization (titles, descriptions, tags, categories), validation, and image management.

## Architecture

### Modules
| Module | Path | Responsibility |
|--------|------|----------------|
| Excel Parser | `src/excel_parser/` | Read Products, Variations, Categories, Attributes, Images sheets → Pydantic models |
| Validator | `src/validator/` | Validate required fields, SKU uniqueness, price ranges, stock, images, categories, attributes |
| WooCommerce Client | `src/woocommerce/client.py` | REST API wrapper: auth, retry logic, CRUD for products/variations, SKU lookup, upsert, rollback |
| Image Manager | `src/image_manager/` | Download → validate → upload to WP media → attach to products/variations |
| AI Processing | `src/ai/` | OpenAI integration: SEO titles, descriptions, product descriptions, tags, category suggestions |
| Automation | `src/automation/` | Batch import, progress tracking, scheduling, incremental imports |
| Reporter | `src/reporter/` | Excel validation/import reports |

### Data Flow
```
Excel Workbook → ExcelReader → Product Models → Validator → (AIManager) → WooCommerceClient (upsert) → ImageManager → ProgressTracker → Reports
```

### Key Design Patterns
- **Dependency Injection**: `BatchImporter` receives all services → testable
- **Pydantic Models**: Contracts between layers (Product, Variation, ProductImage, Category, Attribute)
- **Retry Logic**: `_retry_request()` with exponential backoff in WC client
- **Idempotency**: `upsert_product()` checks SKU → update or create

## Configuration

### Environment Variables (`.env`)
```bash
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
EXCEL_INPUT_PATH=./input/Product_Master.xlsx
OUTPUT_DIR=./output
```

### Settings (`config/settings.yaml`)
Uses `${VAR}` placeholders resolved by `main.py:load_settings()` with `python-dotenv`.

## Excel Schema (Input)

### Required Sheets
| Sheet | Key Columns |
|-------|-------------|
| **Products** | ID, post_title, sku, regular_price, post_status, stock_status, categories, images, description, attributes:* |
| **Variations** | ID, sku, parent_sku, regular_price, stock_status, images, attributes:* |
| **Categories** | ID, name, parent_category |
| **Attributes** | ID, name, values (pipe-separated) |
| **Images** | ID, product_sku, image_url, alt_text, title, is_main |

### Attribute Columns
Dynamic columns: `attribute:Color`, `attribute:Size` → parsed as `attributes: {"Color": ["Red", "Blue"]}`

### Image Paths
Must use dynamic WordPress paths: `/uploads/2026/07/filename.webp` (validated by `ImageValidationRule`)

## Running the System

### Prerequisites
```bash
pip install -e ".[dev]"  # installs core + dev deps
cp .env.example .env     # fill in your credentials
```

### Execute
```bash
cd src
python main.py
```

### Dry Run (Planned)
```bash
cd src
python main.py --dry-run  # validates without importing
```

## Testing

```bash
# All tests
pytest -v

# Specific module
pytest tests/test_ai/ -v

# With coverage
pytest --cov=src --cov-report=html
```

## Common Tasks

### Add a Validation Rule
1. Create new rule in `src/validator/rules.py` (subclass `ValidationRule`)
2. Add to `Validator.validate_product()` or `validate_variation()`
3. Add test in `tests/test_validator/`

### Add an Excel Field
1. Update `src/excel_parser/reader.py` to parse the column
2. Add field to Pydantic model in `src/excel_parser/models.py`
3. Update `Excel_Data_Dictionary.md`
4. Add mapping in `WooCommerceClient._map_product_to_payload()`

### Extend AI Prompts
Modify `src/ai/client.py` methods: `generate_seo_title()`, `generate_seo_description()`, etc.

## Security Notes
- **Never commit `.env`** - gitignored
- Rotate WooCommerce keys if exposed: WC → Settings → Advanced → REST API
- OpenAI key in `.env` only
- Input validation via Pydantic + custom rules

## Known Limitations
- Synchronous/blocking (no async/await)
- Scheduler uses `time.sleep()` (dev only)
- No horizontal scaling / queue
- Excel-only input (no CSV/DB/API sources)
- Image Manager expects Excel IDs but WC returns numeric IDs (bug M4)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: src" | Run from project root, not src/ |
| Duplicate products | Ensure `upsert_product()` is used (not `create_product`) |
| Validation fails | Check `output/reports/validation_errors.xlsx` |
| Images not attaching | Verify image URLs use `/uploads/...` format |
| OpenAI errors | Check API key, quota, model name in `.env` |

## File Structure
```
project-root/
├── .env                    # secrets (gitignored)
├── .env.example            # template
├── config/
│   ├── settings.yaml       # template with ${VAR} placeholders
│   └── logging.yaml        # logging config
├── input/
│   └── Product_Master.xlsx # source data
├── output/                 # generated (gitignored)
│   ├── logs/
│   ├── reports/
│   └── image_cache/
├── src/
│   ├── main.py             # entry point
│   ├── ai/
│   ├── automation/
│   ├── excel_parser/
│   ├── image_manager/
│   ├── reporter/
│   ├── utils/
│   ├── validator/
│   └── woocommerce/
├── tests/                  # pytest unit tests
├── scripts/                # utility scripts
└── docs/                   # documentation
```