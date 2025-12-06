"""
Services for Module 6A: Buyer Requests - AI Smart Matching

Implements:
- PBI-BE-M6-09: AI Smart Matching - Category & HS Code
- PBI-BE-M6-10: AI Smart Matching - Spec Requirements
- PBI-BE-M6-11: AI Smart Matching - Capability Filter
- PBI-BE-M6-12: Calculate Final Match Score
"""

import logging
from typing import Dict, List, Optional

from django.db.models import Q, QuerySet
from apps.business_profiles.models import BusinessProfile
from apps.export_analysis.models import ExportAnalysis
from apps.products.models import Product, ProductEnrichment
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
        Main matching function that combines all matching services.
        
        Returns list of matched UMKM with final_match_score >= 70.
        """
        # Step 1: Get base matches by category and HS code
        base_matches = self._match_category_and_hs_code(buyer_request)
        
        if not base_matches:
            return []

        # Step 2: Calculate spec match scores
        spec_scores = self._match_spec_requirements(
            buyer_request.spec_requirements,
            buyer_request.keyword_tags,
            base_matches
        )

        # Step 3: Calculate capability scores
        capability_scores = self._filter_by_capability(
            buyer_request.min_rank_required,
            buyer_request.destination_country,
            base_matches
        )

        # Step 4: Calculate final match scores
        matched_umkm = []
        for umkm_data in base_matches:
            umkm_id = umkm_data["umkm_id"]
            base_score = umkm_data["base_score"]
            spec_score = spec_scores.get(umkm_id, 0)
            capability_score = capability_scores.get(umkm_id, 0)

            final_score = self._calculate_final_match_score(
                base_score, spec_score, capability_score
            )

            # Only include if score >= 70
            if final_score >= 70:
                matched_umkm.append({
                    **umkm_data,
                    "spec_match_score": spec_score,
                    "capability_score": capability_score,
                    "final_match_score": final_score,
                })

        # Sort by final_match_score DESC
        matched_umkm.sort(key=lambda x: x["final_match_score"], reverse=True)
        return matched_umkm

    def _match_category_and_hs_code(self, buyer_request) -> List[Dict]:
        """
        PBI-BE-M6-09: AI Smart Matching - Category & HS Code
        
        Input: BuyerRequest (category, hs_code_target)
        Query: Products WHERE category LIKE buyer.category
        Query: ProductEnrichment WHERE hs_code starts with buyer.hs_code_target
        Score calculation: exact HS match = 100, same category = 50, partial = 25
        Output: Array of matched UMKM with base_score
        """
        # Get products matching category
        products = Product.objects.filter(
            category_id__icontains=buyer_request.product_category
        ).select_related("business__user")

        matched_umkm = {}
        
        for product in products:
            umkm_id = product.business.user_id
            if umkm_id not in matched_umkm:
                matched_umkm[umkm_id] = {
                    "umkm_id": umkm_id,
                    "base_score": 50,  # Same category = 50
                }

            # Check HS code match if available
            if buyer_request.hs_code_target:
                try:
                    enrichment = product.enrichment
                    if enrichment and enrichment.hs_code_recommendation:
                        hs_code = enrichment.hs_code_recommendation
                        target_hs = buyer_request.hs_code_target

                        # Exact match = 100
                        if hs_code == target_hs:
                            matched_umkm[umkm_id]["base_score"] = 100
                        # Partial match (starts with) = 75
                        elif hs_code.startswith(target_hs[:6]) or target_hs.startswith(hs_code[:6]):
                            if matched_umkm[umkm_id]["base_score"] < 75:
                                matched_umkm[umkm_id]["base_score"] = 75
                        # Same category but different HS = 25
                        else:
                            if matched_umkm[umkm_id]["base_score"] < 25:
                                matched_umkm[umkm_id]["base_score"] = 25
                except ProductEnrichment.DoesNotExist:
                    pass

        return list(matched_umkm.values())

    def _match_spec_requirements(
        self,
        spec_requirements: str,
        keyword_tags: List[str],
        base_matches: List[Dict]
    ) -> Dict[int, int]:
        """
        PBI-BE-M6-10: AI Smart Matching - Spec Requirements
        
        Input: spec_requirements (text), keyword_tags (array)
        LLM Prompt: "Ekstrak kata kunci penting dari spesifikasi: {spec_requirements}"
        Compare with Product.description_local and quality_specs
        Text similarity scoring: keyword overlap, semantic matching
        Bonus score for matching keyword_tags
        Output: spec_match_score (0-100) per UMKM
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
            umkm_id = match["umkm_id"]
            score = 0

            # Get all products for this UMKM
            try:
                business_profile = BusinessProfile.objects.get(user_id=umkm_id)
                products = Product.objects.filter(business=business_profile)
                
                max_product_score = 0
                for product in products:
                    product_text = f"{product.description_local} {product.material_composition}".lower()
                    product_specs = str(product.quality_specs).lower() if product.quality_specs else ""
                    combined_text = f"{product_text} {product_specs}"

                    # Count keyword matches
                    matches = sum(1 for keyword in all_keywords if keyword in combined_text)
                    if all_keywords:
                        product_score = min(100, int((matches / len(all_keywords)) * 100))
                    else:
                        product_score = 50  # Default if no keywords

                    # Bonus for keyword_tags match
                    if keyword_tags:
                        tag_matches = sum(1 for tag in keyword_tags if tag.lower() in combined_text)
                        tag_bonus = min(20, int((tag_matches / len(keyword_tags)) * 20))
                        product_score = min(100, product_score + tag_bonus)

                    max_product_score = max(max_product_score, product_score)

                score = max_product_score
            except BusinessProfile.DoesNotExist:
                score = 0

            spec_scores[umkm_id] = score

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

    def _calculate_final_match_score(
        self,
        base_score: int,
        spec_match_score: int,
        capability_score: int
    ) -> int:
        """
        PBI-BE-M6-12: Calculate Final Match Score
        
        Input: base_score, spec_match_score, capability_score
        Formula: final_score = (base_score × 0.4) + (spec_match × 0.3) + (capability × 0.3)
        Round to integer (0-100)
        Threshold: only return UMKM with score >= 70
        Output: final_match_score per UMKM
        """
        final_score = (base_score * 0.4) + (spec_match_score * 0.3) + (capability_score * 0.3)
        return int(round(final_score))

