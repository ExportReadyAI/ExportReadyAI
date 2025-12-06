"""
HS Code Loader Utility

Utility untuk memuat dan mencari HS codes dari data CSV.
Digunakan untuk memberikan context ke AI dalam menentukan HS code yang tepat.
"""

import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HSCodeLoader:
    """Utility class untuk load dan search HS codes dari CSV files."""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.hs_file = self.base_dir / "data_HS" / "harmonized-system.csv"
        self.sections_file = self.base_dir / "data_HS" / "sections.csv"
        self._hs_data: Optional[List[Dict]] = None
        self._sections: Optional[Dict[str, str]] = None

    def _load_hs_data(self) -> List[Dict]:
        """Load HS code data dari CSV file."""
        if self._hs_data is not None:
            return self._hs_data

        if not self.hs_file.exists():
            logger.warning(f"HS code file not found: {self.hs_file}")
            return []

        hs_data = []
        try:
            with open(self.hs_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    hs_data.append({
                        "section": row.get("section", ""),
                        "hscode": row.get("hscode", ""),
                        "description": row.get("description", ""),
                        "parent": row.get("parent", ""),
                        "level": int(row.get("level", 0)),
                    })
            self._hs_data = hs_data
            logger.info(f"Loaded {len(hs_data)} HS codes from CSV")
        except Exception as e:
            logger.error(f"Error loading HS codes: {e}", exc_info=True)
            return []

        return self._hs_data

    def _load_sections(self) -> Dict[str, str]:
        """Load section names dari CSV file."""
        if self._sections is not None:
            return self._sections

        if not self.sections_file.exists():
            logger.warning(f"Sections file not found: {self.sections_file}")
            return {}

        sections = {}
        try:
            with open(self.sections_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "section" in reader.fieldnames and "name" in reader.fieldnames:
                    for row in reader:
                        section_key = row.get("section", "").strip()
                        name_key = row.get("name", "").strip()
                        if section_key and name_key:
                            sections[section_key] = name_key
            self._sections = sections
            logger.debug(f"Loaded {len(sections)} sections")
        except Exception as e:
            logger.error(f"Error loading sections: {e}", exc_info=True)
            return {}

        return sections

    def search_hs_codes(
        self,
        keywords: str,
        max_results: int = 20,
        min_level: int = 6,
    ) -> List[Dict]:
        """
        Search HS codes berdasarkan keywords.

        Args:
            keywords: Keywords untuk search (bisa nama produk, material, dll)
            max_results: Maximum number of results to return
            min_level: Minimum level of HS code detail (6 = 6-digit, 8 = 8-digit)

        Returns:
            List of HS code dictionaries yang relevan
        """
        hs_data = self._load_hs_data()
        if not hs_data:
            return []

        # Normalize keywords
        keywords_lower = keywords.lower()
        keywords_list = keywords_lower.split()

        # Score each HS code based on keyword matches
        scored_results = []
        for item in hs_data:
            if item["level"] < min_level:
                continue

            description_lower = item["description"].lower()
            score = 0

            # Exact phrase match gets highest score
            if keywords_lower in description_lower:
                score += 15

            # Individual keyword matches
            for keyword in keywords_list:
                if len(keyword) > 2:  # Only match words longer than 2 chars
                    if keyword in description_lower:
                        score += 2

            # Prefer 8-digit codes (most specific)
            if item["level"] == 8:
                score += 3
            elif item["level"] == 6:
                score += 1

            if score > 0:
                scored_results.append((score, item))

        # Sort by score (descending) and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored_results[:max_results]]

        return results

    def get_hs_code_context(
        self,
        product_name: str,
        material_composition: str = "",
        category: str = "",
        max_codes: int = 15,
    ) -> str:
        """
        Generate context string untuk AI prompt dengan HS codes yang relevan.

        Args:
            product_name: Nama produk
            material_composition: Komposisi material
            category: Kategori produk
            max_codes: Maximum number of HS codes to include

        Returns:
            Formatted string dengan HS codes yang relevan untuk context AI
        """
        # Combine search terms
        search_terms = f"{product_name} {material_composition} {category}".strip()

        # Search for relevant HS codes
        relevant_codes = self.search_hs_codes(
            keywords=search_terms,
            max_results=max_codes,
            min_level=6,  # At least 6-digit codes
        )

        if not relevant_codes:
            return ""

        # Format context
        context_lines = ["RELEVANT HS CODES (pilih yang paling sesuai):"]
        sections = self._load_sections()

        for code in relevant_codes:
            section_name = sections.get(code["section"], code["section"])
            # Format: HS Code | Description | Section
            hscode = code["hscode"]
            # Pad to 8 digits if needed
            if len(hscode) == 6:
                hscode = hscode + "00"
            context_lines.append(
                f"- {hscode:8s} | {code['description']} | Section {code['section']}: {section_name}"
            )

        return "\n".join(context_lines)


# Singleton instance
_hs_loader_instance: Optional[HSCodeLoader] = None


def get_hs_loader() -> HSCodeLoader:
    """Get singleton instance of HS Code Loader."""
    global _hs_loader_instance
    if _hs_loader_instance is None:
        _hs_loader_instance = HSCodeLoader()
    return _hs_loader_instance
