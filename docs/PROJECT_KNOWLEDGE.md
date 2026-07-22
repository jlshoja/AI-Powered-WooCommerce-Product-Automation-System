# AI-Powered WooCommerce Product Automation System - PROJECT_KNOWLEDGE.md

> **Authoritative project knowledge source** for future AI assistants and developers.
> Generated from comprehensive codebase analysis (2026-07-22).

---

## 1. Project Overview

### Problem Solved
Automates the manual process of importing products from Excel spreadsheets into WooCommerce, including:
- Product creation/update (simple + variable with variations)
- AI-generated SEO content (titles, descriptions, tags, categories)
- Data validation and error reporting
- Image download, validation, upload, and attachment
- Progress tracking and reporting

### Main Purpose
Eliminate manual product entry for Persian-language WooCommerce stores by automating the full pipeline from Excel → WooCommerce with AI enhancement.

### Target Users
- E-commerce managers with Persian-language WooCommerce stores
- Developers maintaining product catalogs
- Teams doing bulk product imports

### High-Level Workflow
```
Excel (Product_Master.xlsx) → ExcelReader → Pydantic Models → Validator 
  → (AIManager) → WooCommerceClient (upsert) 
  → ImageManager (download→validate→upload→attach) 
  → ProgressTracker → Reports
```

---

## 2. Architecture Overview

### System Architecture
```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Excel Input    │────▶│ Excel Parser │────▶│  Pydantic Models │
│  (5 sheets)     │     │  (pandas)    │     │ (Product, Var,   │
└─────────────────┘     └──────────────┘     │  Category, Attr) │
                                             └────────┬─────────┘
                                                      │
                        ┌─────────────────────────────┼─────────────────────────────┐
                        ▼                             ▼                             ▼
                   ┌────────────┐              ┌──────────────┐              ┌──────────────┐
                   │  Validator │              │  AI Manager  │              │ Image Manager│
                   │ (rules)    │              │ (OpenAI)     │              │ (download,   │
                   └─────┬──────┘              └──────┬───────┘              │ validate,    │
                       │                             │                     │ upload, attach)│
                       ▼                             ▼                     └──────┬───────┘
                   ┌─────────────────────────────────▼───────────────────────────▼──────┐
                   │                    Batch Importer (orchestrator)                   │
                   │  - Validate → AI → WC upsert → Images → Track → Report            │
                   └────────────────────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
                                             ┌──────────────┐
                                             │ WooCommerce  │
                                             │ REST API     │
                                             │ (WC Client)  │
                                             └──────────────┘
```

### Main Components & Responsibilities

| Module | Path | Responsibility |
|--------|------|----------------|
| **Excel Parser** | `src/excel_parser/` | Read Products, Variations, Categories, Attributes, Images sheets → Pydantic models |
| **Validator** | `src/validator/` | Required fields, SKU uniqueness, price ranges, stock, images, categories, attributes |
| **WooCommerce Client** | `src/woocommerce/client.py` | REST API wrapper: auth, retry logic, CRUD for products/variations, SKU lookup, upsert, rollback |
| **Image Manager** | `src/image_manager/` | Download → validate → upload to WP media → attach to products/variations |
| **AI Processing** | `src/ai/` | OpenAI integration: SEO titles, descriptions, product descriptions, tags, category suggestions |
| **Automation** | `src/automation/` | Batch import, progress tracking, scheduling, incremental imports |
| **Reporter** | `src/reporter/` | Excel validation/import reports |

### Key Design Patterns
- **Dependency Injection**: `BatchImporter` receives all services → testable
- **Pydantic Models**: Contracts between layers (Product, Variation, ProductImage, Category, Attribute)
- **Retry Logic**: `_retry_request()` with exponential backoff in WC client
- **Idempotency**: `upsert_product()` checks SKU → update or create
- **Compensating Transactions**: `rollback_product_creation()` deletes variations + product on failure

### External Integrations
- **WooCommerce REST API** (Consumer Key/Secret auth)
- **OpenAI API** (Chat Completions for SEO content)
- **WordPress Media Library** (image upload via WC media endpoint)

---

## 3. Directory Structure

```
project-root/
├── .env                          # Secrets (gitignored)
├── .env.example                  # Template for .env
├── .gitignore
├── pyproject.toml                # Build, deps, tools config (ruff, mypy, pytest)
├── requirements.txt              # Legacy deps (use pyproject.toml)
├── README.md
├── CHANGELOG.md
├── PROJECT_KNOWLEDGE.md          # This file
├── DEVELOPMENT_GUIDE.md
├── DEPLOYMENT_GUIDE.md
├── TESTING_STRATEGY.md
├── SECURITY.md
├── config/
│   ├── settings.yaml             # Template with ${ENV_VAR} placeholders
│   ├── logging.yaml              # Logging config
│   └── .gitignore                # Ignores settings.yaml
├── input/
│   ├── Product_Master_Input.csv  # Raw input (CSV)
│   ├── Product_Master.xlsx       # Generated by restructure script
│   └── images/                   # Local images folder (1814 files)
├── output/                       # Generated (gitignored)
│   ├── logs/
│   ├── reports/
│   └── image_cache/
├── scripts/
│   ├── excel_restructure.py      # Legacy restructure script
│   └── restructure_excel.py      # Current restructure script
├── src/
│   ├── main.py                   # Entry point
│   ├── ai/
│   │   ├── client.py             # OpenAI API wrapper
│   │   └── manager.py            # Orchestrates AI per product
│   ├── automation/
│   │   ├── importer.py           # BatchImporter (main pipeline)
│   │   ├── scheduler.py          # Scheduler (time.sleep - dev only)
│   │   └── tracker.py            # ProgressTracker
│   ├── excel_parser/
│   │   ├── models.py             # Pydantic models (Product, Variation, etc.)
│   │   └── reader.py             # ExcelReader (pandas)
│   ├── image_manager/
│   │   ├── downloader.py         # HTTP download + local copy
│   │   ├── manager.py            # Orchestrator
│   │   ├── uploader.py           # WP media upload + attach
│   │   └── validator.py          # PIL format/size validation
│   ├── reporter/
│   │   └── exporter.py           # ValidationReporter (Excel)
│   ├── utils/
│   │   └── logger.py             # Logger wrapper (stdlib)
│   ├── validator/
│   │   ├── rules.py              # ValidationRule subclasses
│   │   ├── reporter.py           # ValidationReporter
│   │   └── validator.py          # Validator orchestrator
│   └── woocommerce/
│       └── client.py             # WooCommerceClient (API wrapper)
├── tests/                        # pytest unit tests (46 tests)
│   ├── test_ai/
│   ├── test_automation/
│   ├── test_excel_parser/
│   ├── test_image_manager/
│   ├── test_validator/
│   └── test_woocommerce/
└── docs/                         # Documentation
    ├── Architecture.md
    ├── Excel_Data_Dictionary.md
    ├── WooCommerce_API.md
    ├── AUDIT_REPORT.md
```

---

## 4. Entry Points

### Main Executable
- **`src/main.py`** - Primary entry point
  - Loads settings from `config/settings.yaml` + `.env`
  - Initializes all modules (WC Client, Image Manager, AI Manager, Validator, BatchImporter)
  - Reads products from Excel via `ExcelReader`
  - Calls `BatchImporter.import_products(products)`

### Startup Scripts
- **`cd src && python main.py`** - Standard execution
- **Dry-run** (planned): `python main.py --dry-run`

### Scheduled Jobs
- **`src/automation/scheduler.py`** - `Scheduler` class
  - `schedule_import(products, schedule_time)` - Uses `time.sleep()` (dev only)
  - `incremental_import(products, last_import_time)` - Filters by `product.id` timestamp
  - **Note**: Uses blocking `time.sleep()` - not production-ready

---

## 5. Core Modules

### 5.1 Excel Parser (`src/excel_parser/`)

**Models** (`models.py`): Pydantic models
- `Product` - Parent product with variations, images, attributes, SEO fields
- `Variation` - Child product linked via `parent_sku`
- `ProductImage` - Image metadata (URL, local_filename, alt, title, is_main)
- `Category`, `Attribute` - Taxonomy models

**Reader** (`reader.py`): `ExcelReader` class
- Parses 5 sheets: Products, Variations, Categories, Attributes, Images
- Uses pandas `ExcelFile.parse()`
- Handles NaN → None, type coercion, pipe-separated values
- Extracts `local_image` / `local_gallery_images` for local image support

### 5.2 Validator (`src/validator/`)

**Rules** (`rules.py`): ValidationRule subclasses
- `RequiredFieldRule` - Non-empty fields
- `UniqueSKURule` - SKU uniqueness across products + variations
- `PriceRangeRule` - Min/max price bounds
- `StockQuantityRule` - Non-negative stock
- `ImageValidationRule` - URL must contain `/uploads/`
- `CategoryValidationRule` - At least one category
- `AttributeValidationRule` - At least one attribute

**Validator** (`validator.py`): Orchestrator
- Tracks SKUs across products + variations
- Returns `ValidationReport` with errors/warnings
- Generates Excel report via `ValidationReporter`

### 5.3 WooCommerce Client (`src/woocommerce/client.py`)

**`WooCommerceClient`** - REST API wrapper
- Auth: Consumer Key/Secret via `woocommerce` Python package
- Retry logic: `_retry_request()` with 3 attempts, exponential backoff
- **Key Methods**:
  - `upsert_product(product)` - SKU lookup → update or create
  - `create_product(product, track_for_rollback)` - Creates product + variations
  - `update_product(product_id, product)` - PUT by ID
  - `get_product_by_sku(sku)` - Search by SKU
  - `create_variation(product_id, variation)` - POST variation
  - `delete_product/delete_variation` - DELETE with force=true
  - `rollback_product_creation(product_id, variation_ids)` - Compensating transaction
  - `_map_product_to_payload()` - Pydantic → WC JSON
  - `_map_variation_to_payload()` - Pydantic → WC JSON

### 5.4 Image Manager (`src/image_manager/`)

**Downloader** (`downloader.py`): `ImageDownloader`
- Local-first: checks `local_images_dir` for `local_filename` → `shutil.copy2()`
- Fallback: HTTP download via `requests` (30s timeout, streaming)
- Caches to `cache_dir` (`../output/image_cache`)

**Validator** (`validator.py`): `ImageValidator`
- PIL-based: checks file size (≤2MB) and format (JPEG/PNG/WEBP)

**Uploader** (`uploader.py`): `ImageUploader`
- Multipart upload to WC media endpoint
- Attaches to product (`position=0` main, `1` gallery) or variation

**Manager** (`manager.py`): `ImageManager` orchestrator
- Processes main image, gallery images, variation images
- Uses `local_filename` from `ProductImage` for local lookup

### 5.5 AI Processing (`src/ai/`)

**Client** (`client.py`): `AIClient` - OpenAI wrapper
- Methods: `generate_seo_title`, `generate_seo_description`, `generate_product_description`, `generate_tags`, `suggest_categories`
- Persian prompts, token limits per type

**Manager** (`manager.py`): `AIManager`
- `process_product(product)` - Fills missing SEO fields, description, tags, categories
- Only generates if field is empty/None

### 5.6 Automation (`src/automation/`)

**BatchImporter** (`importer.py`): Main pipeline
- Validates → AI process → WC upsert → Image processing → Track → Report
- Batch size configurable (default 10)
- Uses `upsert_product()` for idempotency

**ProgressTracker** (`tracker.py`): Tracks success/failure
- Generates `import_report.xlsx` with SKU, name, status, error

**Scheduler** (`scheduler.py`): Time-based & incremental
- `schedule_import()` - blocking sleep
- `incremental_import()` - Filters by `product.id` timestamp parsing

### 5.7 Reporter (`src/reporter/exporter.py`)

**ValidationReporter**: Generates `validation_errors.xlsx` from `ValidationReport`

---

## 6. Data Flow Analysis

### Data Sources
1. **Excel Input** (`input/Product_Master.xlsx`) - 5 sheets
2. **Local Images** (`input/images/`) - 1814 .webp files
3. **Environment Variables** (`.env`) - Credentials
4. **OpenAI API** - SEO content generation

### Data Transformations
```
Excel (raw) → pandas DataFrame → Pydantic Models (typed)
  → Validation (rules) → AI enrichment (optional)
  → WC Payload Mapping → REST API calls
  → Image Processing (local copy → cache → WP upload → attach)
  → Progress Tracking → Excel Reports
```

### Intermediate Outputs
- `output/image_cache/` - Downloaded/copied images
- `output/logs/*.log` - Module-specific logs
- `output/reports/validation_errors.xlsx` - Validation failures
- `output/reports/import_report.xlsx` - Import success/failure

### Final Outputs
- Products/Variations in WooCommerce
- Images in WordPress Media Library
- Reports in `output/reports/`

---

## 7. Configuration System

### Environment Variables (`.env`)
| Variable | Description | Default |
|----------|-------------|---------|
| `WOOCOMMERCE_API_URL` | WC REST endpoint | Required |
| `WOOCOMMERCE_CONSUMER_KEY` | WC API key | Required |
| `WOOCOMMERCE_CONSUMER_SECRET` | WC API secret | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required for AI |
| `OPENAI_MODEL` | Model name | `gpt-4o-mini` |
| `EXCEL_INPUT_PATH` | Path to Excel | `../input/Product_Master.xlsx` |
| `OUTPUT_DIR` | Output directory | `../output` |
| `VALIDATION_MIN_PRICE` | Min price | 1000 |
| `VALIDATION_MAX_PRICE` | Max price | 10000000 |
| `IMAGE_CACHE_DIR` | Image cache | `../output/image_cache` |
| `IMAGE_MAX_SIZE_MB` | Max image size | 2 |
| `IMAGE_ALLOWED_FORMATS` | Allowed formats | JPEG,PNG,WEBP |

### Settings File (`config/settings.yaml`)
Uses `${ENV_VAR}` placeholders resolved in `main.py:load_settings()`:
```yaml
woocommerce:
  api_url: "${WOOCOMMERCE_API_URL}"
  consumer_key: "${WOOCOMMERCE_CONSUMER_KEY}"
  consumer_secret: "${WOOCOMMERCE_CONSUMER_SECRET}"
  timeout: 30
  max_retries: 3
excel:
  input_path: "${EXCEL_INPUT_PATH}"
  output_dir: "${OUTPUT_DIR}"
validation:
  min_price: 1000
  max_price: 10000000
  required_fields: ["sku", "post_title", "regular_price"]
ai:
  api_key: "${OPENAI_API_KEY}"
  model: "${OPENAI_MODEL:-gpt-4o-mini}"
image:
  cache_dir: "../output/image_cache"
  local_folder: "../input/images"
  max_size_mb: 2
  allowed_formats: ["JPEG", "PNG", "WEBP"]
```

### Logging Config (`config/logging.yaml`)
- DictConfig format
- Console + file handlers
- Output: `../output/logs/system.log`

---

## 8. Database and Storage

### WooCommerce (External)
- Products, Variations, Categories, Attributes, Media
- Managed via REST API

### Local File Storage
| Path | Purpose | Retention |
|------|---------|-----------|
| `input/images/` | Source images (1814 files) | Manual |
| `output/image_cache/` | Downloaded/copied images | Auto (reused) |
| `output/logs/` | Module logs | Manual cleanup |
| `output/reports/` | Excel reports | 90 days (per DEPLOYMENT_GUIDE) |
| `input/Product_Master.xlsx` | Generated Excel | Per run |

### Cache Behavior
- `ImageDownloader` checks cache first (`cache_path.exists()`)
- Local images copied to cache via `shutil.copy2()`
- HTTP downloads streamed to cache

---

## 9. External Services

### WooCommerce REST API
- **Endpoints**: `/wp-json/wc/v3/products`, `/products/{id}`, `/products/{id}/variations`, `/media`
- **Auth**: Consumer Key/Secret (Basic Auth via `woocommerce` package)
- **Permissions**: Products (CRUD), Variations (CRUD), Media (Create)
- **Rate Limiting**: Not implemented (risk: 429 errors)

### OpenAI API
- **Endpoint**: Chat Completions (`/v1/chat/completions`)
- **Model**: `gpt-4o-mini` (configurable)
- **Usage**: 5 calls per product (SEO title, SEO desc, description, tags, categories)
- **Rate Limiting**: Not implemented (risk: 429 errors)

### WordPress Media Library
- Images uploaded via `/wp-json/wc/v3/media` (multipart)
- Attached via product/variation PUT with image IDs

---

## 10. Execution Workflows

### 10.1 Normal Execution
```
1. main.py loads settings (.env + settings.yaml)
2. Initialize: WCClient, ImageManager, AIManager, Validator, BatchImporter
3. ExcelReader.read_products() → List[Product]
4. BatchImporter.import_products(products):
   a. Validator.validate_products() → ValidationReport
   b. If errors: generate validation_errors.xlsx, STOP
   c. For each batch (size=10):
      i. For each product:
         - AIManager.process_product() [if AI enabled]
         - WCClient.upsert_product() → create or update
         - ImageManager.process_product_images() → download/validate/upload/attach
         - Tracker.track_success() or track_failure()
   d. Tracker.generate_report() → import_report.xlsx
5. Log completion
```

### 10.2 Resume Execution
- **Idempotency**: `upsert_product()` checks SKU → updates existing
- **Incremental Import**: `Scheduler.incremental_import()` filters by `product.id` timestamp
- **Reports**: `import_report.xlsx` tracks SKU + status for manual review

### 10.3 Error Handling
- **Validation Errors**: Stop entire import, generate `validation_errors.xlsx`
- **WC API Errors**: Retry 3x with backoff, then track_failure()
- **Image Errors**: Log warning, continue with other images
- **AI Errors**: Log error, continue with empty AI fields

### 10.4 Recovery Mechanisms
- **Rollback**: `WCClient.rollback_product_creation()` deletes variations + product
- **Manual Cleanup**: Use `import_report.xlsx` to identify failed SKUs
- **Re-run**: Fix data, re-run import (upsert handles duplicates)

---

## 11. State Management

### Progress Tracking
- **ProgressTracker** (in-memory): `imported_products[]`, `failed_products[]`
- **Report Generation**: `generate_report()` → `import_report.xlsx`

### State Files
| File | Purpose |
|------|---------|
| `output/reports/import_report.xlsx` | SKU, name, status, error |
| `output/reports/validation_errors.xlsx` | SKU, field, message |
| `output/logs/*.log` | Module-level logs |

### Checkpoints
- None implemented (no persistent checkpoint file)
- Resume relies on WC SKU lookup + Excel re-read

### Resume Behavior
- Re-run `main.py` → reads Excel fresh → upserts handle duplicates
- Failed products tracked in report for manual retry

---

## 12. Input and Output Inventory

### Input Files
| File | Format | Source | Required |
|------|--------|--------|----------|
| `input/Product_Master_Input.csv` | CSV | Manual | Yes |
| `input/Product_Master.xlsx` | Excel (5 sheets) | Generated | Yes (by reader) |
| `input/images/*.webp` | Image files | Manual copy | Optional (fallback to URL) |
| `.env` | Key-value | Manual | Yes |

### Generated Files
| File | Format | Purpose |
|------|--------|---------|
| `output/Product_Master.xlsx` | Excel (5 sheets) | Restructured for reader |
| `output/image_cache/*.webp` | Images | Cached for upload |
| `output/logs/*.log` | Text | Debugging |
| `output/reports/import_report.xlsx` | Excel | Import results |
| `output/reports/validation_errors.xlsx` | Excel | Validation failures |

### Temporary Files
- `output/image_cache/` - Reused across runs

### Final Outputs (External)
- WooCommerce Products/Variations
- WordPress Media Library images

---

## 13. Important Business Rules

### Validation Rules (Enforced)
1. **Required Fields**: `post_title`, `sku`, `regular_price`, `stock_status`
2. **SKU Uniqueness**: Across all products + variations
3. **Price Range**: 1,000 - 10,000,000 (configurable)
4. **Stock Quantity**: Non-negative
5. **Image URL Format**: Must contain `/uploads/` (dynamic WP path)
5. **Categories**: At least one required
6. **Attributes**: At least one required

### Processing Rules
1. **Upsert Behavior**: SKU exists → UPDATE, else CREATE
2. **Variation Linking**: `parent_sku` must match parent product SKU
3. **Image Attachment**: Main image position=0, gallery position=1+
4. **AI Generation**: Only fills empty fields (preserves existing)
7. **Batch Processing**: 10 products per batch (configurable)

### Pricing Rules
- Regular price required, sale price optional
- Prices stored as strings in WC payload
- Stock managed via `manage_stock` (yes/no)

### Image Rules
- Local-first: copy from `input/images/` if `local_filename` exists
- Fallback: HTTP download from `image_url`
- Validation: ≤2MB, JPEG/PNG/WEBP only
- WP upload via multipart, attach via product/variation PUT

---

## 14. Testing

### Current Coverage (46 tests)
| Module | Tests | Status |
|--------|-------|--------|
| AI Client/Manager | 7 | ✅ |
| Automation (BatchImporter, Scheduler, Tracker) | 5 | ✅ |
| Excel Parser (Reader) | 5 | ✅ |
| Image Manager | 7 | ✅ |
| Validator | 11 | ✅ |
| WooCommerce Client | 9 | ✅ |
| **Total** | **46** | ✅ |

### Test Structure
- **Files**: `tests/test_<module>/test_<component>.py`
- **Fixtures**: Module-level, minimal valid data
- **Mocking**: External APIs (WC, OpenAI, HTTP, file system)
- **Test Data**: Factory functions, inline Pydantic models

### Running Tests
```bash
# All
pytest -v

# Module
pytest tests/test_ai/ -v
pytest tests/test_woocommerce/test_client.py -v

# Coverage
pytest --cov=src --cov-report=html

# CI mode
pytest -x --strict-markers --strict-config
```

### Gaps (Planned)
- No integration tests (real WC, real OpenAI)
- No E2E tests
- No property-based testing (Hypothesis)
- No performance tests

---

## 15. Known Issues and Technical Debt

### Critical - FIXED ✅
| Issue | Location | Status |
|-------|----------|--------|
| No rate limiting | WC Client, AI Client | **FIXED** - Token bucket in `src/utils/rate_limiter.py` |
| No SSRF protection | ImageDownloader | **FIXED** - Private IP blocking in `downloader.py` |
| No HTML sanitization | AI output → WC | **FIXED** - Bleach sanitization in `AIClient` |
| Image ID mismatch | `ImageManager` uses Excel IDs | **FIXED** - Uses WC numeric IDs from upload response |

### High
| Issue | Location | Impact |
|-------|----------|--------|
| Blocking scheduler | `scheduler.py:28` | Not production-ready |
| No async/await | All I/O blocking | Scalability limited |
| No JSON logging | `logger.py` | Hard to parse in production |

### Medium
| Issue | Location | Impact |
|-------|----------|--------|
| Excel-only input | `ExcelReader` | Hard to add CSV/DB/API sources |
| Tight coupling | `BatchImporter` calls concrete classes | Hard to extend |
| No file rotation | `logging.yaml` | Disk space growth |
| Test file dependency | `TEST_EXCEL_PATH` | Fails if Excel missing |

### Code Smells
- `Scheduler` uses `time.sleep()` blocking
- `ProductImage.local_filename` optional but critical for local images
- `Variation.images` only uses first image (index 0)

---

## 16. Improvement Recommendations

### Critical (Do First) - ✅ COMPLETED
1. ~~**Rate Limiting**: Token bucket for WC API + OpenAI~~ → **DONE** (commit 9f365a8)
2. ~~**SSRF Protection**: Validate image URLs (block private IPs)~~ → **DONE** (commit 9f365a8)
3. ~~**HTML Sanitization**: Bleach on AI output before WC~~ → **DONE** (commit 9f365a8)
4. ~~**Fix Image IDs**: Use WC numeric IDs for attachment~~ → **DONE** (commit 9f365a8)

### High
5. **Replace Scheduler**: APScheduler or Celery
6. **Add `--dry-run`**: Validate + simulate without WC calls
7. **Structured JSON Logging**: `python-json-logger` + log rotation
8. **Async/Await**: `httpx` + `asyncio` for batch imports

### Medium
9. **Plugin Architecture**: Abstract storage (Excel → CSV, DB, API)
10. **Domain Events**: Decouple BatchImporter from concrete services
11. **Integration Tests**: Docker WC + test script
12. **Health Check CLI**: `python main.py --health-check`

### Low
13. **Dockerfile + docker-compose**
14. **Kubernetes CronJob manifests**
15. **Property-based testing** (Hypothesis)
16. **Mutation testing** (mutmut)

---

## 17. AI HANDOVER

### What the Project Does
Automates WooCommerce product imports from Excel with AI-powered SEO content generation, validation, image management, and progress tracking. Modular, typed, tested, and documented.

### Current Architecture
- **Modular monolith** with clear separation: Parser → Validator → AI → WC → Images → Tracker
- **Dependency injection** in `BatchImporter` enables testing
- **Pydantic models** as contracts between layers
- **Configuration** via `.env` + YAML with `${VAR}` placeholders
- **Security**: Rate limiting, SSRF protection, HTML sanitization ✅

### Important Files
| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, wiring |
| `src/woocommerce/client.py` | WC API + upsert + rollback |
| `src/excel_parser/reader.py` | Excel → Pydantic |
| `src/image_manager/downloader.py` | Local-first image fetch |
| `src/automation/importer.py` | Main pipeline |
| `config/settings.yaml` | Config template |
| `.env.example` | Secrets template |

### Important Workflows
1. **Import**: `cd src && python main.py`
2. **Test**: `pytest -v`
3. **Lint**: `ruff check src/ tests/`
4. **Type Check**: `mypy src/`
5. **Restructure Excel**: `python scripts/restructure_excel.py`

### Known Limitations
- **Synchronous/blocking** - no async/await
- **Scheduler is dev-only** - uses `time.sleep()`
- **No horizontal scaling** - single-threaded, no queue
- **Excel-only input** - no CSV/DB/API sources
- **No structured logging** - plain text logs

### How Future AIs Should Understand the Project
1. **Start with `README.md` + `docs/Architecture.md`**
2. **Read `PROJECT_KNOWLEDGE.md` (this file) for deep context**
3. **Trace from `main.py`** to understand wiring
4. **Check `CHANGELOG.md`** for recent changes
5. **Run tests first** (`pytest -v`) to verify environment
6. **When adding features**: Follow patterns in `DEVELOPMENT_GUIDE.md`
7. **When fixing bugs**: Check `SECURITY.md` for related concerns

---

## Remaining Activities for Next Session

### High Priority
1. **Replace Scheduler** - Integrate APScheduler or Celery
2. **Add `--dry-run` Flag** - Argument parsing in `main.py`
3. **Structured JSON Logging** - `python-json-logger` + rotation
4. **Async Image Download** - `httpx.AsyncClient` in `ImageDownloader`

### Medium-term (Month 1)
5. **Integration Tests** - Docker WC instance + test script
6. **Plugin Architecture** - Abstract `ExcelReader` for CSV/DB
7. **Domain Events** - Decouple `BatchImporter` from concrete services
8. **Dockerfile + CI/CD** - GitHub Actions workflow

### Documentation Updates Needed
- Update `DEVELOPMENT_GUIDE.md` with new patterns
- Document rate limiting config in `config/settings.yaml`
- Document SSRF protection in `SECURITY.md`

---

*Generated: 2026-07-22 | Based on codebase at commit 9f365a8 (fix/critical-security-and-runtime-issues)*
*This document is the authoritative knowledge source. Update it when architecture changes.*