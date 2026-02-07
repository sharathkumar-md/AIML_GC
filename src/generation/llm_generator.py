"""
LLM-based content generation for Investment Teasers.
Uses OpenAI GPT-4o-mini or Anthropic Claude for cost-effective generation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.company_data import CompanyData, Sector
from generation.anonymizer import Anonymizer
from config import get_sector_template, LLMConfig

logger = logging.getLogger("llm_generator")

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Run: pip install openai")


@dataclass
class SlideContent:
    """Content for a single slide."""
    title: str
    sections: List[Dict[str, Any]] = field(default_factory=list)
    key_metrics: Dict[str, str] = field(default_factory=dict)
    bullet_points: List[str] = field(default_factory=list)
    chart_data: Optional[Dict[str, Any]] = None
    image_keywords: List[str] = field(default_factory=list)


@dataclass
class TeaserContent:
    """Complete content for an Investment Teaser."""
    project_name: str
    sector: str
    slides: List[SlideContent] = field(default_factory=list)
    citations: Dict[str, str] = field(default_factory=dict)
    raw_response: str = ""


class ContentGenerator:
    """
    Generates Investment Teaser content using LLM.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the content generator.

        Args:
            config: LLM configuration (uses environment variables if not provided)
        """
        self.config = config or LLMConfig()
        self.client = None
        self.total_tokens_used = 0
        self.total_cost = 0.0

        # Initialize OpenAI client
        if OPENAI_AVAILABLE and self.config.openai_api_key:
            self.client = OpenAI(api_key=self.config.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI client not available. Check API key.")

    def generate_teaser_content(
        self,
        company: CompanyData,
        anonymizer: Anonymizer
    ) -> TeaserContent:
        """
        Generate complete teaser content for a company.

        Args:
            company: Parsed company data
            anonymizer: Anonymizer instance

        Returns:
            TeaserContent with all slides
        """
        logger.info(f"Generating teaser content for: {company.name}")

        # Get sector template
        template = get_sector_template(company.sector.value)

        # Create teaser content structure
        teaser = TeaserContent(
            project_name=anonymizer.get_anonymous_reference(),
            sector=company.sector.value
        )

        if not self.client:
            logger.warning("No LLM client available. Using fallback content generation.")
            return self._generate_fallback_content(company, anonymizer, template)

        # Generate content for each slide
        try:
            # Slide 1: Business Overview
            slide1 = self._generate_slide_1(company, anonymizer, template)
            teaser.slides.append(slide1)

            # Slide 2: Financial & Metrics
            slide2 = self._generate_slide_2(company, anonymizer, template)
            teaser.slides.append(slide2)

            # Slide 3: Investment Highlights
            slide3 = self._generate_slide_3(company, anonymizer, template)
            teaser.slides.append(slide3)

            logger.info(f"Generated {len(teaser.slides)} slides")
            logger.info(f"Total tokens used: {self.total_tokens_used}")

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return self._generate_fallback_content(company, anonymizer, template)

        return teaser

    def _generate_slide_1(
        self,
        company: CompanyData,
        anonymizer: Anonymizer,
        template: Dict
    ) -> SlideContent:
        """Generate content for Slide 1: Business Overview."""
        logger.info("Generating Slide 1: Business Overview")

        # Prepare data for the prompt
        products = company.products_services[:8]  # Limit to 8 products
        facilities = [f.location for f in company.facilities[:5]]
        certifications = company.certifications[:6]

        prompt = f"""You are creating content for a professional M&A Investment Teaser slide.

TASK: Create concise, anonymized content for the "Business Overview" slide.

COMPANY DATA (DO NOT reveal the company name - use "The Company" instead):
- Business Description: {company.business_description}
- Sector: {company.sector.value}
- Founded: {company.founded}
- Products/Services: {', '.join(products)}
- Industries Served: {', '.join(company.industries_served[:5])}
- Number of Facilities: {len(company.facilities)}
- Facility Locations (generalize): {', '.join(facilities)}
- Key Certifications: {', '.join(certifications)}
- Employees: {company.employees}
- Global Presence: {', '.join(company.global_presence)}

OUTPUT FORMAT (JSON):
{{
    "business_overview": "2-3 sentence anonymized description focusing on value proposition",
    "key_facts": [
        {{"label": "Founded", "value": "year"}},
        {{"label": "Employees", "value": "number"}},
        {{"label": "Facilities", "value": "X state-of-the-art facilities"}},
        {{"label": "Global Presence", "value": "countries/regions"}}
    ],
    "product_segments": ["segment1", "segment2", "segment3", "segment4"],
    "industries_served": ["industry1", "industry2", "industry3"],
    "certifications_highlight": ["cert1", "cert2", "cert3"]
}}

RULES:
1. DO NOT mention the company name - use "The Company" or "The Business"
2. Keep text concise - suitable for presentation slides
3. Highlight unique value propositions
4. Use professional M&A language
"""

        response = self._call_llm(prompt)

        # Parse response
        try:
            content = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using fallback")
            content = self._parse_text_response(response)

        # Build slide content
        slide = SlideContent(
            title=template.get('slide_1_title', 'Business Overview'),
            image_keywords=template.get('image_keywords', [])
        )

        slide.sections = [
            {'type': 'overview', 'content': content.get('business_overview', '')},
            {'type': 'key_facts', 'items': content.get('key_facts', [])},
            {'type': 'products', 'items': content.get('product_segments', [])},
            {'type': 'industries', 'items': content.get('industries_served', [])},
            {'type': 'certifications', 'items': content.get('certifications_highlight', [])}
        ]

        return slide

    def _generate_slide_2(
        self,
        company: CompanyData,
        anonymizer: Anonymizer,
        template: Dict
    ) -> SlideContent:
        """Generate content for Slide 2: Financial Metrics."""
        logger.info("Generating Slide 2: Financial Metrics")

        # Prepare financial data
        latest = company.get_latest_financials()
        financial_years = sorted(company.financials.yearly_data.keys())[-5:]  # Last 5 years

        revenue_data = []
        ebitda_data = []
        pat_data = []

        for year in financial_years:
            fy = company.financials.yearly_data.get(year)
            if fy:
                if fy.revenue:
                    revenue_data.append({'year': f'FY{str(year)[2:]}', 'value': round(fy.revenue, 1)})
                if fy.ebitda:
                    ebitda_data.append({'year': f'FY{str(year)[2:]}', 'value': round(fy.ebitda, 1)})
                if fy.pat:
                    pat_data.append({'year': f'FY{str(year)[2:]}', 'value': round(fy.pat, 1)})

        # Calculate CAGR
        revenue_cagr = company.financials.calculate_cagr('revenue', 5)

        prompt = f"""You are creating content for a professional M&A Investment Teaser slide.

TASK: Create the "Financial Metrics & Growth" slide content.

FINANCIAL DATA:
- Latest Year: {latest.year if latest else 'N/A'}
- Revenue (Latest): {latest.revenue if latest else 'N/A'} (in local currency millions)
- EBITDA (Latest): {latest.ebitda if latest else 'N/A'}
- PAT (Latest): {latest.pat if latest else 'N/A'}
- Revenue CAGR (5Y): {revenue_cagr:.1f}% if revenue_cagr else 'N/A'
- PAT Margin: {latest.pat_margin:.1f}% if latest and latest.pat_margin else 'N/A'
- RoCE: {latest.roce:.1f}% if latest and latest.roce else 'N/A'
- ROE: {latest.roe:.1f}% if latest and latest.roe else 'N/A'

Revenue History: {revenue_data}
EBITDA History: {ebitda_data}

SECTOR: {company.sector.value}

OUTPUT FORMAT (JSON):
{{
    "headline_metrics": [
        {{"label": "Revenue CAGR", "value": "X%", "period": "FYxx-FYxx"}},
        {{"label": "EBITDA Margin", "value": "X%"}},
        {{"label": "RoCE", "value": "X%"}},
        {{"label": "ROE", "value": "X%"}}
    ],
    "growth_narrative": "1-2 sentences about financial growth story",
    "key_achievements": ["achievement1", "achievement2", "achievement3"],
    "operational_highlights": ["highlight1", "highlight2"]
}}

RULES:
1. Use actual numbers from the data
2. Highlight positive trends
3. Use professional investment language
4. Keep text concise for slides
"""

        response = self._call_llm(prompt)

        try:
            content = json.loads(response)
        except json.JSONDecodeError:
            content = self._parse_text_response(response)

        # Build slide content
        slide = SlideContent(
            title=template.get('slide_2_title', 'Financial Performance')
        )

        slide.sections = [
            {'type': 'metrics', 'items': content.get('headline_metrics', [])},
            {'type': 'narrative', 'content': content.get('growth_narrative', '')},
            {'type': 'achievements', 'items': content.get('key_achievements', [])},
        ]

        # Add chart data
        slide.chart_data = {
            'revenue': revenue_data,
            'ebitda': ebitda_data,
            'pat': pat_data
        }

        return slide

    def _generate_slide_3(
        self,
        company: CompanyData,
        anonymizer: Anonymizer,
        template: Dict
    ) -> SlideContent:
        """Generate content for Slide 3: Investment Highlights."""
        logger.info("Generating Slide 3: Investment Highlights")

        # Gather all relevant data for highlights
        strengths = company.swot.strengths[:3]
        opportunities = company.swot.opportunities[:2]
        future_plans = company.future_plans[:3]
        market_data = company.market_data[:2]

        prompt = f"""You are creating content for a professional M&A Investment Teaser slide.

TASK: Create 5 compelling "Investment Highlights" for the final slide.

COMPANY DATA:
- Sector: {company.sector.value}
- Strengths: {strengths}
- Opportunities: {opportunities}
- Future Plans: {future_plans}
- Market Data: {[{'market': m.market, 'growth': m.growth_rate} for m in market_data]}
- Certifications: {len(company.certifications)} certifications
- Client Base: {len(company.clients)} clients
- Global Presence: {company.global_presence}
- Revenue CAGR: {company.financials.calculate_cagr('revenue', 5):.1f}%

OUTPUT FORMAT (JSON):
{{
    "investment_highlights": [
        {{
            "headline": "Short compelling headline (5-8 words)",
            "detail": "Supporting detail with specific data points (1 sentence)"
        }},
        // ... 4 more highlights
    ],
    "closing_statement": "One powerful closing statement for the teaser"
}}

RULES:
1. Each highlight should be unique and compelling
2. Use specific numbers where available
3. DO NOT mention company name
4. Focus on: Market Position, Financial Strength, Growth Potential, Competitive Moat, Strategic Value
5. Use active, confident language
"""

        response = self._call_llm(prompt)

        try:
            content = json.loads(response)
        except json.JSONDecodeError:
            content = self._parse_text_response(response)

        # Build slide content
        slide = SlideContent(
            title=template.get('slide_3_title', 'Investment Highlights')
        )

        slide.sections = [
            {'type': 'highlights', 'items': content.get('investment_highlights', [])},
        ]

        if content.get('closing_statement'):
            slide.sections.append({
                'type': 'closing',
                'content': content.get('closing_statement')
            })

        return slide

    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM API.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        if not self.client:
            raise ValueError("No LLM client available")

        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert M&A analyst creating professional investment teasers. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=self.config.openai_max_tokens,
                response_format={"type": "json_object"}
            )

            # Track usage
            if response.usage:
                self.total_tokens_used += response.usage.total_tokens
                # Estimate cost (GPT-4o-mini pricing)
                self.total_cost += (response.usage.prompt_tokens * 0.00015 / 1000 +
                                   response.usage.completion_tokens * 0.0006 / 1000)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def _parse_text_response(self, response: str) -> Dict:
        """Parse a text response when JSON parsing fails."""
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {"raw_response": response}

    def _generate_fallback_content(
        self,
        company: CompanyData,
        anonymizer: Anonymizer,
        template: Dict
    ) -> TeaserContent:
        """Generate fallback content without LLM."""
        logger.info("Generating fallback content (no LLM)")

        teaser = TeaserContent(
            project_name=anonymizer.get_anonymous_reference(),
            sector=company.sector.value
        )

        # Slide 1: Business Overview
        slide1 = SlideContent(title=template.get('slide_1_title', 'Business Overview'))
        slide1.sections = [
            {
                'type': 'overview',
                'content': anonymizer.anonymize_text(company.business_description[:300])
            },
            {
                'type': 'key_facts',
                'items': [
                    {'label': 'Founded', 'value': str(company.founded) if company.founded else 'N/A'},
                    {'label': 'Employees', 'value': str(company.employees) if company.employees else 'N/A'},
                    {'label': 'Facilities', 'value': f"{len(company.facilities)} locations"},
                    {'label': 'Global Presence', 'value': ', '.join(company.global_presence[:3])}
                ]
            },
            {
                'type': 'products',
                'items': company.products_services[:6]
            }
        ]
        slide1.image_keywords = template.get('image_keywords', [])
        teaser.slides.append(slide1)

        # Slide 2: Financial Metrics
        slide2 = SlideContent(title=template.get('slide_2_title', 'Financial Performance'))
        latest = company.get_latest_financials()

        if latest:
            slide2.key_metrics = {
                'Revenue': f"{latest.revenue:.1f}" if latest.revenue else 'N/A',
                'EBITDA': f"{latest.ebitda:.1f}" if latest.ebitda else 'N/A',
                'PAT Margin': f"{latest.pat_margin:.1f}%" if latest.pat_margin else 'N/A',
                'RoCE': f"{latest.roce:.1f}%" if latest.roce else 'N/A'
            }

            # Prepare chart data
            financial_years = sorted(company.financials.yearly_data.keys())[-5:]
            revenue_data = []
            for year in financial_years:
                fy = company.financials.yearly_data.get(year)
                if fy and fy.revenue:
                    revenue_data.append({'year': f'FY{str(year)[2:]}', 'value': round(fy.revenue, 1)})

            slide2.chart_data = {'revenue': revenue_data}

        teaser.slides.append(slide2)

        # Slide 3: Investment Highlights
        slide3 = SlideContent(title=template.get('slide_3_title', 'Investment Highlights'))
        highlights = []

        # Use strengths and opportunities
        for strength in company.swot.strengths[:3]:
            highlights.append({
                'headline': 'Key Strength',
                'detail': anonymizer.anonymize_text(strength[:150])
            })

        for opportunity in company.swot.opportunities[:2]:
            highlights.append({
                'headline': 'Growth Opportunity',
                'detail': anonymizer.anonymize_text(opportunity[:150])
            })

        slide3.sections = [{'type': 'highlights', 'items': highlights[:5]}]
        teaser.slides.append(slide3)

        return teaser

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            'total_tokens': self.total_tokens_used,
            'estimated_cost_usd': round(self.total_cost, 4),
            'estimated_cost_inr': round(self.total_cost * 83, 2)  # Approximate USD to INR
        }


# Import re at module level
import re
