"""
Anonymization module for creating "Blind" investment teasers.
Removes or replaces company-identifying information while preserving data accuracy.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("anonymizer")


@dataclass
class AnonymizationResult:
    """Result of anonymization process."""
    original: str
    anonymized: str
    replacements: Dict[str, str]


class Anonymizer:
    """
    Anonymizes company information for blind investment teasers.
    """

    def __init__(self, company_name: str, codename: str):
        """
        Initialize anonymizer with company details.

        Args:
            company_name: Original company name
            codename: Project codename to use
        """
        self.company_name = company_name
        self.codename = codename
        self.replacements: Dict[str, str] = {}

        # Build replacement patterns
        self._build_patterns()

        logger.info(f"Anonymizer initialized: {company_name} -> Project {codename}")

    def _build_patterns(self) -> None:
        """Build replacement patterns for anonymization."""
        # Company name variations
        name_variations = self._generate_name_variations(self.company_name)

        for variation in name_variations:
            self.replacements[variation] = f"Project {self.codename}"
            self.replacements[variation.lower()] = f"Project {self.codename}"
            self.replacements[variation.upper()] = f"PROJECT {self.codename.upper()}"

        # Common patterns to anonymize
        self.generic_replacements = {
            # Specific cities/locations (keep generic region)
            r'\bNoida\b': 'NCR Region',
            r'\bPune\b': 'Western India',
            r'\bMumbai\b': 'Western India',
            r'\bBangalore\b': 'Southern India',
            r'\bBengaluru\b': 'Southern India',
            r'\bChennai\b': 'Southern India',
            r'\bHyderabad\b': 'Southern India',
            r'\bAhmedabad\b': 'Western India',
            r'\bDelhi\b': 'NCR Region',
            r'\bGurgaon\b': 'NCR Region',
            r'\bGurugram\b': 'NCR Region',
            r'\bKolkata\b': 'Eastern India',
        }

    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate common variations of a company name."""
        variations = [name]

        # Without common suffixes
        suffixes = [
            ' Limited', ' Ltd', ' Ltd.', ' Pvt', ' Private',
            ' Inc', ' Inc.', ' Corp', ' Corporation',
            ' Industries', ' India', ' Global'
        ]

        for suffix in suffixes:
            if name.endswith(suffix):
                variations.append(name[:-len(suffix)].strip())
            variations.append(name + suffix)

        # Split by spaces and add individual significant words
        words = name.split()
        if len(words) > 1:
            variations.append(words[0])  # First word

        return list(set(variations))

    def anonymize_text(self, text: str) -> str:
        """
        Anonymize a text string.

        Args:
            text: Original text

        Returns:
            Anonymized text
        """
        if not text:
            return text

        result = text

        # Replace company name variations
        for original, replacement in self.replacements.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            result = pattern.sub(replacement, result)

        # Apply generic location replacements (optional - can be configured)
        # for pattern, replacement in self.generic_replacements.items():
        #     result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def anonymize_for_slide(self, text: str, preserve_numbers: bool = True) -> str:
        """
        Anonymize text specifically for slide content.

        Args:
            text: Original text
            preserve_numbers: Whether to preserve numerical data

        Returns:
            Anonymized text suitable for slides
        """
        result = self.anonymize_text(text)

        # Remove any remaining potential identifiers
        # Remove URLs that might contain company name
        url_pattern = r'https?://[^\s]+'
        result = re.sub(url_pattern, '[Website]', result)

        # Remove email addresses
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        result = re.sub(email_pattern, '[Email]', result)

        return result

    def create_anonymous_description(self, original_description: str) -> str:
        """
        Create an anonymized business description.

        Args:
            original_description: Original business description

        Returns:
            Anonymized description
        """
        # Anonymize the text
        result = self.anonymize_text(original_description)

        # Replace first-person references
        result = result.replace("Our company", "The Company")
        result = result.replace("our company", "the Company")
        result = result.replace("We are", "The Company is")
        result = result.replace("we are", "the Company is")

        return result

    def get_anonymous_reference(self) -> str:
        """Get the anonymous reference name for the company."""
        return f"Project {self.codename}"

    def anonymize_client_list(self, clients: List[str]) -> List[str]:
        """
        Anonymize a list of client names.

        Args:
            clients: List of client names

        Returns:
            List of anonymized client descriptions
        """
        anonymized = []
        categories = {
            'fmcg': ['Global FMCG Major', 'Leading Consumer Goods Company'],
            'auto': ['Major Automotive OEM', 'Leading Auto Manufacturer'],
            'tech': ['Global Technology Company', 'Leading IT Services Firm'],
            'bank': ['Leading Private Bank', 'Major Financial Institution'],
            'pharma': ['Global Pharmaceutical Company', 'Leading Healthcare Firm'],
        }

        # Categorize and anonymize clients
        for i, client in enumerate(clients):
            client_lower = client.lower()

            # Try to categorize
            if any(word in client_lower for word in ['unilever', 'nestle', 'p&g', 'danone']):
                anonymized.append(f"Global FMCG Major #{i+1}")
            elif any(word in client_lower for word in ['tata', 'mahindra', 'honda', 'toyota']):
                anonymized.append(f"Leading Automotive OEM #{i+1}")
            elif any(word in client_lower for word in ['infosys', 'tcs', 'wipro', 'accenture']):
                anonymized.append(f"Global IT Services Company #{i+1}")
            else:
                anonymized.append(f"Key Client #{i+1}")

        return anonymized


def create_anonymizer(company_name: str, codename: str) -> Anonymizer:
    """
    Factory function to create an Anonymizer.

    Args:
        company_name: Original company name
        codename: Project codename

    Returns:
        Configured Anonymizer instance
    """
    return Anonymizer(company_name, codename)
