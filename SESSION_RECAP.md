# AI-Powered WooCommerce Product Automation System - Session Recap & Continuation Guide

## Project Overview
This is a Python 3.10+ system that automates WooCommerce product imports:
- **Input**: CSV/Excel file with product data (Persian/English)
- **Process**: CSV → XLSX → Pydantic models → AI SEO enrichment → WooCommerce REST API
- **Output**: Products with variations, images, categories, attributes, tags

**Run command**: `python -m src.main` (from project root)

---

## Current State (As of Last Commit)

### ✅ Fixed Issues
1. **CSV→XLSX auto-conversion** - `scripts/restructure_excel.py` runs on first run
2. **Local image handling** - Images copied from `input/images/` to cache, no URL downloads
3. **Image upload** - Uses WordPress REST API `/wp-json/wp/v2/media` with Application Passwords
4. **Variation sync on update** - `update_product()` now creates/updates/deletes variations
5. **Category resolution** - Finds/creates WC categories by name, uses IDs
6. **Tag support** - Uses `sale_tag` as tag, resolves/creates tags
7. **Variable product stock** - Parent product: `manage_stock=false`, variations handle stock
8. **MIME type detection** - Upload detects PNG/JPEG/WEBP/GIF from file signatures
9. **Extension preservation** - Variation images saved with `.webp` extension
10. **Attribute variation filtering** - Only attributes used in variations get `"variation": true`

### ⚠️ Known Issues (Not Yet Fixed)
1. **Image attachment mode** - Currently attaches all images to variations; needs "featured + gallery" mode
2. **Attribute labels** - Uses English keys (e.g., "color") instead of Persian names (e.g., "رنگ")
3. **Existing WC attributes** - Creates new attributes instead of reusing existing ones
3. **Color swatches** - Imported products show dropdown instead of color swatches
4. **Image re-upload** - Re-uploads images on every product update
5. **FTP image upload** - Not implemented (low priority)

---

## Project Structure
```
AI-Powered-WooCommerce-Product-Automation-System/
├── config/
│   └── settings.yaml          # Template with ${ENV_VAR:-default} placeholders
├── input/
│   ├── Product_Master.csv     # Source CSV (33 products, 131 variations)
│   └── images/                # Local images folder
├── output/
│   ├── Product_Master.xlsx    # Generated XLSX (gitignored)
│   └── image_cache/           # Cached images
├── scripts/
│   └── restructure_excel.py   # CSV→XLSX converter
├── src/
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── ai/                    # OpenAI SEO enrichment
│   ├── automation/            # BatchImporter, ProgressTracker
│   ├── excel_parser/          # Reader, models (Product, Variation, etc.)
│   ├── image_manager/         # Downloader, Uploader, Validator, Manager
│   ├── reporter/              # ValidationReporter
│   ├── utils/                 # Credentials, Logger, RateLimiter
│   ├── validator/             # Validation rules
│   └── woocommerce/           # WC REST API client
├── tests/                     # 46 unit tests (all passing)
├── .env                       # Actual credentials (gitignored)
├── .env.example               # Template
├── pyproject.toml             # Package config
├── requirements.txt           # Dependencies
└── docs/                      # DEVELOPMENT_GUIDE.md, QUICK_START.md
```

---

## Key Configuration (.env)
```bash
# WooCommerce
WOOCOMMERCE_API_URL=https://luxbaz.com
WOOCOMMERCE_CONSUMER_KEY=ck_xxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxx

# WordPress (for media uploads - REQUIRED)
WP_USER=admin
WP_APP_PASSWORD=<generate in WP Admin > Users > Application Passwords>

# OpenAI (optional)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# Paths
EXCEL_INPUT_PATH=input/Product_Master.csv
IMAGE_LOCAL_FOLDER=input/images
IMAGE_CACHE_DIR=output/image_cache
```

---

## Data Flow
1. **CSV Input** → `restructure_excel.py` → **XLSX** (5 sheets: Products, Variations, Categories, Attributes, Images)
2. **XLSX** → `ExcelReader.read_products()` → **List[Product]** (Pydantic models)
3. **Product** → `BatchImporter.import_products()` → `WooCommerceClient.upsert_product()`
4. **Product** → `_map_product_to_payload()` → WC REST API
5. **Images** → `ImageManager.process_product_images()` → Download → Validate → Upload → Attach

---

## Remaining Issues - Detailed Analysis

### Issue 1: Image Attachment Mode
**Current**: Each variation gets its own image
**Required**: 
- One featured image (`is_main=True`)
- Gallery = remaining images
- No variation images
- Config option: `gallery` (default) vs `variation`

**Files**: `manager.py`, `settings.yaml`, `main.py`

### Issue 2: Color Swatches vs Dropdown
**Root cause**: English attribute names sent to WC (e.g., "color") vs existing WC attributes using Persian names (e.g., "رنگ")
**Fix**: Issue 4 must be done first (use Persian names)

### Issue 3: Use Existing WC Attributes
**Current**: Creates new attributes/terms
**Required**: Fetch existing WC attributes at startup, match by Persian name, reuse term IDs
**Files**: `client.py` (add `resolve_attribute_ids()`, `resolve_term_ids()`), `reader.py`

### Issue 4: Incorrect Attribute Labels
**Current**: Uses English key from column name (`attribute:color` → "color")
**Required**: Use Persian name from `attribute_name:color` column ("رنگ")
**Files**: `reader.py` (parse `attribute_name:*`), `models.py` (store display_name), `client.py` (use display_name)

### Issue 5: FTP Image Upload (Low Priority)
**Approach**: Upload via FTP to `wp-content/uploads/YYYY/MM/`, then create WC media entries during import

### Issue 6: Avoid Re-uploading Images
**Current**: Re-uploads on every update
**Required**: Search WC media by filename, reuse existing media ID
**Cache**: `output/media_cache.json` mapping `{filename: media_id}`

---

## Implementation Priority Order
1. **Issue 4** - Attribute Labels (foundation for 2, 3)
2. **Issue 3** - Existing WC Attributes (depends on 4)
3. **Issue 2** - Color Swatches (depends on 3, 4)
4. **Issue 1** - Image Attachment Mode
5. **Issue 6** - Skip Re-upload
6. **Issue 5** - FTP Upload

---

## Critical Code References

### Attribute Parsing (reader.py:118-125)
```python
for col in df_products.columns:
    if col.startswith("attribute:"):
        attr_name = col.split(":")[1]  # English key
        attr_values = self._clean_attribute_value(row[col])
        if attr_values:
            attributes[attr_name] = attr_values
```
**Problem**: Doesn't read `attribute_name:*` for Persian display name

### Payload Mapping (client.py:374-377)
```python
"attributes": [
    {"name": attr_name, "options": attr_values, "visible": True, "variation": attr_name in variation_attr_names}
    for attr_name, attr_values in product.attributes.items()
],
```
**Problem**: Uses English key as `name` sent to WC

### Variation Sync (client.py:315-350)
```python
def _sync_variations(self, product_id: int, product: Product) -> list[int]:
    # Creates missing, updates existing, deletes stale variations
```

### Image Upload (uploader.py:24-75)
- Uses `mimetypes.guess_type()` + file signature sniffing
- Auth: WP Application Passwords (not WC consumer keys)

---

## Tests
```bash
python -m pytest tests/ -v
# 46 tests passing
```

---

## How to Continue in Another AI Session

### Starting Context
```bash
cd E:\Luxbaz\All Codes\Projects\AI-Powered-WooCommerce-Product-Automation-System
python -m src.main --test-sku 5718
```

### Next Steps (in order)
1. **Fix Issue 4**: Update `reader.py` to parse `attribute_name:*` columns, update `models.py` and `client.py`
2. **Fix Issue 3**: Add attribute/term resolution in `client.py`, use existing WC attributes
3. **Fix Issue 1**: Add `attachment_mode` config, update `ImageManager`
4. **Fix Issue 6**: Add media cache, check before upload

### Key Files to Modify First
1. `src/excel_parser/reader.py` - Parse Persian attribute names
2. `src/excel_parser/models.py` - Store display_name in Product attributes
3. `src/woocommerce/client.py` - Use display_name in payload, add attribute resolution

---

## References
- WooCommerce Export: `wc-product-export-23-7-2026-1784805085252.csv` (shows WC attribute structure)
- WC Attributes: `attributes.xlsx` (existing attributes with terms)
- Input CSV: `input/Product_Master.csv` (has `attribute:*` and `attribute_name:*` columns)

---

## Notes for Next AI
- **Don't break existing tests** - run `pytest tests/` after each change
- **Commit after each issue** - one issue = one commit
- **Use Persian attribute names** when sending to WC API
- **WP Application Passwords required** for media uploads (not WC keys)
- **Variable products**: parent has `manage_stock=false`, variations have stock