"""
Validation Reporter for the WooCommerce Product Automation System.

Generates Excel reports for validation errors.
"""

from pathlib import Path

from src.validator.validator import ValidationReport


class ValidationReporter:
    """Generates validation reports in Excel format."""

    def __init__(self, output_dir: Path = Path("../output")):
        """Initialize the ValidationReporter."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self, report: ValidationReport, filename: str = "validation_report.xlsx"
    ) -> Path:
        """Generate an Excel report from a ValidationReport."""
        file_path = self.output_dir / filename
        df = report.to_dataframe()
        if not df.empty:
            df.to_excel(file_path, index=False)
        return file_path
