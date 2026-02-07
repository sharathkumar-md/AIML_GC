"""
Image fetcher for sourcing stock images from Unsplash and Pexels.
Used to add relevant visuals to Investment Teaser presentations.
"""

import os
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict
from io import BytesIO

logger = logging.getLogger("image_fetcher")


class ImageFetcher:
    """
    Fetches stock images from Unsplash and Pexels APIs.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the image fetcher.

        Args:
            cache_dir: Directory to cache downloaded images
        """
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")

        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent.parent / "output" / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ImageFetcher initialized. Cache dir: {self.cache_dir}")
        logger.info(f"Unsplash API: {'configured' if self.unsplash_key else 'not configured'}")
        logger.info(f"Pexels API: {'configured' if self.pexels_key else 'not configured'}")

    def fetch_image(
        self,
        keywords: List[str],
        width: int = 800,
        height: int = 600,
        orientation: str = "landscape"
    ) -> Optional[str]:
        """
        Fetch an image based on keywords.

        Args:
            keywords: List of search keywords
            width: Desired image width
            height: Desired image height
            orientation: "landscape", "portrait", or "squarish"

        Returns:
            Path to downloaded image or None if failed
        """
        query = " ".join(keywords[:3])  # Use first 3 keywords
        logger.info(f"Fetching image for: {query}")

        # Try Unsplash first
        if self.unsplash_key:
            image_path = self._fetch_from_unsplash(query, width, height, orientation)
            if image_path:
                return image_path

        # Fall back to Pexels
        if self.pexels_key:
            image_path = self._fetch_from_pexels(query, width, height, orientation)
            if image_path:
                return image_path

        logger.warning(f"Could not fetch image for: {query}")
        return None

    def _fetch_from_unsplash(
        self,
        query: str,
        width: int,
        height: int,
        orientation: str
    ) -> Optional[str]:
        """Fetch image from Unsplash API."""
        try:
            # Search for photos
            search_url = "https://api.unsplash.com/search/photos"
            params = {
                "query": query,
                "per_page": 1,
                "orientation": orientation,
                "client_id": self.unsplash_key
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.debug(f"No Unsplash results for: {query}")
                return None

            # Get the first result
            photo = results[0]
            image_url = photo.get("urls", {}).get("regular", "")

            if not image_url:
                return None

            # Download the image
            return self._download_image(image_url, query, "unsplash")

        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
            return None

    def _fetch_from_pexels(
        self,
        query: str,
        width: int,
        height: int,
        orientation: str
    ) -> Optional[str]:
        """Fetch image from Pexels API."""
        try:
            search_url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_key
            }
            params = {
                "query": query,
                "per_page": 1,
                "orientation": orientation
            }

            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            photos = data.get("photos", [])

            if not photos:
                logger.debug(f"No Pexels results for: {query}")
                return None

            # Get the first result
            photo = photos[0]
            image_url = photo.get("src", {}).get("large", "")

            if not image_url:
                return None

            # Download the image
            return self._download_image(image_url, query, "pexels")

        except Exception as e:
            logger.error(f"Pexels API error: {e}")
            return None

    def _download_image(
        self,
        url: str,
        query: str,
        source: str
    ) -> Optional[str]:
        """Download image from URL and save to cache."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Generate filename from query
            safe_query = "".join(c if c.isalnum() else "_" for c in query)[:30]
            filename = f"{safe_query}_{source}.jpg"
            filepath = self.cache_dir / filename

            # Save the image
            with open(filepath, "wb") as f:
                f.write(response.content)

            logger.info(f"Downloaded image: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None

    def get_sector_keywords(self, sector: str) -> List[str]:
        """
        Get relevant image keywords for a sector.

        Args:
            sector: Company sector

        Returns:
            List of search keywords
        """
        sector_keywords = {
            "manufacturing": ["factory", "industrial", "machinery", "production line"],
            "technology": ["technology", "software", "digital", "computer", "server room"],
            "pharma": ["pharmaceutical", "laboratory", "medicine", "research", "healthcare"],
            "logistics": ["logistics", "warehouse", "shipping", "truck", "supply chain"],
            "consumer": ["retail", "shopping", "products", "store", "consumer goods"],
            "electronics": ["electronics", "circuit board", "semiconductor", "technology"],
            "entertainment": ["cinema", "entertainment", "theater", "audience", "movie"],
        }

        return sector_keywords.get(sector, ["business", "corporate", "office"])

    def fetch_sector_image(self, sector: str) -> Optional[str]:
        """
        Fetch a relevant image for a sector.

        Args:
            sector: Company sector

        Returns:
            Path to downloaded image or None
        """
        keywords = self.get_sector_keywords(sector)
        return self.fetch_image(keywords)


def get_image_fetcher(cache_dir: Optional[str] = None) -> ImageFetcher:
    """Factory function to create an ImageFetcher."""
    return ImageFetcher(cache_dir)
