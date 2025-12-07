"""
Services for Module 6A: Buyer Requests - AI Smart Matching

Implements:
- PBI-BE-M6-09: AI Smart Matching - Category & HS Code (using Catalogs)
- PBI-BE-M6-10: AI Smart Matching - Spec Requirements (using Catalog fields)
- PBI-BE-M6-11: AI Smart Matching - Capability Filter
- PBI-BE-M6-12: Calculate Final Match Score

Updated to match against published catalogs instead of products.
Returns multiple catalogs per UMKM if they have multiple matching catalogs.
"""

import logging
from typing import Dict, List, Optional
import json

from django.db.models import Q, QuerySet
from apps.business_profiles.models import BusinessProfile
from apps.export_analysis.models import ExportAnalysis
from apps.products.models import Product, ProductEnrichment
from apps.catalogs.models import ProductCatalog
from core.services.ai_service import KolosalAIService

logger = logging.getLogger(__name__)


class BuyerRequestMatchingService:
    """
    Service for matching BuyerRequests with UMKM using AI.
    
    Implements all AI Smart Matching services from PBI-BE-M6-09 to M6-12.
    """

    def __init__(self):
        self.ai_service = KolosalAIService()

    def match_buyer_request(self, buyer_request) -> List[Dict]:
        """
        Main matching function - Category only matching.
        
        Returns list of matched published catalogs that match the buyer request category.
        Each catalog includes UMKM info and catalog details.
        Multiple catalogs per UMKM are returned if they match.
        """
        # Only match by category
        matched_catalogs = self._match_category_only(buyer_request)
        
        # Sort by catalog ID (or you can sort by any other field like display_name)
        matched_catalogs.sort(key=lambda x: x["catalog_id"])
        return matched_catalogs

    def _get_category_id_from_name(self, category_name: str) -> Optional[int]:
        """
        Map category name to category_id.
        
        Since there's no category lookup table, we'll use a mapping dictionary.
        This can be extended or moved to a database table later.
        """
        # Category name to ID mapping
        # This should ideally come from a Category model/table
        category_mapping = {
            "Makanan Olahan": 1,
            "makanan olahan": 1,
            "Kerajinan": 2,
            "kerajinan": 2,
            "Tekstil": 3,
            "tekstil": 3,
            "Furniture": 4,
            "furniture": 4,
            "Mebel": 4,
            "mebel": 4,
            # Add more mappings as needed
        }
        
        # Try direct lookup
        if category_name in category_mapping:
            return category_mapping[category_name]
        
        # Try case-insensitive lookup
        category_name_lower = category_name.lower().strip()
        for name, cat_id in category_mapping.items():
            if name.lower() == category_name_lower:
                return cat_id
        
        # If not found in mapping, return None
        # The caller should handle this by returning empty results
        logger.warning(f"Category name '{category_name}' not found in mapping. Available mappings: {list(set(category_mapping.values()))}")
        return None

    def _match_category_only(self, buyer_request) -> List[Dict]:
        """
        Simplified matching - Category only.
        
        Input: BuyerRequest (product_category)
        Query: Published Catalogs WHERE product.category_id matches buyer.product_category
        Output: Array of matched catalogs with catalog details
        """
        # Get published catalogs (via product relationship)
        catalogs = ProductCatalog.objects.filter(
            is_published=True
        ).select_related(
            "product__business__user",
            "product__enrichment"
        ).prefetch_related("images")
        
        # Determine category_id from product_category
        category_id = None
        
        # Try to convert to int first (if product_category is numeric)
        try:
            category_id = int(buyer_request.product_category)
        except (ValueError, TypeError):
            # If not numeric, try to map from category name
            category_id = self._get_category_id_from_name(buyer_request.product_category)
        
        # Filter by category_id if we have one
        if category_id is not None:
            catalogs = catalogs.filter(product__category_id=category_id)
        else:
            # If we can't determine category_id, return empty
            logger.warning(f"Could not determine category_id for '{buyer_request.product_category}'. Returning empty results.")
            return []

        matched_catalogs = []
        
        for catalog in catalogs:
            umkm_id = catalog.product.business.user_id

            # Get primary image URL
            primary_image = catalog.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = catalog.images.first()
            image_url = primary_image.url if primary_image else None

            matched_catalogs.append({
                "catalog_id": catalog.id,
                "umkm_id": umkm_id,
                "catalog": {
                    "id": catalog.id,
                    "display_name": catalog.display_name,
                    "export_description": catalog.export_description,
                    "marketing_description": catalog.marketing_description,
                    "technical_specs": catalog.technical_specs,
                    "tags": catalog.tags,
                    "min_order_quantity": float(catalog.min_order_quantity),
                    "unit_type": catalog.unit_type,
                    "available_stock": catalog.available_stock,
                    "base_price_exw": float(catalog.base_price_exw),
                    "base_price_fob": float(catalog.base_price_fob) if catalog.base_price_fob else None,
                    "base_price_cif": float(catalog.base_price_cif) if catalog.base_price_cif else None,
                    "lead_time_days": catalog.lead_time_days,
                    "primary_image_url": image_url,
                }
            })

        return matched_catalogs

    def _match_category_and_hs_code(self, buyer_request) -> List[Dict]:
        """
        PBI-BE-M6-09: AI Smart Matching - Category & HS Code (Updated for Catalogs)
        
        Input: BuyerRequest (category, hs_code_target)
        Query: Published Catalogs WHERE product.category LIKE buyer.category
        Query: ProductEnrichment WHERE hs_code starts with buyer.hs_code_target
        Score calculation: exact HS match = 100, same category = 50, partial = 25
        Output: Array of matched catalogs with base_score, catalog_id, and catalog details
        """
        # Get published catalogs matching category (via product relationship)
        # product_category in BuyerRequest is a string, category_id in Product is an integer
        # Try to match by converting product_category to int if possible
        catalogs = ProductCatalog.objects.filter(
            is_published=True
        ).select_related(
            "product__business__user",
            "product__enrichment"
        ).prefetch_related("images")
        
        # Filter by category - try to match category_id as integer
        # If product_category is numeric, use exact match; otherwise get all and filter later
        try:
            # Try to convert buyer_request.product_category to int for exact match
            category_id = int(buyer_request.product_category)
            catalogs = catalogs.filter(product__category_id=category_id)
        except (ValueError, TypeError):
            # If product_category is not numeric (e.g., category name), 
            # we can't match directly with category_id (integer field)
            # For now, get all published catalogs and let scoring handle it
            # In production, you might want to add a category name lookup table
            logger.warning(f"product_category '{buyer_request.product_category}' is not numeric, cannot match with category_id")
            # Return empty or all catalogs - for now, return all and let other scoring factors handle it
            pass

        matched_catalogs = []
        
        for catalog in catalogs:
            umkm_id = catalog.product.business.user_id
            base_score = 50  # Same category = 50

            # Check HS code match if available
            if buyer_request.hs_code_target:
                try:
                    enrichment = catalog.product.enrichment
                    if enrichment and enrichment.hs_code_recommendation:
                        hs_code = enrichment.hs_code_recommendation
                        target_hs = buyer_request.hs_code_target

                        # Exact match = 100
                        if hs_code == target_hs:
                            base_score = 100
                        # Partial match (starts with) = 75
                        elif hs_code.startswith(target_hs[:6]) or target_hs.startswith(hs_code[:6]):
                            base_score = 75
                        # Same category but different HS = 25
                        else:
                            base_score = 25
                except ProductEnrichment.DoesNotExist:
                    pass

            # Get primary image URL
            primary_image = catalog.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = catalog.images.first()
            image_url = primary_image.url if primary_image else None

            matched_catalogs.append({
                "catalog_id": catalog.id,
                "umkm_id": umkm_id,
                "base_score": base_score,
                "catalog": {
                    "id": catalog.id,
                    "display_name": catalog.display_name,
                    "export_description": catalog.export_description,
                    "marketing_description": catalog.marketing_description,
                    "technical_specs": catalog.technical_specs,
                    "tags": catalog.tags,
                    "min_order_quantity": float(catalog.min_order_quantity),
                    "unit_type": catalog.unit_type,
                    "available_stock": catalog.available_stock,
                    "base_price_exw": float(catalog.base_price_exw),
                    "base_price_fob": float(catalog.base_price_fob) if catalog.base_price_fob else None,
                    "base_price_cif": float(catalog.base_price_cif) if catalog.base_price_cif else None,
                    "lead_time_days": catalog.lead_time_days,
                    "primary_image_url": image_url,
                }
            })

        return matched_catalogs

    def _match_spec_requirements(
        self,
        spec_requirements: str,
        keyword_tags: List[str],
        base_matches: List[Dict]
    ) -> Dict[int, int]:
        """
        PBI-BE-M6-10: AI Smart Matching - Spec Requirements (Updated for Catalogs)
        
        Input: spec_requirements (text), keyword_tags (array)
        LLM Prompt: "Ekstrak kata kunci penting dari spesifikasi: {spec_requirements}"
        Compare with Catalog fields: export_description, marketing_description, technical_specs, tags
        Text similarity scoring: keyword overlap, semantic matching
        Bonus score for matching keyword_tags
        Output: spec_match_score (0-100) per catalog
        """
        # Extract keywords from spec using AI
        try:
            prompt = f"Ekstrak kata kunci penting dari spesifikasi berikut (berikan hanya kata kunci, pisahkan dengan koma):\n\n{spec_requirements}"
            system_prompt = "Kamu adalah ahli yang mengekstrak kata kunci dari spesifikasi produk. Berikan hanya kata kunci yang relevan, pisahkan dengan koma."
            
            ai_keywords_text = self.ai_service._call_ai(prompt, system_prompt)
            ai_keywords = [k.strip().lower() for k in ai_keywords_text.split(",") if k.strip()]
        except Exception as e:
            logger.error(f"Error extracting keywords from spec: {e}")
            ai_keywords = []

        # Combine with keyword_tags
        all_keywords = set(ai_keywords + [tag.lower() for tag in keyword_tags])

        spec_scores = {}
        
        for match in base_matches:
            catalog_id = match["catalog_id"]
            catalog_data = match["catalog"]
            
            # Combine all catalog text fields for matching
            export_desc = (catalog_data.get("export_description") or "").lower()
            marketing_desc = (catalog_data.get("marketing_description") or "").lower()
            technical_specs = json.dumps(catalog_data.get("technical_specs") or {}).lower()
            tags_list = catalog_data.get("tags") or []
            tags_text = " ".join([str(tag).lower() for tag in tags_list])
            
            combined_text = f"{export_desc} {marketing_desc} {technical_specs} {tags_text}"

            # Count keyword matches
            matches = sum(1 for keyword in all_keywords if keyword in combined_text)
            if all_keywords:
                score = min(100, int((matches / len(all_keywords)) * 100))
            else:
                score = 50  # Default if no keywords

            # Bonus for keyword_tags match in catalog tags
            if keyword_tags and tags_list:
                tag_matches = sum(1 for tag in keyword_tags if str(tag).lower() in tags_text)
                tag_bonus = min(20, int((tag_matches / len(keyword_tags)) * 20))
                score = min(100, score + tag_bonus)

            spec_scores[catalog_id] = score

        return spec_scores

    def _filter_by_capability(
        self,
        min_rank_required: int,
        destination_country: str,
        base_matches: List[Dict]
    ) -> Dict[int, int]:
        """
        PBI-BE-M6-11: AI Smart Matching - Capability Filter
        
        Input: min_rank_required, destination_country
        Filter: UMKM with rank >= min_rank_required
        Check: UMKM has ExportAnalysis for destination_country
        Check: UMKM has matching certifications from BusinessProfile
        Bonus score: +20 if exported to that country before
        Bonus score: +10 per relevant certification
        Output: capability_score (0-100) per UMKM
        """
        capability_scores = {}
        
        for match in base_matches:
            umkm_id = match["umkm_id"]
            score = 0

            try:
                business_profile = BusinessProfile.objects.get(user_id=umkm_id)
                
                # Check rank (for now, use certification_count as rank proxy)
                # In future, implement actual ranking system
                rank = business_profile.certification_count
                if rank < min_rank_required:
                    capability_scores[umkm_id] = 0
                    continue

                # Base score based on rank
                score = min(60, rank * 10)

                # Check export experience to destination country
                has_export_experience = ExportAnalysis.objects.filter(
                    product__business=business_profile,
                    target_country__country_code=destination_country
                ).exists()
                
                if has_export_experience:
                    score += 20

                # Bonus for certifications
                certifications = business_profile.certifications or []
                certification_bonus = min(20, len(certifications) * 10)
                score += certification_bonus

                score = min(100, score)
            except BusinessProfile.DoesNotExist:
                score = 0

            capability_scores[umkm_id] = score

        return capability_scores

    def _match_volume_requirements(
        self,
        target_volume: int,
        base_matches: List[Dict]
    ) -> Dict[int, int]:
        """
        Optional volume matching bonus.
        
        Checks if catalog can fulfill target volume:
        - available_stock >= target_volume: +10 bonus
        - min_order_quantity <= target_volume: +5 bonus
        - Both: +15 bonus
        
        Output: volume_bonus (0-15) per catalog
        """
        if not target_volume or target_volume <= 0:
            return {}
        
        volume_bonuses = {}
        
        for match in base_matches:
            catalog_id = match["catalog_id"]
            catalog_data = match["catalog"]
            
            bonus = 0
            available_stock = catalog_data.get("available_stock", 0)
            min_order_qty = catalog_data.get("min_order_quantity", 0)
            
            # Check if stock can fulfill target
            if available_stock >= target_volume:
                bonus += 10
            
            # Check if min order is acceptable
            if min_order_qty <= target_volume:
                bonus += 5
            
            volume_bonuses[catalog_id] = min(15, bonus)
        
        return volume_bonuses

    def _calculate_buyer_bonuses(self, base_matches: List[Dict]) -> Dict[int, int]:
        """
        Calculate buyer-friendly bonuses based on catalog attributes.
        
        Factors considered:
        - Pricing completeness (has FOB/CIF): +5
        - Lead time (shorter is better): +5 to +10
        - Stock availability (higher is better): +5 to +10
        
        Output: buyer_bonus (0-25) per catalog
        """
        buyer_bonuses = {}
        
        for match in base_matches:
            catalog_id = match["catalog_id"]
            catalog_data = match["catalog"]
            
            bonus = 0
            
            # Pricing completeness bonus
            if catalog_data.get("base_price_fob") or catalog_data.get("base_price_cif"):
                bonus += 5
            
            # Lead time bonus (shorter is better)
            lead_time = catalog_data.get("lead_time_days", 30)
            if lead_time <= 7:
                bonus += 10
            elif lead_time <= 14:
                bonus += 7
            elif lead_time <= 21:
                bonus += 5
            
            # Stock availability bonus
            stock = catalog_data.get("available_stock", 0)
            if stock >= 1000:
                bonus += 10
            elif stock >= 500:
                bonus += 7
            elif stock >= 100:
                bonus += 5
            
            buyer_bonuses[catalog_id] = min(25, bonus)
        
        return buyer_bonuses

    def _calculate_final_match_score(
        self,
        base_score: int,
        spec_match_score: int,
        capability_score: int,
        volume_bonus: int = 0,
        buyer_bonus: int = 0
    ) -> int:
        """
        PBI-BE-M6-12: Calculate Final Match Score (Updated)
        
        Input: base_score, spec_match_score, capability_score, volume_bonus, buyer_bonus
        Formula: final_score = (base_score × 0.35) + (spec_match × 0.3) + (capability × 0.25) + (volume_bonus × 0.05) + (buyer_bonus × 0.05)
        Round to integer (0-100)
        Threshold: only return catalogs with score >= 70
        Output: final_match_score per catalog
        """
        # Base scores weighted
        weighted_base = base_score * 0.35
        weighted_spec = spec_match_score * 0.3
        weighted_capability = capability_score * 0.25
        
        # Bonuses (smaller weight but still impactful)
        weighted_volume = volume_bonus * 0.05
        weighted_buyer = buyer_bonus * 0.05
        
        final_score = weighted_base + weighted_spec + weighted_capability + weighted_volume + weighted_buyer
        return int(round(final_score))

