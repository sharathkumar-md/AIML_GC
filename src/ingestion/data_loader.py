"""
Data loader module for loading company data from various sources.
Coordinates loading from OnePager files, PDFs, Excel files, and web scraping.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger, LogTimer
from models.company_data import CompanyData, Sector
from ingestion.markdown_parser import parse_onepager
from ingestion.pdf_parser import PDFParser
from ingestion.excel_parser import ExcelParser
from ingestion.web_scraper import WebScraper

logger = get_logger("data_loader")


class DataLoader:
    """
    Loads and aggregates company data from multiple sources.
    """

    def __init__(self, data_dir: str):
        """
        Initialize the data loader.

        Args:
            data_dir: Path to the Company Data directory
        """
        self.data_dir = Path(data_dir)
        self.companies: Dict[str, CompanyData] = {}

        logger.info(f"DataLoader initialized with data directory: {self.data_dir}")

    def load_company(self, company_folder: str) -> Optional[CompanyData]:
        """
        Load data for a single company from its folder.

        Args:
            company_folder: Name of the company folder (e.g., 'technology-ksolves')

        Returns:
            CompanyData object or None if loading fails
        """
        folder_path = self.data_dir / company_folder

        if not folder_path.exists():
            logger.error(f"Company folder not found: {folder_path}")
            return None

        logger.info(f"Loading company data from: {company_folder}")

        company_data = None

        # Find and parse OnePager.md
        onepager_files = list(folder_path.glob("*-OnePager.md"))
        if onepager_files:
            onepager_path = onepager_files[0]
            logger.debug(f"Parsing OnePager: {onepager_path.name}")

            try:
                company_data = parse_onepager(str(onepager_path))
                logger.info(f"Successfully parsed OnePager for: {company_data.name}")
            except Exception as e:
                logger.error(f"Failed to parse OnePager: {e}")
                return None
        else:
            logger.warning(f"No OnePager.md found in {company_folder}")
            return None

        # Use folder name prefix for sector classification (more reliable)
        sector_from_folder = self._extract_sector_from_folder(company_folder)
        if sector_from_folder != Sector.UNKNOWN:
            company_data.sector = sector_from_folder

        # Load additional data sources
        company_data = self._load_additional_sources(company_data, folder_path)

        # Store in cache
        self.companies[company_data.name] = company_data

        # Log summary
        self._log_company_summary(company_data)

        return company_data

    def _extract_sector_from_folder(self, folder_name: str) -> Sector:
        """
        Extract sector from folder name prefix.

        Folder names follow the pattern: sector-company (e.g., 'technology-ksolves')
        """
        folder_lower = folder_name.lower()
        sector_mapping = {
            'technology': Sector.TECHNOLOGY,
            'manufacturing': Sector.MANUFACTURING,
            'automotive': Sector.MANUFACTURING,  # Automotive is manufacturing
            'pharma': Sector.PHARMA,
            'logistics': Sector.LOGISTICS,
            'consumer': Sector.CONSUMER,
            'electronics': Sector.ELECTRONICS,
            'entertainment': Sector.ENTERTAINMENT,
        }

        for prefix, sector in sector_mapping.items():
            if folder_lower.startswith(prefix):
                return sector

        return Sector.UNKNOWN

    def _load_additional_sources(
        self,
        company: CompanyData,
        folder_path: Path
    ) -> CompanyData:
        """
        Load additional data from PDFs, Excel files, and web scraping.

        Args:
            company: Existing CompanyData object
            folder_path: Path to company folder

        Returns:
            Updated CompanyData object
        """
        # Parse PDF files
        pdf_files = list(folder_path.glob("*.pdf"))
        if pdf_files:
            logger.debug(f"Found {len(pdf_files)} PDF files")
            pdf_parser = PDFParser()
            for pdf_file in pdf_files:
                company.sources[f"pdf_{pdf_file.stem}"] = str(pdf_file)
                try:
                    pdf_data = pdf_parser.parse_pdf(str(pdf_file))
                    if pdf_data:
                        # Merge credit rating if found
                        if pdf_data.get("credit_rating"):
                            company.credit_ratings.append(pdf_data)
                        # Merge financial data if found
                        if pdf_data.get("financials"):
                            logger.debug(f"Extracted financials from PDF: {pdf_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to parse PDF {pdf_file.name}: {e}")

        # Parse Excel files
        excel_files = list(folder_path.glob("*.xlsx")) + list(folder_path.glob("*.xls"))
        if excel_files:
            logger.debug(f"Found {len(excel_files)} Excel files")
            excel_parser = ExcelParser()
            for excel_file in excel_files:
                company.sources[f"excel_{excel_file.stem}"] = str(excel_file)
                try:
                    excel_data = excel_parser.parse_excel(str(excel_file))
                    if excel_data and excel_data.get("financials"):
                        logger.debug(f"Extracted financials from Excel: {excel_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to parse Excel {excel_file.name}: {e}")

        # Web scraping for additional public data (if website is available)
        if company.website:
            try:
                scraper = WebScraper(timeout=5)
                web_data = scraper.scrape_company_website(company.website)
                if web_data:
                    company.sources["web_scrape"] = company.website
                    # Merge scraped data if useful
                    if web_data.get("description") and not company.business_description:
                        company.business_description = web_data["description"]
                    if web_data.get("products"):
                        for product in web_data["products"]:
                            if product not in company.products_services:
                                company.products_services.append(product)
            except Exception as e:
                logger.debug(f"Web scraping failed for {company.website}: {e}")

        return company

    def _log_company_summary(self, company: CompanyData) -> None:
        """Log a summary of loaded company data."""
        logger.info(f"  - Sector: {company.sector.value}")
        logger.info(f"  - Founded: {company.founded or 'N/A'}")
        logger.info(f"  - Employees: {company.employees or 'N/A'}")
        logger.info(f"  - Products/Services: {len(company.products_services)}")
        logger.info(f"  - Facilities: {len(company.facilities)}")
        logger.info(f"  - Certifications: {len(company.certifications)}")

        latest = company.get_latest_financials()
        if latest:
            logger.info(f"  - Latest Revenue ({latest.year}): {latest.revenue or 'N/A'}")

    def load_all_companies(self) -> Dict[str, CompanyData]:
        """
        Load all companies from the data directory.

        Returns:
            Dictionary mapping company names to CompanyData objects
        """
        with LogTimer("Loading all companies", "data_loader"):
            # Find all company folders
            company_folders = [
                f.name for f in self.data_dir.iterdir()
                if f.is_dir() and not f.name.startswith('.')
            ]

            logger.info(f"Found {len(company_folders)} company folders")

            for folder in company_folders:
                try:
                    self.load_company(folder)
                except Exception as e:
                    logger.error(f"Failed to load {folder}: {e}")

            logger.info(f"Successfully loaded {len(self.companies)} companies")

        return self.companies

    def get_company(self, name: str) -> Optional[CompanyData]:
        """
        Get a loaded company by name.

        Args:
            name: Company name

        Returns:
            CompanyData object or None
        """
        # Try exact match first
        if name in self.companies:
            return self.companies[name]

        # Try case-insensitive match
        name_lower = name.lower()
        for company_name, company_data in self.companies.items():
            if company_name.lower() == name_lower:
                return company_data

        # Try partial match
        for company_name, company_data in self.companies.items():
            if name_lower in company_name.lower():
                return company_data

        logger.warning(f"Company not found: {name}")
        return None

    def get_companies_by_sector(self, sector: Sector) -> List[CompanyData]:
        """
        Get all companies in a specific sector.

        Args:
            sector: Sector enum value

        Returns:
            List of CompanyData objects
        """
        return [
            company for company in self.companies.values()
            if company.sector == sector
        ]

    def list_companies(self) -> List[str]:
        """
        List all loaded company names.

        Returns:
            List of company names
        """
        return list(self.companies.keys())


def load_company_data(data_dir: str, company_folder: str) -> Optional[CompanyData]:
    """
    Convenience function to load a single company.

    Args:
        data_dir: Path to Company Data directory
        company_folder: Company folder name

    Returns:
        CompanyData object or None
    """
    loader = DataLoader(data_dir)
    return loader.load_company(company_folder)


def load_all_companies(data_dir: str) -> Dict[str, CompanyData]:
    """
    Convenience function to load all companies.

    Args:
        data_dir: Path to Company Data directory

    Returns:
        Dictionary of company data
    """
    loader = DataLoader(data_dir)
    return loader.load_all_companies()


if __name__ == "__main__":
    # Test the data loader
    import sys

    # Setup logger for testing
    from utils.logger import setup_logger
    setup_logger("data_loader", level=10)  # DEBUG level

    # Default data directory
    data_dir = Path(__file__).parent.parent.parent / "Company Data"

    if len(sys.argv) > 1:
        company_folder = sys.argv[1]
        company = load_company_data(str(data_dir), company_folder)
        if company:
            print(f"\n{'='*60}")
            print(f"Loaded: {company.name}")
            print(f"Sector: {company.sector.value}")
    else:
        # Load all companies
        companies = load_all_companies(str(data_dir))
        print(f"\n{'='*60}")
        print(f"Loaded {len(companies)} companies:")
        for name, data in companies.items():
            print(f"  - {name} ({data.sector.value})")
