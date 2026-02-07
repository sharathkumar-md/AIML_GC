"""
Markdown parser for OnePager.md files.
Extracts structured data from the markdown format used by Kelp.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.company_data import (
    CompanyData, Sector, Shareholder, Milestone, MarketData,
    Facility, CreditRating, SWOT, Financials, FinancialMetrics,
    LeadershipMember, classify_sector
)

# Get logger
logger = logging.getLogger("markdown_parser")


def parse_onepager(file_path: str) -> CompanyData:
    """
    Parse a OnePager.md file and extract structured company data.

    Args:
        file_path: Path to the OnePager.md file

    Returns:
        CompanyData object with extracted information
    """
    logger.info(f"Parsing OnePager file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    logger.debug(f"File size: {len(content)} characters")

    # Extract company name from the first line or file path
    company_name = extract_company_name(file_path, content)
    logger.info(f"Extracted company name: {company_name}")

    # Parse sections
    sections = parse_sections(content)
    logger.debug(f"Found {len(sections)} sections: {list(sections.keys())}")

    # Create CompanyData object
    company = CompanyData(name=company_name)

    # Populate each field
    company.business_description = sections.get('Business Description', '').strip()
    company.website = sections.get('Website', '').strip()

    # Products & Services
    company.products_services = parse_list_items(sections.get('Product & Services', ''))

    # Industries served
    industries_text = sections.get('Application areas / Industries served', '')
    if industries_text:
        company.industries_served = [i.strip() for i in industries_text.split(',')]

    # Key Operational Indicators
    company.key_operational_indicators = parse_bullet_points(
        sections.get('Key Operational Indicators', '')
    )

    # Shareholders
    company.shareholders = parse_shareholders(sections.get('Shareholders', ''))

    # Extract promoter holding
    for sh in company.shareholders:
        if 'promoter' in sh.name.lower():
            company.promoter_holding = sh.percentage
            break

    # Milestones
    company.milestones = parse_milestones(sections.get('Key Milestones', ''))

    # Market Data
    company.market_data = parse_market_data(sections.get('Market Size', ''))

    # SWOT
    company.swot = parse_swot(sections.get('SWOT', ''))

    # Global Presence
    global_presence = sections.get('Global Presence', '')
    if global_presence:
        company.global_presence = [g.strip() for g in global_presence.split(',')]

    # Future Plans
    company.future_plans = parse_bullet_points(sections.get('Future Plan', ''))

    # Details section (contains multiple fields)
    details = sections.get('Details', '')
    parse_details_section(company, details)

    # Ownership
    ownership = sections.get('Ownership', '')
    parse_ownership_section(company, ownership)

    # Leadership
    company.leadership = parse_leadership(sections.get('Leadership', ''))
    company.board_members = parse_board_members(sections.get('Board Members', ''))

    # People/Employees
    parse_people_section(company, sections.get('People', ''))

    # Facilities
    company.facilities = parse_facilities(sections.get('Facilities', ''))

    # Certifications and Awards
    certs_awards = sections.get('Awards and Certifications', '')
    company.certifications, company.awards = parse_certifications_awards(certs_awards)

    # Partners and Clients
    company.partners = parse_simple_list(sections.get('Partners', ''))
    company.clients = parse_simple_list(sections.get('Clients', ''))

    # Peers
    company.peers = parse_simple_list(sections.get('Peers', ''))

    # Credit Status
    company.credit_ratings = parse_credit_status(sections.get('Credit Status', ''))

    # Financials
    company.financials = parse_financials(sections.get('Financials Status', ''))

    # Store raw data for reference
    company.raw_data = sections

    # Classify sector
    company.sector = classify_sector(company)
    logger.info(f"Classified sector: {company.sector.value}")

    # Add source tracking
    company.sources['onepager'] = file_path

    # Log parsing summary
    logger.info(f"Parsing complete for {company.name}:")
    logger.debug(f"  - Products/Services: {len(company.products_services)}")
    logger.debug(f"  - Shareholders: {len(company.shareholders)}")
    logger.debug(f"  - Milestones: {len(company.milestones)}")
    logger.debug(f"  - Facilities: {len(company.facilities)}")
    logger.debug(f"  - Financial years: {len(company.financials.yearly_data)}")

    return company


def extract_company_name(file_path: str, content: str) -> str:
    """Extract company name from file path or content."""
    # Try to get from file name
    path = Path(file_path)
    name = path.stem.replace('-OnePager', '').replace('_', ' ')

    # Clean up the name
    name = ' '.join(word.capitalize() for word in name.split())

    return name


def parse_sections(content: str) -> Dict[str, str]:
    """
    Parse markdown content into sections based on ## headers.
    """
    sections = {}
    current_section = None
    current_content = []

    lines = content.split('\n')

    for line in lines:
        # Check for ## header
        if line.startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()

            # Start new section
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def parse_list_items(text: str) -> List[str]:
    """Parse markdown list items with ** bold ** markers."""
    items = []

    # Match patterns like "- **Item Name** (description)"
    pattern = r'-\s*\*\*([^*]+)\*\*'
    matches = re.findall(pattern, text)

    for match in matches:
        items.append(match.strip())

    # If no bold items found, try regular list items
    if not items:
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:].strip())

    return items


def parse_bullet_points(text: str) -> List[str]:
    """Parse bullet points from text."""
    points = []

    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('- ') or line.startswith('* '):
            points.append(line[2:].strip())

    return points


def parse_shareholders(text: str) -> List[Shareholder]:
    """Parse shareholder table data."""
    shareholders = []

    # Parse markdown tables
    lines = text.split('\n')
    in_table = False

    for line in lines:
        line = line.strip()
        if '|' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 2:
                # Skip header row
                if parts[0].upper() == 'SHAREHOLDER NAME':
                    in_table = True
                    continue

                if in_table:
                    try:
                        name = parts[0]
                        percentage = float(parts[1]) if parts[1] else 0
                        share_type = parts[2] if len(parts) > 2 else 'Equity'

                        shareholders.append(Shareholder(
                            name=name,
                            percentage=percentage,
                            share_type=share_type
                        ))
                    except (ValueError, IndexError):
                        continue

    return shareholders


def parse_milestones(text: str) -> List[Milestone]:
    """Parse milestones table."""
    milestones = []

    lines = text.split('\n')
    in_table = False

    for line in lines:
        line = line.strip()
        if '|' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 2:
                if parts[0].upper() == 'DATE':
                    in_table = True
                    continue

                if in_table:
                    milestones.append(Milestone(
                        date=parts[0],
                        description=parts[1]
                    ))

    return milestones


def parse_market_data(text: str) -> List[MarketData]:
    """Parse market size table."""
    market_data = []

    lines = text.split('\n')
    in_table = False

    for line in lines:
        line = line.strip()
        if '|' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 5:
                if parts[0].upper() == 'SOURCE':
                    in_table = True
                    continue

                if in_table:
                    try:
                        growth = float(parts[5]) if len(parts) > 5 and parts[5] else 0
                        market_data.append(MarketData(
                            source=parts[0],
                            market=parts[1],
                            region=parts[2],
                            date=parts[3],
                            current_size=parts[4],
                            growth_rate=growth
                        ))
                    except (ValueError, IndexError):
                        continue

    return market_data


def parse_swot(text: str) -> SWOT:
    """Parse SWOT analysis section."""
    swot = SWOT()

    current_category = None

    for line in text.split('\n'):
        line = line.strip()

        if '### Strengths' in line:
            current_category = 'strengths'
        elif '### Weaknesses' in line:
            current_category = 'weaknesses'
        elif '### Opportunities' in line:
            current_category = 'opportunities'
        elif '### Threats' in line:
            current_category = 'threats'
        elif line.startswith('- ') and current_category:
            item = line[2:].strip()
            getattr(swot, current_category).append(item)

    return swot


def parse_details_section(company: CompanyData, text: str) -> None:
    """Parse the Details section with key-value pairs."""
    patterns = {
        'Founded': ('founded', str),
        'Headquarters': ('headquarters', str),
        'Domain': ('domain', str),
        'Segment': ('segment', str),
        'Sub-segment': ('sub_segment', str),
        'Customer Base': ('customer_base', str),
        'Business Activity': ('business_activity', str),
    }

    for line in text.split('\n'):
        for key, (attr, converter) in patterns.items():
            if line.startswith(f'{key}:'):
                # Extract value between ** **
                match = re.search(r'\*\*([^*]+)\*\*', line)
                if match:
                    value = match.group(1).strip()
                    setattr(company, attr, converter(value))


def parse_ownership_section(company: CompanyData, text: str) -> None:
    """Parse ownership information."""
    match = re.search(r'Type:\s*\*\*([^*]+)\*\*', text)
    if match:
        company.ownership_type = match.group(1).strip()


def parse_leadership(text: str) -> List[LeadershipMember]:
    """Parse leadership list."""
    leaders = []

    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('* '):
            # Format: "* Name (Role)"
            match = re.match(r'\*\s*([^(]+)\s*\(([^)]+)\)', line)
            if match:
                leaders.append(LeadershipMember(
                    name=match.group(1).strip(),
                    role=match.group(2).strip()
                ))

    return leaders


def parse_board_members(text: str) -> List[LeadershipMember]:
    """Parse board members section."""
    members = []
    current_type = ""

    for line in text.split('\n'):
        line = line.strip()

        if line.startswith('#### '):
            current_type = line[5:].strip()
        elif line.startswith('- '):
            # Format: "- Name (Role)"
            match = re.match(r'-\s*([^(]+)\s*\(([^)]+)\)', line)
            if match:
                members.append(LeadershipMember(
                    name=match.group(1).strip(),
                    role=f"{match.group(2).strip()} ({current_type})" if current_type else match.group(2).strip()
                ))

    return members


def parse_people_section(company: CompanyData, text: str) -> None:
    """Parse People/Employees section."""
    # Look for employee count
    match = re.search(r'Employees:\s*\*\*(\d+)', text)
    if match:
        company.employees = int(match.group(1))

    # Look for growth percentage
    match = re.search(r'Employees:\s*\*\*\d+\s*\(([^)]+)\)', text)
    if match:
        company.employee_growth = match.group(1)


def parse_facilities(text: str) -> List[Facility]:
    """Parse facilities section."""
    facilities = []
    current_type = ""

    for line in text.split('\n'):
        line = line.strip()

        if line.startswith('- **') and line.endswith('**'):
            current_type = line[4:-2].strip()
        elif line.startswith('- ') and current_type:
            location = line[2:].strip()
            facilities.append(Facility(
                location=location,
                facility_type=current_type
            ))

    return facilities


def parse_certifications_awards(text: str) -> Tuple[List[str], List[str]]:
    """Parse certifications and awards."""
    items = []

    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())

    # Separate certifications from awards (heuristic)
    certifications = []
    awards = []

    cert_keywords = ['ISO', 'IATF', 'certified', 'certification', 'FSSC', 'GMP', 'OHSAS']

    for item in items:
        is_cert = any(kw.lower() in item.lower() for kw in cert_keywords)
        if is_cert:
            certifications.append(item)
        else:
            awards.append(item)

    return certifications, awards


def parse_simple_list(text: str) -> List[str]:
    """Parse a simple comma-separated or line-separated list."""
    if not text or text.strip() == 'Not Available':
        return []

    # First try comma-separated
    items = [item.strip() for item in text.split(',') if item.strip()]

    # If only one item, might be newline separated
    if len(items) == 1:
        items = [item.strip() for item in text.split('\n') if item.strip() and not item.startswith('#')]

    return items


def parse_credit_status(text: str) -> List[CreditRating]:
    """Parse credit status table."""
    ratings = []

    if not text or text.strip() == '[]':
        return ratings

    lines = text.split('\n')
    in_table = False

    for line in lines:
        line = line.strip()
        if '|' in line and '---' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 6:
                if parts[0].lower() == 'instrument':
                    in_table = True
                    continue

                if in_table:
                    try:
                        amount = float(parts[2]) if parts[2] and parts[2] != 'N/A' else None
                        ratings.append(CreditRating(
                            instrument=parts[0],
                            date=parts[1],
                            amount=amount,
                            agency=parts[3],
                            rating=parts[4],
                            status=parts[5],
                            grade=parts[6] if len(parts) > 6 else ''
                        ))
                    except (ValueError, IndexError):
                        continue

    return ratings


def parse_financials(text: str) -> Financials:
    """Parse financial statements section."""
    financials = Financials()

    if not text:
        return financials

    # Parse the nested financial data
    current_statement = None

    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        if '### Income Statement' in line:
            current_statement = 'income'
        elif '### Balance Sheet' in line:
            current_statement = 'balance'
        elif '### Cash Flow' in line:
            current_statement = 'cashflow'
        elif '### Ratios' in line:
            current_statement = 'ratios'
        elif line.startswith('- ') and '|' in line:
            # Parse financial line items
            parse_financial_line(financials, line, current_statement)

    return financials


def parse_financial_line(financials: Financials, line: str, statement_type: str) -> None:
    """Parse a single financial line item."""
    # Format: "- Metric Name | 2020: value | 2021: value | ..."

    # Extract metric name
    parts = line.split('|')
    if len(parts) < 2:
        return

    metric_part = parts[0].replace('- ', '').strip()

    # Determine which metric this is
    metric_mapping = {
        'Revenue From Operations': 'revenue',
        'Operating EBITDA': 'ebitda',
        'PAT': 'pat',
        'PBT': 'pbt',
        'PAT Margin': 'pat_margin',
        'RoCE': 'roce',
        'ROE': 'roe',
        'Asset Turnover': 'asset_turnover',
        'Cash & Bank Balances': 'cash',
        'Borrowings': 'total_debt',
    }

    metric_name = metric_mapping.get(metric_part)
    if not metric_name:
        return

    # Parse year values
    for part in parts[1:]:
        match = re.match(r'\s*(\d{4}):\s*([^\|]+)', part)
        if match:
            year = int(match.group(1))
            value_str = match.group(2).strip()

            if value_str and value_str != 'None':
                try:
                    value = float(value_str)

                    # Create year entry if not exists
                    if year not in financials.yearly_data:
                        financials.yearly_data[year] = FinancialMetrics(year=year)

                    setattr(financials.yearly_data[year], metric_name, value)
                except ValueError:
                    pass


# Utility function to load all companies
def load_all_companies(data_dir: str) -> Dict[str, CompanyData]:
    """
    Load all company data from the data directory.

    Args:
        data_dir: Path to the Company Data directory

    Returns:
        Dictionary mapping company names to CompanyData objects
    """
    companies = {}
    data_path = Path(data_dir)

    # Find all OnePager.md files
    for md_file in data_path.rglob('*-OnePager.md'):
        try:
            company = parse_onepager(str(md_file))
            companies[company.name] = company
            print(f"Loaded: {company.name} ({company.sector.value})")
        except Exception as e:
            print(f"Error loading {md_file}: {e}")

    return companies


if __name__ == "__main__":
    # Test the parser
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        company = parse_onepager(file_path)

        print(f"\n{'='*60}")
        print(f"Company: {company.name}")
        print(f"Sector: {company.sector.value}")
        print(f"Website: {company.website}")
        print(f"Founded: {company.founded}")
        print(f"Employees: {company.employees}")
        print(f"\nBusiness Description:")
        print(company.business_description[:200] + "..." if len(company.business_description) > 200 else company.business_description)
        print(f"\nProducts/Services: {len(company.products_services)}")
        print(f"Facilities: {len(company.facilities)}")
        print(f"Certifications: {len(company.certifications)}")
        print(f"Milestones: {len(company.milestones)}")

        latest = company.get_latest_financials()
        if latest:
            print(f"\nLatest Financials ({latest.year}):")
            print(f"  Revenue: {latest.revenue}")
            print(f"  EBITDA: {latest.ebitda}")
            print(f"  PAT: {latest.pat}")

        print(f"\nSWOT:")
        print(f"  Strengths: {len(company.swot.strengths)}")
        print(f"  Weaknesses: {len(company.swot.weaknesses)}")
        print(f"  Opportunities: {len(company.swot.opportunities)}")
        print(f"  Threats: {len(company.swot.threats)}")
