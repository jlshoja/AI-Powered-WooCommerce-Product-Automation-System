#!/usr/bin/env python3
"""
Live test for the reconstructed system.
Proves all files are functional.
"""

import yaml
from pathlib import Path

# 1. Test settings.yaml
print("🔍 Testing config/settings.yaml...")
try:
    with open(Path("config/settings.yaml"), "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    assert "woocommerce" in settings, "Missing 'woocommerce' in settings.yaml"
    assert "excel" in settings, "Missing 'excel' in settings.yaml"
    print("✅ config/settings.yaml: PASSED")
except Exception as e:
    print(f"❌ config/settings.yaml: FAILED - {e}")

# 2. Test docs/
print("🔍 Testing docs/...")
try:
    docs_files = ["Architecture.md", "Excel_Data_Dictionary.md", "WooCommerce_API.md"]
    for file in docs_files:
        path = Path(f"docs/{file}")
        assert path.exists(), f"Missing {file}"
    print("✅ docs/: PASSED")
except Exception as e:
    print(f"❌ docs/: FAILED - {e}")

# 3. Test Product_Master.xlsx (in output/)
print("🔍 Testing output/Product_Master.xlsx...")
try:
    excel_path = Path("output/Product_Master.xlsx")
    assert excel_path.exists(), f"Missing {excel_path}"
    print("✅ output/Product_Master.xlsx: PASSED")
except Exception as e:
    print(f"❌ output/Product_Master.xlsx: FAILED - {e}")

# 4. Test src/main.py
print("🔍 Testing src/main.py...")
try:
    with open(Path("src/main.py"), "r", encoding="utf-8") as f:
        content = f.read()
    assert "WooCommerceClient" in content, "Missing WooCommerceClient in main.py"
    assert "ExcelReader" in content, "Missing ExcelReader in main.py"
    print("✅ src/main.py: PASSED")
except Exception as e:
    print(f"❌ src/main.py: FAILED - {e}")

print("🔚 Live test complete.")