"""
Excel parser for extracting financial data from Excel files.
Handles Balance Sheets, Financial Statements, and structured data.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("excel_parser")

# Try to import openpyxl
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not installed. Run: pip install openpyxl")


class ExcelParser:
    """
    Parses Excel files to extract financial and company data.
    """

    def __init__(self):
        """Initialize the Excel parser."""
        if not OPENPYXL_AVAILABLE:
            logger.warning("ExcelParser initialized but openpyxl not available")

    def parse_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an Excel file and extract relevant data.

        Args:
            file_path: Path to the Excel file

        Returns:
            Dictionary with extracted data
        """
        if not OPENPYXL_AVAILABLE:
            logger.error("Cannot parse Excel: openpyxl not available")
            return {}

        logger.info(f"Parsing Excel: {file_path}")

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            data = {
                "source_file": file_path,
                "sheets": {},
                "financials": {}
            }

            # Process each sheet
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_data = self._parse_sheet(sheet, sheet_name)
                data["sheets"][sheet_name] = sheet_data

                # Extract financial data if this looks like a financial sheet
                if self._is_financial_sheet(sheet_name):
                    financials = self._extract_financials(sheet)
                    data["financials"].update(financials)

            workbook.close()
            return data

        except Exception as e:
            logger.error(f"Error parsing Excel {file_path}: {e}")
            return {}

    def _parse_sheet(self, sheet, sheet_name: str) -> Dict[str, Any]:
        """Parse a single worksheet."""
        data = {
            "name": sheet_name,
            "rows": sheet.max_row,
            "columns": sheet.max_column,
            "data": []
        }

        # Extract first 50 rows as sample data
        for row_idx, row in enumerate(sheet.iter_rows(max_row=50, values_only=True)):
            if any(cell is not None for cell in row):
                data["data"].append(list(row))

        return data

    def _is_financial_sheet(self, sheet_name: str) -> bool:
        """Check if sheet name indicates financial data."""
        financial_keywords = [
            "financials", "income", "balance", "cash flow",
            "revenue", "profit", "loss", "statement", "p&l"
        ]
        sheet_lower = sheet_name.lower()
        return any(keyword in sheet_lower for keyword in financial_keywords)

    def _extract_financials(self, sheet) -> Dict[str, Any]:
        """Extract financial metrics from a worksheet."""
        financials = {}

        # Search for common financial terms in first column
        financial_terms = {
            "revenue": ["revenue", "total revenue", "sales", "turnover", "income"],
            "ebitda": ["ebitda", "operating profit", "operating income"],
            "pat": ["pat", "net profit", "net income", "profit after tax"],
            "total_assets": ["total assets", "assets"],
            "total_liabilities": ["total liabilities", "liabilities"],
            "equity": ["equity", "shareholders equity", "net worth"]
        }

        for row in sheet.iter_rows(max_row=100, max_col=10, values_only=True):
            if not row or not row[0]:
                continue

            cell_value = str(row[0]).lower().strip()

            for metric, keywords in financial_terms.items():
                if any(keyword in cell_value for keyword in keywords):
                    # Look for numeric value in the same row
                    for cell in row[1:]:
                        if isinstance(cell, (int, float)) and cell > 0:
                            if metric not in financials:
                                financials[metric] = cell
                            break

        return financials

    def parse_financial_statement(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Parse a financial statement Excel file with multiple years of data.

        Args:
            file_path: Path to the Excel file

        Returns:
            Dictionary with yearly financial data
        """
        if not OPENPYXL_AVAILABLE:
            return {}

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            # Try to detect years from header row
            years = []
            yearly_data = {}

            # Find header row with years
            for row_idx, row in enumerate(sheet.iter_rows(max_row=10, values_only=True)):
                for cell in row:
                    if isinstance(cell, (int, float)) and 2015 <= cell <= 2030:
                        years.append(int(cell))
                    elif isinstance(cell, str):
                        # Try to extract year from string like "FY24" or "2024"
                        import re
                        match = re.search(r"(?:FY)?(\d{2,4})", cell)
                        if match:
                            year = int(match.group(1))
                            if year < 100:
                                year += 2000
                            if 2015 <= year <= 2030:
                                years.append(year)

                if years:
                    break

            # Initialize yearly data
            for year in years:
                yearly_data[year] = {}

            workbook.close()
            return {"years": years, "data": yearly_data}

        except Exception as e:
            logger.error(f"Error parsing financial statement {file_path}: {e}")
            return {}

    def parse_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Parse all Excel files in a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            List of parsed data from each Excel file
        """
        results = []
        folder = Path(folder_path)

        for excel_file in folder.glob("*.xlsx"):
            data = self.parse_excel(str(excel_file))
            if data:
                results.append(data)

        for excel_file in folder.glob("*.xls"):
            data = self.parse_excel(str(excel_file))
            if data:
                results.append(data)

        return results


def get_excel_parser() -> ExcelParser:
    """Factory function to create an ExcelParser."""
    return ExcelParser()
