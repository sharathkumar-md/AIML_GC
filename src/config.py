"""
Configuration settings for the Kelp Automated Deal Flow pipeline.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class KelpBranding:
    """Kelp brand guidelines configuration."""

    # Colors (RGB tuples)
    primary_dark: tuple = (45, 35, 90)       # Dark Indigo/Violet
    accent_pink: tuple = (255, 100, 130)      # Pink gradient start
    accent_orange: tuple = (255, 150, 80)     # Orange gradient end
    accent_cyan: tuple = (0, 200, 255)        # Cyan for icons
    background: tuple = (255, 255, 255)       # White
    text_dark: tuple = (60, 60, 60)           # Dark grey
    text_white: tuple = (255, 255, 255)       # White text

    # Typography
    heading_font: str = "Arial"
    heading_size: int = 24
    subheading_size: int = 18
    body_font: str = "Arial"
    body_size: int = 10
    footer_size: int = 9

    # Footer text
    footer_text: str = "Strictly Private & Confidential – Prepared by Kelp M&A Team"

    # Logo placeholder
    logo_text: str = "Kelp"


@dataclass
class LLMConfig:
    """LLM API configuration."""

    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = "gpt-4o-mini"  # Cost-effective model
    openai_max_tokens: int = 4000

    # Anthropic (optional)
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = "claude-3-haiku-20240307"

    # Cost tracking
    max_cost_per_presentation: float = 100.0  # INR

    # Which provider to use
    provider: str = "openai"  # or "anthropic"


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "Company Data")
    output_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "output")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")

    # Branding
    branding: KelpBranding = field(default_factory=KelpBranding)

    # LLM
    llm: LLMConfig = field(default_factory=LLMConfig)

    # Processing options
    generate_citations: bool = True
    include_images: bool = True
    anonymize: bool = True

    # Slide configuration
    num_slides: int = 3  # Excluding title slide

    # Debug mode
    debug: bool = False

    def __post_init__(self):
        """Create necessary directories."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Sector-specific templates configuration
SECTOR_TEMPLATES = {
    "manufacturing": {
        "slide_1_title": "Business Profile & Infrastructure",
        "slide_2_title": "Financial & Operational Scale",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "facilities_count",
            "capacity",
            "certifications",
            "export_percentage",
            "customer_count"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["factory", "manufacturing", "industrial", "machinery"]
    },
    "technology": {
        "slide_1_title": "Technology Overview & Capabilities",
        "slide_2_title": "Growth Metrics & Market Position",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "employee_count",
            "tech_stack",
            "certifications",
            "client_retention",
            "global_presence"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["technology", "software", "digital", "office", "team"]
    },
    "pharma": {
        "slide_1_title": "Product Portfolio & Therapeutic Areas",
        "slide_2_title": "Manufacturing & Regulatory Compliance",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "product_count",
            "facilities_count",
            "certifications",
            "export_percentage",
            "r_and_d_spend"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["pharmaceutical", "laboratory", "medicine", "research"]
    },
    "logistics": {
        "slide_1_title": "Network & Infrastructure",
        "slide_2_title": "Operational Metrics & Financials",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "network_coverage",
            "fleet_size",
            "warehouses",
            "delivery_volume",
            "customer_count"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["logistics", "warehouse", "transportation", "delivery", "truck"]
    },
    "consumer": {
        "slide_1_title": "Brand Overview & Market Presence",
        "slide_2_title": "Growth & Unit Economics",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "brand_count",
            "channel_mix",
            "customer_retention",
            "average_order_value",
            "gross_margin"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["retail", "consumer", "products", "lifestyle"]
    },
    "electronics": {
        "slide_1_title": "Technology & Product Portfolio",
        "slide_2_title": "Manufacturing Excellence & Financials",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "product_lines",
            "facilities_count",
            "certifications",
            "defense_share",
            "export_percentage"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["electronics", "circuit", "aerospace", "defense", "technology"]
    },
    "entertainment": {
        "slide_1_title": "Brand & Market Presence",
        "slide_2_title": "Growth & Unit Economics",
        "slide_3_title": "Investment Highlights",
        "key_metrics": [
            "screen_count",
            "seat_capacity",
            "occupancy_rate",
            "ticket_price",
            "f_and_b_spend"
        ],
        "chart_metrics": ["revenue", "ebitda", "pat"],
        "image_keywords": ["cinema", "entertainment", "theatre", "movie", "audience"]
    }
}

# Project code names for anonymization
PROJECT_CODENAMES = [
    "Apex", "Atlas", "Aurora", "Beacon", "Catalyst",
    "Delta", "Eclipse", "Falcon", "Genesis", "Horizon",
    "Infinity", "Jupiter", "Keystone", "Luna", "Magnus",
    "Nova", "Omega", "Phoenix", "Quantum", "Radiant",
    "Summit", "Titan", "Unity", "Vertex", "Zenith"
]


def get_config() -> PipelineConfig:
    """Get the global pipeline configuration."""
    return PipelineConfig()


def get_sector_template(sector: str) -> Dict[str, Any]:
    """Get template configuration for a sector."""
    return SECTOR_TEMPLATES.get(sector, SECTOR_TEMPLATES["manufacturing"])
