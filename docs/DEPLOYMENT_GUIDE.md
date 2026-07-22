# Deployment Guide

## Prerequisites
- Python 3.10+
- WooCommerce store with REST API enabled
- OpenAI API key (for AI features)
- WordPress media write permissions

## Quick Start (Development)

```bash
# 1. Clone
git clone https://github.com/jlshoja/AI-Powered-WooCommerce-Product-Automation-System.git
cd AI-Powered-WooCommerce-Product-Automation-System

# 2. Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install
pip install -e ".[dev]"

# 4. Configure
cp .env.example .env
# Edit .env with your credentials

# 5. Prepare Excel
# Place Product_Master.xlsx in input/

# 6. Run
cd src
python main.py
```

## Configuration

### Required Environment Variables
```bash
# .env
WOOCOMMERCE_API_URL=https://your-store.com/wp-json/wc/v3
WOOCOMMERCE_CONSUMER_KEY=ck_xxxxxxxxxxxxxxxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
EXCEL_INPUT_PATH=/path/to/Product_Master.xlsx
OUTPUT_DIR=../output
```

### Optional
```bash
WOOCOMMERCE_TIMEOUT=30
WOOCOMMERCE_MAX_RETRIES=3
VALIDATION_MIN_PRICE=1000
VALIDATION_MAX_PRICE=10000000
IMAGE_CACHE_DIR=../output/image_cache
IMAGE_MAX_SIZE_MB=2
IMAGE_ALLOWED_FORMATS=JPEG,PNG,WEBP
```

## WooCommerce Setup

1. **Enable REST API**
   - WP Admin → WooCommerce → Settings → Advanced → REST API
   - "Enable the REST API" ✓

2. **Create API Keys**
   - "Add Key" → Description: "Product Automation"
   - User: admin (or dedicated user)
   - Permissions: **Read/Write**
   - Copy Consumer Key & Secret → `.env`

3. **Verify Permissions**
   - Products: create, read, update, delete
   - Variations: create, read, update, delete
   - Media: create (upload images)

## OpenAI Setup

1. Get API key: https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. Set model: `OPENAI_MODEL=gpt-4o-mini` (or `gpt-4o`)

## Excel Preparation

### Required Sheets
| Sheet | Required Columns |
|-------|------------------|
| Products | ID, post_title, sku, regular_price, post_status, stock_status, categories, images, attribute:* |
| Variations | ID, post_title, post_status, sku, parent_sku, regular_price, stock_status, attribute:* |
| Categories | ID, name, parent_category |
| Attributes | ID, name, values (pipe-separated) |
| Images | ID, product_sku, image_url, alt_text, title, is_main |

### Column Format
- **Categories:** `Parent > Child > Grandchild`
- **Attributes:** `attribute:Color` column with `Red|Blue|Green`
- **Images:** Relative paths `/uploads/2026/07/image.webp`
- **Variations:** Link to parent via `parent_sku`

## Production Deployment

### Option 1: Cron Job (Linux)
```bash
# /etc/cron.d/woocommerce-import
# Run daily at 2 AM
0 2 * * * www-data cd /opt/wc-automation && .venv/bin/python src/main.py >> /var/log/wc-import.log 2>&1
```

### Option 2: Systemd Service
```ini
# /etc/systemd/system/wc-import.service
[Unit]
Description=WooCommerce Product Import
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/wc-automation
ExecStart=/opt/wc-automation/.venv/bin/python src/main.py
User=www-data
EnvironmentFile=/opt/wc-automation/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Timer for daily runs
# /etc/systemd/system/wc-import.timer
[Unit]
Description=Daily WC Import

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl daemon-reload
systemctl enable --now wc-import.timer
```

### Option 3: Docker
```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install -e ".[dev]"
COPY . .
CMD ["python", "src/main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  wc-import:
    build: .
    env_file: .env
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    # Run once and exit, or use cron inside container
```

### Option 4: Kubernetes CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: wc-product-import
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: importer
            image: your-registry/wc-automation:latest
            envFrom:
            - secretRef:
                name: wc-secrets
            volumeMounts:
            - name: input
              mountPath: /app/input
            - name: output
              mountPath: /app/output
          restartPolicy: OnFailure
          volumes:
          - name: input
            persistentVolumeClaim:
              claimName: wc-input-pvc
          - name: output
            persistentVolumeClaim:
              claimName: wc-output-pvc
```

## Monitoring

### Logs
```bash
# Structured logs (when JSON logging enabled)
tail -f output/logs/system.log | jq .

# Key metrics to watch
grep -c "successfully imported" output/logs/system.log
grep -c "Failed to create" output/logs/system.log
grep "Rollback completed" output/logs/system.log
```

### Reports
```bash
# Import report
cat output/reports/import_report.xlsx

# Validation errors
cat output/reports/validation_errors.xlsx
```

### Health Check
```bash
# Test WC connection
cd src && python -c "
from woocommerce.client import WooCommerceClient
import os
from dotenv import load_dotenv
load_dotenv()
c = WooCommerceClient(os.getenv('WOOCOMMERCE_API_URL'), os.getenv('WOOCOMMERCE_CONSUMER_KEY'), os.getenv('WOOCOMMERCE_CONSUMER_SECRET'))
print('Connected:', c.test_connection())
"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Check Consumer Key/Secret, ensure Read/Write perms |
| `429 Rate Limited` | Reduce batch size, add delay, implement token bucket |
| Images not attaching | Ensure URLs are `/uploads/...`, WC IDs are numeric |
| Duplicate products | Use `upsert_product()` (default in v0.1+) |
| AI timeout | Increase `WOOCOMMERCE_TIMEOUT`, check OpenAI quota |
| Excel not found | Verify `EXCEL_INPUT_PATH` in `.env` |
| ModuleNotFoundError | Run from project root, not `src/` |

## Rollback Procedure

1. **Stop cron/timer:** `systemctl stop wc-import.timer`
2. **Restore Excel:** Use backup from `output/reports/import_report_YYYY-MM-DD.xlsx`
3. **Manual cleanup:** Delete products via WC admin or API
4. **Re-run:** Fix issue, test, re-enable timer

## Backup Strategy

| Artifact | Frequency | Retention |
|----------|-----------|-----------|
| `.env` | On change | Manual |
| Excel input | Before each run | 30 days |
| Import reports | Each run | 90 days |
| WC products | WC backup plugin | Daily |
| Database | WP backup | Daily |

## Scaling Considerations

- **Batch size:** Default 10, tune based on WC/API limits
- **Concurrency:** Single-threaded; for scale, use async (H7) + queue
- **Memory:** Large Excel → stream with `openpyxl` read-only mode
- **Images:** Cache in `output/image_cache/`, cleanup periodically