"""
AI Services for Product Catalog Module

Implements:
1. AI International Product Description Generator
   - Export Buyer Description (English B2B)
   - Technical Specification Sheet
   - Material/Food Safety Sheet

2. AI Market Intelligence
   - Recommends target countries based on product characteristics
   - Provides market insights and trends

3. Catalog Pricing (reuses costing module)
   - EXW/FOB/CIF pricing for catalog
"""

import json
import logging
import re
from decimal import Decimal
from typing import Dict, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class CatalogAIService:
    """
    AI Service for Catalog features using Kolosal AI.
    """

    # Mapping dari nama model ke ID model Kolosal
    MODEL_MAPPING = {
        "Claude Sonnet 4.5": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "Llama 4 Maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "MiniMax M2": "minimax/minimax-m2",
        "Kimi K2": "moonshotai/kimi-k2-0905",
        "Qwen 3 30BA3B": "qwen/qwen3-vl-30b-a3b-instruct",
        "GLM 4.6": "z-ai/glm-4.6",
    }

    def __init__(self):
        api_key = settings.KOLOSAL_API_KEY
        if not api_key or api_key.strip() == "":
            logger.error("KOLOSAL_API_KEY is not set!")
            raise ValueError("KOLOSAL_API_KEY is required")

        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url=settings.KOLOSAL_BASE_URL,
        )
        # Convert model name to ID if needed
        model_name = settings.KOLOSAL_MODEL
        self.model = self.MODEL_MAPPING.get(model_name, model_name)
        logger.info(f"CatalogAIService initialized - Model: {self.model}")

    def _call_ai(self, prompt: str, system_prompt: str = None, temperature: float = 0.3) -> str:
        """Make a call to Kolosal AI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Kolosal AI API error: {e}", exc_info=True)
            raise

    def generate_international_description(
        self,
        product_name: str,
        description_local: str,
        material_composition: str,
        dimensions: dict = None,
        weight_net: float = None,
        weight_gross: float = None,
        category: str = "",
        is_food_product: bool = False,
    ) -> Dict:
        """
        AI 1: Generate International Product Description

        Creates 3 versions:
        - export_buyer_description: English B2B description
        - technical_spec_sheet: Technical specifications
        - safety_sheet: Material/Food Safety information

        Returns:
            Dict with all three description versions
        """
        system_prompt = """Kamu adalah ahli ekspor dan marketing B2B internasional.
Tugasmu adalah membuat deskripsi produk standar ekspor dalam 3 versi berbeda.

ATURAN:
- Gunakan bahasa Inggris profesional untuk semua output
- Fokus pada value proposition untuk buyer internasional
- Sertakan informasi yang relevan untuk import/export
- Gunakan format yang mudah dibaca dan profesional"""

        dimensions_str = ""
        if dimensions:
            l = dimensions.get("l", dimensions.get("length", "N/A"))
            w = dimensions.get("w", dimensions.get("width", "N/A"))
            h = dimensions.get("h", dimensions.get("height", "N/A"))
            dimensions_str = f"{l} × {w} × {h} cm"

        prompt = f"""Buat 3 versi deskripsi produk untuk ekspor:

INFORMASI PRODUK:
- Nama: {product_name}
- Deskripsi Lokal: {description_local}
- Material: {material_composition}
- Kategori: {category}
- Dimensi: {dimensions_str if dimensions_str else 'N/A'}
- Berat Bersih: {weight_net if weight_net else 'N/A'} kg
- Berat Kotor: {weight_gross if weight_gross else 'N/A'} kg
- Jenis Produk: {'Food/Beverage Product' if is_food_product else 'Non-Food Product'}

OUTPUT FORMAT (dalam JSON):
{{
    "export_buyer_description": "Deskripsi marketing 2-3 paragraf untuk buyer B2B internasional. Fokus pada quality, craftsmanship, dan value proposition.",

    "technical_spec_sheet": {{
        "product_name": "English product name",
        "material": "Material specification",
        "dimensions": "L × W × H cm",
        "weight_net": "X kg",
        "weight_gross": "X kg",
        "finishing": "Finishing details",
        "packaging": "Packaging specification",
        "country_of_origin": "Indonesia",
        "certifications": ["list of applicable certifications"],
        "usage": "Intended use/application",
        "care_instructions": "Care/maintenance instructions"
    }},

    "safety_sheet": {{
        "material_safety": "Material safety information",
        "warnings": ["Any warnings or precautions"],
        "storage": "Storage requirements",
        {"food_safety" if is_food_product else "handling"}: "{'Food safety info' if is_food_product else 'Handling instructions'}"
    }}
}}

Berikan output dalam format JSON yang valid."""

        try:
            response = self._call_ai(prompt, system_prompt)

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "data": result
                }

            # If no valid JSON, return structured response
            return {
                "success": True,
                "data": {
                    "export_buyer_description": response,
                    "technical_spec_sheet": {},
                    "safety_sheet": {}
                }
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "raw_response": response if 'response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Error generating international description: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_market_intelligence(
        self,
        product_name: str,
        description: str,
        material_composition: str,
        category: str = "",
        current_price_usd: float = None,
        production_capacity: int = None,
    ) -> Dict:
        """
        AI 2: Market Intelligence

        Provides:
        - Recommended target countries
        - Countries to avoid
        - Market trends and insights
        - Competitor analysis
        - Pricing recommendations per market

        Returns:
            Dict with market intelligence data
        """
        system_prompt = """Kamu adalah ahli market intelligence dan perdagangan internasional.
Tugasmu adalah menganalisis produk dan memberikan rekomendasi pasar ekspor yang tepat.

ATURAN:
- Berikan rekomendasi berdasarkan data tren pasar terkini
- Pertimbangkan cultural preferences, regulasi, dan demand
- Sertakan alasan konkret untuk setiap rekomendasi
- Fokus pada pasar yang realistis untuk UMKM Indonesia"""

        prompt = f"""Analisis produk berikut dan berikan market intelligence:

INFORMASI PRODUK:
- Nama Produk: {product_name}
- Deskripsi: {description}
- Material: {material_composition}
- Kategori: {category}
- Harga Saat Ini (USD): ${current_price_usd if current_price_usd else 'Belum ditentukan'}
- Kapasitas Produksi: {production_capacity if production_capacity else 'N/A'} unit/bulan

OUTPUT FORMAT (dalam JSON):
{{
    "recommended_countries": [
        {{
            "country": "Country Name",
            "country_code": "XX",
            "score": 85,
            "reason": "Alasan kenapa negara ini cocok",
            "market_size": "Large/Medium/Small",
            "competition_level": "High/Medium/Low",
            "suggested_price_range": "$XX - $XX",
            "entry_strategy": "Strategi masuk pasar"
        }}
    ],
    "countries_to_avoid": [
        {{
            "country": "Country Name",
            "country_code": "XX",
            "reason": "Alasan kenapa sebaiknya dihindari"
        }}
    ],
    "market_trends": [
        "Trend 1 yang relevan",
        "Trend 2 yang relevan"
    ],
    "competitive_landscape": "Analisis kompetitor dan positioning",
    "growth_opportunities": ["Opportunity 1", "Opportunity 2"],
    "risks_and_challenges": ["Risk 1", "Risk 2"],
    "overall_recommendation": "Rekomendasi umum untuk strategi ekspor"
}}

Berikan minimal 3 negara rekomendasi dan 2 negara yang sebaiknya dihindari.
Output dalam format JSON yang valid."""

        try:
            response = self._call_ai(prompt, system_prompt, temperature=0.4)

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "success": True,
                    "data": result
                }

            return {
                "success": False,
                "error": "Failed to parse market intelligence response",
                "raw_response": response
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse market intelligence JSON: {e}")
            return {
                "success": False,
                "error": "Failed to parse AI response"
            }
        except Exception as e:
            logger.error(f"Error getting market intelligence: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_catalog_pricing(
        self,
        product_name: str,
        cogs_per_unit: Decimal,
        target_margin_percent: Decimal,
        material_composition: str = "",
        target_country_code: str = None,
        dimensions: dict = None,
        weight_gross: float = None,
    ) -> Dict:
        """
        AI 3: Catalog Pricing

        Generates pricing recommendations for catalog:
        - EXW price calculation
        - FOB price estimation
        - CIF price estimation (if target country provided)
        - AI pricing insights

        Returns:
            Dict with pricing data
        """
        # Import costing service for reuse
        try:
            from apps.costings.services import PriceCalculatorService
            price_service = PriceCalculatorService()
        except ImportError:
            logger.error("Could not import PriceCalculatorService")
            price_service = None

        # Calculate base prices
        cogs = float(cogs_per_unit)
        margin = float(target_margin_percent) / 100

        # Get exchange rate
        exchange_rate = 16000.0  # Default fallback
        if price_service:
            try:
                rate = price_service.get_exchange_rate()
                exchange_rate = float(rate) if rate else 16000.0
            except:
                pass

        # Calculate EXW (in USD)
        base_price_idr = cogs * (1 + margin)
        exw_price_usd = base_price_idr / exchange_rate

        # Estimate FOB (EXW + ~5-10% for local handling)
        fob_multiplier = 1.08
        fob_price_usd = exw_price_usd * fob_multiplier

        # Estimate CIF (FOB + shipping + insurance, varies by destination)
        cif_price_usd = None
        if target_country_code:
            # Rough estimation based on region
            shipping_multiplier = self._get_shipping_multiplier(target_country_code)
            cif_price_usd = fob_price_usd * shipping_multiplier

        # Get AI pricing insights
        system_prompt = """Kamu adalah ahli pricing dan ekspor. Berikan insight singkat tentang pricing produk untuk katalog ekspor."""

        prompt = f"""Berikan insight pricing untuk produk katalog:

Produk: {product_name}
Material: {material_composition}
COGS: Rp {cogs:,.0f}
Target Margin: {target_margin_percent}%
EXW Price: ${exw_price_usd:.2f}
FOB Price: ${fob_price_usd:.2f}
Target Country: {target_country_code or 'General'}

Berikan:
1. Apakah harga kompetitif untuk pasar internasional?
2. Saran penyesuaian harga jika ada
3. Tips untuk meningkatkan margin

Format: paragraf singkat 3-4 kalimat."""

        pricing_insight = ""
        try:
            pricing_insight = self._call_ai(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Could not get pricing insight: {e}")
            pricing_insight = "Unable to generate pricing insight at this time."

        return {
            "success": True,
            "data": {
                "exchange_rate_used": exchange_rate,
                "cogs_per_unit_idr": cogs,
                "target_margin_percent": float(target_margin_percent),
                "exw_price_usd": round(exw_price_usd, 2),
                "fob_price_usd": round(fob_price_usd, 2),
                "cif_price_usd": round(cif_price_usd, 2) if cif_price_usd else None,
                "target_country": target_country_code,
                "pricing_insight": pricing_insight,
                "pricing_breakdown": {
                    "base_cost_idr": cogs,
                    "margin_amount_idr": cogs * margin,
                    "total_idr": base_price_idr,
                    "local_handling_estimate_usd": round((fob_price_usd - exw_price_usd), 2),
                    "shipping_estimate_usd": round((cif_price_usd - fob_price_usd), 2) if cif_price_usd else None,
                }
            }
        }

    def _get_shipping_multiplier(self, country_code: str) -> float:
        """Get estimated shipping multiplier based on destination region."""
        # Southeast Asia
        if country_code in ["SG", "MY", "TH", "VN", "PH", "BN", "MM", "LA", "KH"]:
            return 1.12
        # East Asia
        elif country_code in ["JP", "KR", "CN", "TW", "HK"]:
            return 1.18
        # South Asia
        elif country_code in ["IN", "BD", "PK", "LK", "NP"]:
            return 1.15
        # Middle East
        elif country_code in ["AE", "SA", "QA", "KW", "BH", "OM", "EG", "TR"]:
            return 1.22
        # Europe
        elif country_code in ["DE", "NL", "FR", "GB", "IT", "ES", "BE", "PL", "AT", "SE"]:
            return 1.28
        # North America
        elif country_code in ["US", "CA", "MX"]:
            return 1.30
        # Australia/Oceania
        elif country_code in ["AU", "NZ"]:
            return 1.20
        # Africa
        elif country_code in ["ZA", "NG", "KE", "GH", "TZ"]:
            return 1.35
        # South America
        elif country_code in ["BR", "AR", "CL", "CO", "PE"]:
            return 1.38
        # Default
        else:
            return 1.25


# Singleton instance
_catalog_ai_service = None

def get_catalog_ai_service() -> CatalogAIService:
    """Get or create CatalogAIService singleton."""
    global _catalog_ai_service
    if _catalog_ai_service is None:
        _catalog_ai_service = CatalogAIService()
    return _catalog_ai_service
