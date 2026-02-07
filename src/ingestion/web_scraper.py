"""
Web scraper for fetching public company data.
Extracts business information from company websites and public sources.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("web_scraper")

# Try to import required packages
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed. Run: pip install requests")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not installed. Run: pip install beautifulsoup4")


class WebScraper:
    """
    Scrapes public company data from websites.
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the web scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session() if REQUESTS_AVAILABLE else None

        if self.session:
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

    def scrape_company_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape company website for business information.

        Args:
            url: Company website URL

        Returns:
            Dictionary with extracted information
        """
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            logger.error("Cannot scrape: missing dependencies")
            return {}

        logger.info(f"Scraping company website: {url}")

        data = {
            "url": url,
            "company_name": None,
            "description": None,
            "products": [],
            "services": [],
            "about": None,
            "contact": {},
            "social_links": [],
            "meta_description": None
        }

        try:
            # Fetch main page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract metadata
            data["company_name"] = self._extract_company_name(soup)
            data["meta_description"] = self._extract_meta_description(soup)

            # Extract main content
            data["description"] = self._extract_description(soup)
            data["about"] = self._extract_about_content(soup, url)

            # Extract products/services
            data["products"] = self._extract_products(soup, url)

            # Extract contact info
            data["contact"] = self._extract_contact_info(soup)

            # Extract social links
            data["social_links"] = self._extract_social_links(soup)

            logger.info(f"Successfully scraped: {url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to scrape {url}: {e}")

        return data

    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from the page."""
        # Try title tag
        title = soup.find("title")
        if title:
            title_text = title.get_text().strip()
            # Remove common suffixes
            for suffix in [" - Home", " | Home", " - Official", " | Official"]:
                if title_text.endswith(suffix):
                    title_text = title_text[:-len(suffix)]
            return title_text

        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        return None

    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"].strip()

        meta = soup.find("meta", attrs={"property": "og:description"})
        if meta and meta.get("content"):
            return meta["content"].strip()

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main business description."""
        # Look for common description containers
        selectors = [
            ".company-description",
            ".about-text",
            "#about-us p",
            ".hero-text",
            "main p",
            "article p"
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = " ".join([el.get_text().strip() for el in elements[:3]])
                if len(text) > 100:
                    return text[:500]

        # Fallback: get first substantial paragraph
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if len(text) > 100:
                return text[:500]

        return None

    def _extract_about_content(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Try to extract about page content."""
        # Find about page link
        about_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "about" in href:
                about_link = urljoin(base_url, a["href"])
                break

        if about_link:
            try:
                response = self.session.get(about_link, timeout=self.timeout)
                response.raise_for_status()
                about_soup = BeautifulSoup(response.text, "html.parser")

                # Get main content
                main = about_soup.find("main") or about_soup.find("article") or about_soup
                paragraphs = main.find_all("p")

                text = " ".join([p.get_text().strip() for p in paragraphs[:5]])
                if len(text) > 100:
                    return text[:1000]
            except:
                pass

        return None

    def _extract_products(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract products or services."""
        products = []

        # Look for products/services section
        selectors = [
            ".products li",
            ".services li",
            "#products li",
            "#services li",
            ".product-item",
            ".service-item"
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for el in elements[:10]:
                text = el.get_text().strip()
                if text and len(text) < 100:
                    products.append(text)

        return products[:10]

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information."""
        contact = {}

        # Email
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact["email"] = emails[0]

        # Phone
        phone_pattern = r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{8,15}"
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            contact["phone"] = phones[0]

        # Address
        address_el = soup.find(class_=re.compile("address|location", re.I))
        if address_el:
            contact["address"] = address_el.get_text().strip()[:200]

        return contact

    def _extract_social_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract social media links."""
        social_links = []
        social_domains = [
            "linkedin.com", "twitter.com", "facebook.com",
            "instagram.com", "youtube.com"
        ]

        for a in soup.find_all("a", href=True):
            href = a["href"]
            for domain in social_domains:
                if domain in href:
                    social_links.append({
                        "platform": domain.split(".")[0],
                        "url": href
                    })
                    break

        return social_links

    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of scraped data
        """
        results = []
        for url in urls:
            data = self.scrape_company_website(url)
            if data:
                results.append(data)
        return results


def get_web_scraper(timeout: int = 10) -> WebScraper:
    """Factory function to create a WebScraper."""
    return WebScraper(timeout)
