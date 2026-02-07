"""
PDF parser for extracting financial data from PDF files.
Handles Balance Sheets, Credit Reports, and other financial documents.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("pdf_parser")

# Try to import PyPDF2
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not installed. Run: pip install PyPDF2")


class PDFParser:
    """
    Parses PDF files to extract financial and company data.
    """

    def __init__(self):
        """Initialize the PDF parser."""
        if not PYPDF2_AVAILABLE:
            logger.warning("PDFParser initialized but PyPDF2 not available")

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PDF file and extract relevant data.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary with extracted data
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Cannot parse PDF: PyPDF2 not available")
            return {}

        logger.info(f"Parsing PDF: {file_path}")

        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                # Extract text from all pages
                text_content = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)

                full_text = "\n".join(text_content)

                # Determine document type and parse accordingly
                doc_type = self._detect_document_type(full_text, file_path)

                if doc_type == "balance_sheet":
                    return self._parse_balance_sheet(full_text)
                elif doc_type == "credit_report":
                    return self._parse_credit_report(full_text)
                elif doc_type == "annual_report":
                    return self._parse_annual_report(full_text)
                else:
                    return self._parse_generic(full_text)

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return {}

    def _detect_document_type(self, text: str, file_path: str) -> str:
        """Detect the type of financial document."""
        text_lower = text.lower()
        filename_lower = Path(file_path).stem.lower()

        if "balance sheet" in text_lower or "balance_sheet" in filename_lower:
            return "balance_sheet"
        elif "credit" in text_lower or "rating" in text_lower:
            return "credit_report"
        elif "annual report" in text_lower or "annual_report" in filename_lower:
            return "annual_report"
        else:
            return "generic"

    def _parse_balance_sheet(self, text: str) -> Dict[str, Any]:
        """Parse a balance sheet PDF."""
        data = {
            "document_type": "balance_sheet",
            "assets": {},
            "liabilities": {},
            "equity": {}
        }

        # Extract financial figures using regex patterns
        patterns = {
            "total_assets": r"total\s+assets[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
            "total_liabilities": r"total\s+liabilities[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
            "shareholders_equity": r"(?:shareholders?|stockholders?)\s+equity[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
            "current_assets": r"current\s+assets[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
            "current_liabilities": r"current\s+liabilities[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
            "cash": r"cash(?:\s+and\s+cash\s+equivalents)?[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    data[key] = float(value_str)
                except ValueError:
                    pass

        return data

    def _parse_credit_report(self, text: str) -> Dict[str, Any]:
        """Parse a credit report PDF."""
        data = {
            "document_type": "credit_report",
            "credit_rating": None,
            "rating_agency": None,
            "outlook": None
        }

        # Extract credit rating
        rating_patterns = [
            r"rating[:\s]+([A-D][+-]?\d*)",
            r"([A-D]{1,3}[+-]?)\s+rating",
            r"CRISIL\s+([A-D]{1,3}[+-]?)",
            r"ICRA\s+([A-D]{1,3}[+-]?)",
        ]

        for pattern in rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["credit_rating"] = match.group(1).upper()
                break

        # Extract outlook
        if "positive" in text.lower():
            data["outlook"] = "Positive"
        elif "negative" in text.lower():
            data["outlook"] = "Negative"
        elif "stable" in text.lower():
            data["outlook"] = "Stable"

        return data

    def _parse_annual_report(self, text: str) -> Dict[str, Any]:
        """Parse an annual report PDF."""
        data = {
            "document_type": "annual_report",
            "highlights": [],
            "financials": {}
        }

        # Extract revenue
        revenue_pattern = r"(?:revenue|turnover|sales)[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)\s*(?:crore|million|billion|cr|mn|bn)?"
        match = re.search(revenue_pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(",", "")
            try:
                data["financials"]["revenue"] = float(value_str)
            except ValueError:
                pass

        # Extract EBITDA
        ebitda_pattern = r"EBITDA[:\s]+[\$₹]?\s*([\d,]+(?:\.\d+)?)"
        match = re.search(ebitda_pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(",", "")
            try:
                data["financials"]["ebitda"] = float(value_str)
            except ValueError:
                pass

        return data

    def _parse_generic(self, text: str) -> Dict[str, Any]:
        """Parse a generic PDF document."""
        return {
            "document_type": "generic",
            "text_length": len(text),
            "text_preview": text[:500] if text else ""
        }

    def parse_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Parse all PDF files in a folder.

        Args:
            folder_path: Path to the folder

        Returns:
            List of parsed data from each PDF
        """
        results = []
        folder = Path(folder_path)

        for pdf_file in folder.glob("*.pdf"):
            data = self.parse_pdf(str(pdf_file))
            if data:
                data["source_file"] = str(pdf_file)
                results.append(data)

        return results


def get_pdf_parser() -> PDFParser:
    """Factory function to create a PDFParser."""
    return PDFParser()
