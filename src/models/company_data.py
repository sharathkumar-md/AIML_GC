"""
Data models for company information extraction.
These structures hold all parsed data from OnePager files and other sources.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Sector(Enum):
    """Industry sectors for template selection."""
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    PHARMA = "pharma"
    LOGISTICS = "logistics"
    CONSUMER = "consumer"
    ELECTRONICS = "electronics"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"


@dataclass
class Shareholder:
    """Shareholder information."""
    name: str
    percentage: float
    share_type: str = "Equity"


@dataclass
class Milestone:
    """Company milestone/event."""
    date: str
    description: str


@dataclass
class MarketData:
    """Market size information."""
    source: str
    market: str
    region: str
    date: str
    current_size: str
    growth_rate: float


@dataclass
class Facility:
    """Company facility information."""
    location: str
    facility_type: str  # Corporate, Manufacturing, R&D, etc.


@dataclass
class CreditRating:
    """Credit rating information."""
    instrument: str
    date: str
    amount: Optional[float]
    agency: str
    rating: str
    status: str
    grade: str


@dataclass
class SWOT:
    """SWOT Analysis."""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)


@dataclass
class FinancialMetrics:
    """Financial data for a single year."""
    year: int
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    pat: Optional[float] = None  # Profit After Tax
    pbt: Optional[float] = None  # Profit Before Tax
    total_assets: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash: Optional[float] = None

    # Ratios
    pat_margin: Optional[float] = None
    roce: Optional[float] = None
    roe: Optional[float] = None
    asset_turnover: Optional[float] = None


@dataclass
class Financials:
    """Complete financial data."""
    yearly_data: Dict[int, FinancialMetrics] = field(default_factory=dict)

    # Derived metrics
    revenue_cagr: Optional[float] = None
    latest_year: Optional[int] = None

    def get_latest(self) -> Optional[FinancialMetrics]:
        """Get the most recent financial data."""
        if not self.yearly_data:
            return None
        self.latest_year = max(self.yearly_data.keys())
        return self.yearly_data.get(self.latest_year)

    def calculate_cagr(self, metric: str, years: int = 5) -> Optional[float]:
        """Calculate CAGR for a given metric over specified years."""
        if len(self.yearly_data) < 2:
            return None

        sorted_years = sorted(self.yearly_data.keys())
        if len(sorted_years) < 2:
            return None

        start_year = sorted_years[max(0, len(sorted_years) - years - 1)]
        end_year = sorted_years[-1]

        start_val = getattr(self.yearly_data.get(start_year), metric, None)
        end_val = getattr(self.yearly_data.get(end_year), metric, None)

        if start_val and end_val and start_val > 0:
            n_years = end_year - start_year
            if n_years > 0:
                return ((end_val / start_val) ** (1 / n_years) - 1) * 100
        return None


@dataclass
class LeadershipMember:
    """Leadership team member."""
    name: str
    role: str


@dataclass
class CompanyData:
    """
    Complete company data structure.
    This is the central data model that holds all extracted information.
    """
    # Basic Info
    name: str
    sector: Sector = Sector.UNKNOWN
    website: str = ""

    # Business Overview
    business_description: str = ""
    products_services: List[str] = field(default_factory=list)
    industries_served: List[str] = field(default_factory=list)

    # Company Details
    founded: Optional[str] = None
    headquarters: str = ""
    domain: str = ""
    segment: str = ""
    sub_segment: str = ""
    customer_base: str = ""  # B2B, B2C, etc.
    business_activity: str = ""
    ownership_type: str = ""  # Public, Private

    # Key Metrics
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    key_operational_indicators: List[str] = field(default_factory=list)

    # People
    employees: Optional[int] = None
    employee_growth: Optional[str] = None
    leadership: List[LeadershipMember] = field(default_factory=list)
    board_members: List[LeadershipMember] = field(default_factory=list)

    # Ownership
    shareholders: List[Shareholder] = field(default_factory=list)
    promoter_holding: Optional[float] = None

    # History & Milestones
    milestones: List[Milestone] = field(default_factory=list)

    # Market & Competition
    market_data: List[MarketData] = field(default_factory=list)
    peers: List[str] = field(default_factory=list)

    # Operations
    facilities: List[Facility] = field(default_factory=list)
    global_presence: List[str] = field(default_factory=list)

    # Certifications & Awards
    certifications: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)

    # Partners & Clients
    partners: List[str] = field(default_factory=list)
    clients: List[str] = field(default_factory=list)

    # Analysis
    swot: SWOT = field(default_factory=SWOT)
    future_plans: List[str] = field(default_factory=list)

    # Financial Data
    financials: Financials = field(default_factory=Financials)
    credit_ratings: List[CreditRating] = field(default_factory=list)

    # Patents
    patents: List[str] = field(default_factory=list)

    # Raw data for reference
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Data sources for citation
    sources: Dict[str, str] = field(default_factory=dict)

    def get_latest_financials(self) -> Optional[FinancialMetrics]:
        """Get the most recent financial metrics."""
        return self.financials.get_latest()

    def get_export_percentage(self) -> Optional[float]:
        """Extract export percentage if available."""
        # This would be extracted from the data during parsing
        return self.key_metrics.get('export_percentage')

    def get_facility_count(self) -> int:
        """Get total number of facilities."""
        return len(self.facilities)

    def get_certification_count(self) -> int:
        """Get total certifications."""
        return len(self.certifications)


# Sector keywords for classification
SECTOR_KEYWORDS = {
    Sector.MANUFACTURING: [
        'manufacturing', 'forging', 'machining', 'fabrication', 'industrial',
        'engineering', 'metal', 'forge', 'casting', 'stamping', 'assembly',
        'automotive', 'auto components', 'machinery'
    ],
    Sector.TECHNOLOGY: [
        'software', 'technology', 'it services', 'digital', 'saas', 'cloud',
        'development', 'salesforce', 'ai', 'ml', 'big data', 'devops',
        'application', 'platform', 'tech'
    ],
    Sector.PHARMA: [
        'pharmaceutical', 'pharma', 'drug', 'medicine', 'healthcare',
        'formulation', 'api', 'therapeutic', 'clinical', 'biotech'
    ],
    Sector.LOGISTICS: [
        'logistics', 'transportation', 'freight', 'shipping', 'supply chain',
        'distribution', 'warehouse', 'express', 'cargo', 'delivery'
    ],
    Sector.CONSUMER: [
        'consumer', 'retail', 'fmcg', 'brand', 'd2c', 'e-commerce',
        'lifestyle', 'food', 'beverage'
    ],
    Sector.ELECTRONICS: [
        'electronics', 'semiconductor', 'pcb', 'ems', 'defense',
        'aerospace', 'avionics', 'radar', 'communication systems'
    ],
    Sector.ENTERTAINMENT: [
        'entertainment', 'cinema', 'multiplex', 'media', 'film',
        'theatre', 'screen', 'movie', 'streaming'
    ]
}


def classify_sector(company_data: CompanyData) -> Sector:
    """
    Classify company into a sector based on business description and other fields.
    """
    # Combine relevant text fields for analysis
    text_to_analyze = ' '.join([
        company_data.business_description.lower(),
        company_data.domain.lower(),
        company_data.segment.lower(),
        company_data.sub_segment.lower(),
        ' '.join(company_data.industries_served).lower(),
        ' '.join(company_data.products_services).lower()
    ])

    # Score each sector
    sector_scores = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_to_analyze)
        sector_scores[sector] = score

    # Return the sector with highest score
    if sector_scores:
        best_sector = max(sector_scores, key=sector_scores.get)
        if sector_scores[best_sector] > 0:
            return best_sector

    return Sector.UNKNOWN
