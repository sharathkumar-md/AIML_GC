"""
PowerPoint generator for Investment Teasers.
Creates professional, editable PPTX files with native charts.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor as RgbColor  # RGBColor is in pptx.dml.color
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import KelpBranding, get_config
from generation.llm_generator import TeaserContent, SlideContent
from utils.image_fetcher import ImageFetcher

logger = logging.getLogger("ppt_generator")


class PresentationGenerator:
    """
    Generates Investment Teaser PowerPoint presentations.
    """

    def __init__(self, branding: Optional[KelpBranding] = None, enable_images: bool = True):
        """
        Initialize the presentation generator.

        Args:
            branding: Kelp branding configuration
            enable_images: Whether to fetch and add stock images
        """
        self.branding = branding or KelpBranding()
        self.prs = None
        self.enable_images = enable_images
        self.image_fetcher = ImageFetcher() if enable_images else None

        # Slide dimensions (16:9 widescreen)
        self.slide_width = Inches(13.333)
        self.slide_height = Inches(7.5)

        logger.info("PresentationGenerator initialized")

    def create_presentation(
        self,
        content: TeaserContent,
        output_path: str
    ) -> str:
        """
        Create a complete Investment Teaser presentation.

        Args:
            content: Generated teaser content
            output_path: Path for the output PPTX file

        Returns:
            Path to the generated file
        """
        logger.info(f"Creating presentation: {content.project_name}")

        # Create new presentation
        self.prs = Presentation()
        self.prs.slide_width = self.slide_width
        self.prs.slide_height = self.slide_height

        # Create title slide
        self._create_title_slide(content.project_name)

        # Fetch sector image if enabled
        sector_image = None
        if self.enable_images and self.image_fetcher:
            try:
                sector_image = self.image_fetcher.fetch_sector_image(content.sector)
            except Exception as e:
                logger.warning(f"Could not fetch sector image: {e}")

        # Create content slides
        for i, slide_content in enumerate(content.slides):
            logger.info(f"Creating slide {i+2}: {slide_content.title}")

            if i == 0:
                self._create_business_overview_slide(slide_content)
            elif i == 1:
                self._create_financial_slide(slide_content)
            elif i == 2:
                self._create_highlights_slide(slide_content, sector_image)

        # Create disclaimer slide (always at the end)
        self._create_disclaimer_slide()

        # Save presentation
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(output_file))

        logger.info(f"Presentation saved: {output_file}")
        return str(output_file)

    def _create_title_slide(self, project_name: str) -> None:
        """Create the title slide with Kelp branding."""
        # Add blank slide
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)

        # Add gradient background (dark indigo/violet)
        self._set_slide_background(slide, self.branding.primary_dark)

        # Add Kelp logo placeholder (top left)
        logo_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(2), Inches(0.6))
        logo_frame = logo_box.text_frame
        logo_para = logo_frame.paragraphs[0]
        logo_run = logo_para.add_run()
        logo_run.text = "Kelp"
        logo_run.font.name = self.branding.heading_font
        logo_run.font.size = Pt(32)
        logo_run.font.bold = True
        logo_run.font.color.rgb = RgbColor(*self.branding.accent_pink)

        # Add project name (main title)
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(10), Inches(1.5))
        title_frame = title_box.text_frame
        title_para = title_frame.paragraphs[0]
        title_run = title_para.add_run()
        title_run.text = project_name
        title_run.font.name = self.branding.heading_font
        title_run.font.size = Pt(54)
        title_run.font.bold = True
        title_run.font.color.rgb = RgbColor(*self.branding.text_white)

        # Add subtitle
        subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(6), Inches(0.8))
        subtitle_frame = subtitle_box.text_frame
        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_run = subtitle_para.add_run()
        subtitle_run.text = "Investment Brief"
        subtitle_run.font.name = self.branding.body_font
        subtitle_run.font.size = Pt(24)
        subtitle_run.font.color.rgb = RgbColor(*self.branding.text_white)

        # Add website
        web_box = slide.shapes.add_textbox(Inches(0.5), Inches(5), Inches(4), Inches(0.5))
        web_frame = web_box.text_frame
        web_para = web_frame.paragraphs[0]
        web_run = web_para.add_run()
        web_run.text = "kelpglobal.com"
        web_run.font.name = self.branding.body_font
        web_run.font.size = Pt(14)
        web_run.font.italic = True
        web_run.font.color.rgb = RgbColor(180, 180, 180)

        # Add footer
        self._add_footer(slide)

    def _create_business_overview_slide(self, content: SlideContent) -> None:
        """Create the Business Overview slide."""
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)

        # White background
        self._set_slide_background(slide, self.branding.background)

        # Add header with title
        self._add_slide_header(slide, content.title)

        # Layout: Left side for overview, Right side for key facts
        left_margin = Inches(0.3)
        content_top = Inches(1.1)

        # Business Overview section header bar
        overview_header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            left_margin, content_top,
            Inches(7.5), Inches(0.35)
        )
        overview_header.fill.solid()
        overview_header.fill.fore_color.rgb = RgbColor(0, 75, 100)  # Dark teal
        overview_header.line.fill.background()

        # Business Overview header text
        header_text = slide.shapes.add_textbox(left_margin + Inches(0.1), content_top + Inches(0.05), Inches(7), Inches(0.3))
        htf = header_text.text_frame
        hp = htf.paragraphs[0]
        hr = hp.add_run()
        hr.text = "Business Overview:"
        hr.font.name = self.branding.heading_font
        hr.font.size = Pt(12)
        hr.font.bold = True
        hr.font.color.rgb = RgbColor(*self.branding.text_white)

        # Business Overview content
        overview_section = self._find_section(content.sections, 'overview')
        if overview_section:
            overview_box = slide.shapes.add_textbox(
                left_margin, content_top + Inches(0.4),
                Inches(7.5), Inches(1.4)
            )
            tf = overview_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = overview_section.get('content', '')
            p.font.name = self.branding.body_font
            p.font.size = Pt(10)
            p.font.color.rgb = RgbColor(*self.branding.text_dark)

        # Key Facts section (right side) - "At a Glance"
        key_facts = self._find_section(content.sections, 'key_facts')
        if key_facts:
            facts_left = Inches(8)
            facts_top = content_top

            # At a Glance header bar
            facts_header = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                facts_left, facts_top,
                Inches(4.8), Inches(0.35)
            )
            facts_header.fill.solid()
            facts_header.fill.fore_color.rgb = RgbColor(*self.branding.accent_cyan)
            facts_header.line.fill.background()

            # Header text
            fh_text = slide.shapes.add_textbox(facts_left + Inches(0.1), facts_top + Inches(0.05), Inches(4.5), Inches(0.3))
            fhtf = fh_text.text_frame
            fhp = fhtf.paragraphs[0]
            fhr = fhp.add_run()
            fhr.text = "At a Glance"
            fhr.font.name = self.branding.heading_font
            fhr.font.size = Pt(12)
            fhr.font.bold = True
            fhr.font.color.rgb = RgbColor(*self.branding.text_white)

            # Facts content
            facts_box = slide.shapes.add_textbox(
                facts_left, facts_top + Inches(0.4),
                Inches(4.8), Inches(2.2)
            )
            self._add_key_facts_box(facts_box, key_facts.get('items', []))

        # Products section
        products = self._find_section(content.sections, 'products')
        if products:
            products_box = slide.shapes.add_textbox(
                left_margin, Inches(3),
                Inches(5.5), Inches(2)
            )
            self._add_list_section(
                products_box,
                "Product Portfolio",
                products.get('items', [])
            )

        # Industries section
        industries = self._find_section(content.sections, 'industries')
        if industries:
            industries_box = slide.shapes.add_textbox(
                Inches(6.5), Inches(3),
                Inches(5.5), Inches(2)
            )
            self._add_list_section(
                industries_box,
                "Industries Served",
                industries.get('items', [])
            )

        # Certifications section (bottom)
        certs = self._find_section(content.sections, 'certifications')
        if certs:
            certs_box = slide.shapes.add_textbox(
                left_margin, Inches(5.5),
                Inches(12), Inches(1.2)
            )
            self._add_horizontal_badges(certs_box, "Certifications", certs.get('items', []))

        # Add footer
        self._add_footer(slide)

    def _create_financial_slide(self, content: SlideContent) -> None:
        """Create the Financial Metrics slide."""
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)

        # White background
        self._set_slide_background(slide, self.branding.background)

        # Add header
        self._add_slide_header(slide, content.title)

        left_margin = Inches(0.5)
        content_top = Inches(1.2)

        # Key metrics boxes at top
        metrics = self._find_section(content.sections, 'metrics')
        if metrics:
            self._add_metric_boxes(slide, metrics.get('items', []), content_top)

        # Chart area (middle)
        if content.chart_data:
            self._add_financial_chart(slide, content.chart_data)

        # Narrative section
        narrative = self._find_section(content.sections, 'narrative')
        if narrative:
            narrative_box = slide.shapes.add_textbox(
                Inches(7.5), Inches(3),
                Inches(5), Inches(2)
            )
            tf = narrative_box.text_frame
            tf.word_wrap = True

            # Add growth narrative
            p = tf.paragraphs[0]
            p.text = narrative.get('content', '')
            p.font.name = self.branding.body_font
            p.font.size = Pt(11)
            p.font.color.rgb = RgbColor(*self.branding.text_dark)

        # Key achievements
        achievements = self._find_section(content.sections, 'achievements')
        if achievements:
            ach_box = slide.shapes.add_textbox(
                Inches(7.5), Inches(5),
                Inches(5), Inches(1.8)
            )
            self._add_list_section(ach_box, "Key Achievements", achievements.get('items', []))

        # Add footer
        self._add_footer(slide)

    def _create_highlights_slide(self, content: SlideContent, sector_image: Optional[str] = None) -> None:
        """Create the Investment Highlights slide."""
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)

        # White background
        self._set_slide_background(slide, self.branding.background)

        # Add header
        self._add_slide_header(slide, content.title)

        # Add sector image on the left if available
        image_width = 0
        if sector_image:
            try:
                from PIL import Image
                # Add circular/rounded image on the left side
                img = slide.shapes.add_picture(
                    sector_image,
                    Inches(0.3), Inches(1.5),
                    width=Inches(4), height=Inches(4)
                )
                image_width = 4.5
                logger.info(f"Added sector image to highlights slide")
            except Exception as e:
                logger.warning(f"Could not add image to slide: {e}")

        # Get highlights
        highlights = self._find_section(content.sections, 'highlights')
        if highlights:
            items = highlights.get('items', [])
            self._add_investment_highlights(slide, items, left_offset=image_width)

        # Closing statement
        closing = self._find_section(content.sections, 'closing')
        if closing:
            closing_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(6.3),
                Inches(12), Inches(0.5)
            )
            tf = closing_box.text_frame
            p = tf.paragraphs[0]
            p.text = closing.get('content', '')
            p.font.name = self.branding.body_font
            p.font.size = Pt(12)
            p.font.italic = True
            p.font.color.rgb = RgbColor(*self.branding.text_dark)
            p.alignment = PP_ALIGN.CENTER

        # Add footer
        self._add_footer(slide)

    def _create_disclaimer_slide(self) -> None:
        """Create the disclaimer slide at the end."""
        slide_layout = self.prs.slide_layouts[6]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)

        # Dark background (matching title slide)
        self._set_slide_background(slide, self.branding.primary_dark)

        # Add Kelp logo (top left)
        logo_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(2), Inches(0.6))
        logo_frame = logo_box.text_frame
        logo_para = logo_frame.paragraphs[0]
        logo_run = logo_para.add_run()
        logo_run.text = "Kelp"
        logo_run.font.name = self.branding.heading_font
        logo_run.font.size = Pt(32)
        logo_run.font.bold = True
        logo_run.font.color.rgb = RgbColor(*self.branding.accent_pink)

        # Add title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(12), Inches(0.8))
        title_frame = title_box.text_frame
        title_para = title_frame.paragraphs[0]
        title_run = title_para.add_run()
        title_run.text = "Important Notice & Disclaimer"
        title_run.font.name = self.branding.heading_font
        title_run.font.size = Pt(36)
        title_run.font.bold = True
        title_run.font.color.rgb = RgbColor(*self.branding.text_white)

        # Add disclaimer text
        disclaimer_text = """Strictly Private & Confidential. This presentation is prepared by Kelp Global exclusively for the intended recipient and may not be reproduced or distributed without prior written consent. This document is for informational purposes only and does not constitute an offer to sell or a solicitation of an offer to buy any securities. While all information is obtained from sources believed to be reliable, Kelp Global makes no representation or warranty regarding its accuracy or completeness and accepts no liability for any loss arising from its use. This presentation contains forward-looking statements and financial projections based on current assumptions; actual results may vary materially."""

        disclaimer_box = slide.shapes.add_textbox(Inches(0.5), Inches(3), Inches(12), Inches(3))
        disclaimer_frame = disclaimer_box.text_frame
        disclaimer_frame.word_wrap = True
        disclaimer_para = disclaimer_frame.paragraphs[0]
        disclaimer_para.line_spacing = 1.5
        disclaimer_run = disclaimer_para.add_run()
        disclaimer_run.text = disclaimer_text
        disclaimer_run.font.name = self.branding.body_font
        disclaimer_run.font.size = Pt(14)
        disclaimer_run.font.color.rgb = RgbColor(200, 200, 200)

        # Add footer
        self._add_footer(slide)

    # Helper methods

    def _set_slide_background(self, slide, color: Tuple[int, int, int]) -> None:
        """Set slide background color."""
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RgbColor(*color)

    def _add_slide_header(self, slide, title: str) -> None:
        """Add slide header with Kelp branding bar and logo."""
        # Header bar background (dark teal/indigo gradient effect)
        header_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(0),
            self.slide_width, Inches(0.9)
        )
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = RgbColor(0, 75, 100)  # Dark teal
        header_bar.line.fill.background()

        # Title (on the header bar)
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(10), Inches(0.5))
        title_frame = title_box.text_frame
        title_para = title_frame.paragraphs[0]
        title_run = title_para.add_run()
        title_run.text = title
        title_run.font.name = self.branding.heading_font
        title_run.font.size = Pt(24)
        title_run.font.bold = True
        title_run.font.color.rgb = RgbColor(*self.branding.text_white)

        # Kelp logo (top right on header bar)
        logo_box = slide.shapes.add_textbox(Inches(11.5), Inches(0.25), Inches(1.5), Inches(0.5))
        logo_frame = logo_box.text_frame
        logo_para = logo_frame.paragraphs[0]
        logo_para.alignment = PP_ALIGN.RIGHT
        logo_run = logo_para.add_run()
        logo_run.text = "Kelp"
        logo_run.font.name = self.branding.heading_font
        logo_run.font.size = Pt(20)
        logo_run.font.bold = True
        logo_run.font.color.rgb = RgbColor(*self.branding.accent_pink)

    def _add_footer(self, slide) -> None:
        """Add footer to slide."""
        footer_box = slide.shapes.add_textbox(
            Inches(0), Inches(7.1),
            self.slide_width, Inches(0.3)
        )
        footer_frame = footer_box.text_frame
        footer_para = footer_frame.paragraphs[0]
        footer_para.alignment = PP_ALIGN.CENTER
        footer_run = footer_para.add_run()
        footer_run.text = self.branding.footer_text
        footer_run.font.name = self.branding.body_font
        footer_run.font.size = Pt(self.branding.footer_size)
        footer_run.font.color.rgb = RgbColor(120, 120, 120)

    def _add_text_content(
        self,
        shape,
        header: str,
        content: str,
        is_header: bool = False
    ) -> None:
        """Add formatted text content to a shape."""
        tf = shape.text_frame
        tf.word_wrap = True

        # Header
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = header
        run.font.name = self.branding.heading_font
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RgbColor(*self.branding.primary_dark)

        # Content
        p2 = tf.add_paragraph()
        p2.text = content
        p2.font.name = self.branding.body_font
        p2.font.size = Pt(10)
        p2.font.color.rgb = RgbColor(*self.branding.text_dark)
        p2.space_before = Pt(6)

    def _add_key_facts_box(self, shape, facts: List[Dict]) -> None:
        """Add key facts in a formatted box."""
        tf = shape.text_frame
        tf.word_wrap = True

        # Header
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = "At a Glance"
        run.font.name = self.branding.heading_font
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RgbColor(*self.branding.accent_cyan)

        # Facts
        for fact in facts:
            p = tf.add_paragraph()
            label = fact.get('label', '')
            value = fact.get('value', '')

            run1 = p.add_run()
            run1.text = f"{label}: "
            run1.font.name = self.branding.body_font
            run1.font.size = Pt(10)
            run1.font.bold = True
            run1.font.color.rgb = RgbColor(*self.branding.text_dark)

            run2 = p.add_run()
            run2.text = str(value)
            run2.font.name = self.branding.body_font
            run2.font.size = Pt(10)
            run2.font.color.rgb = RgbColor(*self.branding.text_dark)

            p.space_before = Pt(4)

    def _add_list_section(self, shape, title: str, items: List[str]) -> None:
        """Add a section with a title and bullet list."""
        tf = shape.text_frame
        tf.word_wrap = True

        # Title
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = title
        run.font.name = self.branding.heading_font
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RgbColor(*self.branding.primary_dark)

        # Items
        for item in items[:6]:  # Limit to 6 items
            p = tf.add_paragraph()
            p.text = f"• {item}"
            p.font.name = self.branding.body_font
            p.font.size = Pt(9)
            p.font.color.rgb = RgbColor(*self.branding.text_dark)
            p.space_before = Pt(2)

    def _add_horizontal_badges(self, shape, title: str, items: List[str]) -> None:
        """Add badges/certifications in a horizontal layout."""
        tf = shape.text_frame
        tf.word_wrap = True

        # Title
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = f"{title}: "
        run.font.name = self.branding.heading_font
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RgbColor(*self.branding.primary_dark)

        # Items as comma-separated
        run2 = p.add_run()
        run2.text = " | ".join(items[:5])
        run2.font.name = self.branding.body_font
        run2.font.size = Pt(9)
        run2.font.color.rgb = RgbColor(*self.branding.text_dark)

    def _add_metric_boxes(self, slide, metrics: List[Dict], top: float) -> None:
        """Add metric highlight boxes."""
        box_width = Inches(2.8)
        box_height = Inches(0.8)
        start_left = Inches(0.5)
        spacing = Inches(3.1)

        for i, metric in enumerate(metrics[:4]):  # Max 4 metrics
            left = start_left + (i * spacing)

            # Create box shape
            box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                left, top,
                box_width, box_height
            )
            box.fill.solid()
            box.fill.fore_color.rgb = RgbColor(*self.branding.primary_dark)
            box.line.fill.background()

            # Add text
            tf = box.text_frame
            tf.word_wrap = True

            # Value
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(metric.get('value', 'N/A'))
            run.font.name = self.branding.heading_font
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = RgbColor(*self.branding.text_white)

            # Label
            p2 = tf.add_paragraph()
            p2.alignment = PP_ALIGN.CENTER
            run2 = p2.add_run()
            run2.text = metric.get('label', '')
            run2.font.name = self.branding.body_font
            run2.font.size = Pt(9)
            run2.font.color.rgb = RgbColor(200, 200, 200)

    def _add_financial_chart(self, slide, chart_data: Dict) -> None:
        """Add a financial chart to the slide."""
        from pptx.chart.data import CategoryChartData
        from pptx.enum.chart import XL_LEGEND_POSITION

        revenue_data = chart_data.get('revenue', [])
        if not revenue_data:
            return

        # Create chart data
        chart_data_obj = CategoryChartData()
        chart_data_obj.categories = [d['year'] for d in revenue_data]
        chart_data_obj.add_series('Revenue', [d['value'] for d in revenue_data])

        # Add EBITDA if available
        ebitda_data = chart_data.get('ebitda', [])
        if ebitda_data and len(ebitda_data) == len(revenue_data):
            chart_data_obj.add_series('EBITDA', [d['value'] for d in ebitda_data])

        # Add PAT if available
        pat_data = chart_data.get('pat', [])
        if pat_data and len(pat_data) == len(revenue_data):
            chart_data_obj.add_series('PAT', [d['value'] for d in pat_data])

        # Add chart to slide (positioned on the left)
        chart_shape = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(0.5), Inches(2.2),
            Inches(6.5), Inches(3.5),
            chart_data_obj
        )
        chart = chart_shape.chart

        # Style the chart
        chart.has_legend = True
        chart.legend.include_in_layout = False
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM

        # Style the series colors
        try:
            plot = chart.plots[0]
            if len(plot.series) > 0:
                plot.series[0].format.fill.solid()
                plot.series[0].format.fill.fore_color.rgb = RgbColor(45, 35, 90)  # Dark indigo for Revenue
            if len(plot.series) > 1:
                plot.series[1].format.fill.solid()
                plot.series[1].format.fill.fore_color.rgb = RgbColor(0, 200, 255)  # Cyan for EBITDA
            if len(plot.series) > 2:
                plot.series[2].format.fill.solid()
                plot.series[2].format.fill.fore_color.rgb = RgbColor(255, 100, 130)  # Pink for PAT
        except Exception as e:
            logger.debug(f"Could not style chart series: {e}")

    def _add_investment_highlights(self, slide, highlights: List[Dict], left_offset: float = 0) -> None:
        """Add investment highlights with icons."""
        start_top = Inches(1.4)
        left_margin = Inches(0.5 + left_offset)
        icon_left = Inches(0.3 + left_offset)
        text_width = Inches(12 - left_offset) if left_offset else Inches(11)
        spacing = Inches(1)

        for i, highlight in enumerate(highlights[:5]):
            top = start_top + (i * spacing)

            # Icon circle
            circle = slide.shapes.add_shape(
                MSO_SHAPE.OVAL,
                icon_left, top,
                Inches(0.4), Inches(0.4)
            )
            circle.fill.solid()
            circle.fill.fore_color.rgb = RgbColor(*self.branding.accent_cyan)
            circle.line.fill.background()

            # Text box
            text_box = slide.shapes.add_textbox(
                left_margin, top,
                text_width, Inches(0.9)
            )
            tf = text_box.text_frame
            tf.word_wrap = True

            # Headline
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = highlight.get('headline', '')
            run.font.name = self.branding.heading_font
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RgbColor(*self.branding.primary_dark)

            # Detail
            if highlight.get('detail'):
                p2 = tf.add_paragraph()
                p2.text = highlight.get('detail', '')
                p2.font.name = self.branding.body_font
                p2.font.size = Pt(10)
                p2.font.color.rgb = RgbColor(*self.branding.text_dark)

    def _find_section(self, sections: List[Dict], section_type: str) -> Optional[Dict]:
        """Find a section by type."""
        for section in sections:
            if section.get('type') == section_type:
                return section
        return None
