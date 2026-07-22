@echo off
title WooCommerce Product Automation System
cd /d "%~dp0"

echo ============================================
echo  WooCommerce Product Automation System
echo ============================================
echo.

echo [1] Full import (all products)
echo [2] Test single product (by SKU)
echo [3] Dry run (validate only)
echo [4] Restructure CSV to XLSX
echo [5] Run tests
echo.
set /p choice="Select option (1-5): "

if "%choice%"=="1" (
    echo.
    echo Running full import...
    python -m src.main
) else if "%choice%"=="2" (
    echo.
    set /p sku="Enter product SKU: "
    python -m src.main --test-sku %sku%
) else if "%choice%"=="3" (
    echo.
    echo Running dry run...
    python -m src.main --dry-run
) else if "%choice%"=="4" (
    echo.
    echo Restructuring CSV to XLSX...
    python scripts/restructure_excel.py
) else if "%choice%"=="5" (
    echo.
    echo Running tests...
    python -m pytest tests/ -v
) else (
    echo Invalid option
)

echo.
echo Press any key to exit...
pause >nul
