# AI-Powered WooCommerce Product Automation System

## Overview
Automate WooCommerce product imports from Excel with **AI-generated SEO content**, **validation**, and **batch processing**.

## Features
- ✅ **Excel to WooCommerce**: Import products, variations, categories, and images.
- ✅ **AI-Powered SEO**: Generate titles, descriptions, tags, and category suggestions.
- ✅ **Validation**: Check for missing fields, duplicate SKUs, and invalid data.
- ✅ **Image Management**: Download, validate, and upload images to WordPress.
- ✅ **Batch Automation**: Schedule imports and track progress.

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `config/settings.yaml`**:
   - Add your WooCommerce API keys.
   - Add your OpenAI API key for AI processing.

3. **Prepare Input**:
   - Place your `Product_Master.xlsx` in `input/`.

4. **Run the System**:
   ```bash
   cd src
   python main.py
   ```

## Documentation
- [Architecture](docs/Architecture.md)
- [Excel Data Dictionary](docs/Excel_Data_Dictionary.md)
- [WooCommerce API](docs/WooCommerce_API.md)

## Outputs
- **Reports**: `output/reports/validation_report.xlsx`, `output/reports/import_report.xlsx`
- **Logs**: `output/logs/system.log`
- **Image Cache**: `output/image_cache/`