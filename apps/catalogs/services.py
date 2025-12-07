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

4. Catalog Storage Service
   - Upload images to Supabase Storage
"""

import json
import logging
import re
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Dict, Optional

from django.conf import settings
from django.core.files.storage import default_storage
from openai import OpenAI

logger = logging.getLogger(__name__)


class CatalogAIService:
    """
    AI Service for Catalog features using Kolosal AI.
    """

    def __init__(self):
        api_key = settings.KOLOSAL_API_KEY
        if not api_key or api_key.strip() == "":
            logger.error("KOLOSAL_API_KEY is not set!")
            raise ValueError("KOLOSAL_API_KEY is required")

        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url=settings.KOLOSAL_BASE_URL,
        )
        # Use model name directly from settings (same as other services)
        # Don't use model mapping - use the name as-is from settings
        self.model = settings.KOLOSAL_MODEL
        logger.info(f"CatalogAIService initialized - Model: {self.model}")

    def _call_ai(self, prompt: str, system_prompt: str = None, temperature: float = 0.1) -> str:
        """
        Make a call to Kolosal AI API.
        
        Matches the pattern used in core/services/ai_service.py (KolosalAIService)
        which is successfully working for product enrichment.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            temperature: Temperature for AI response (default 0.1 for consistency)
            
        Returns:
            The AI response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            logger.debug(f"Calling Kolosal AI API with model: {self.model}")
            logger.debug(f"Messages count: {len(messages)}")
            # Log message lengths for debugging
            for i, msg in enumerate(messages):
                content_len = len(msg.get("content", ""))
                logger.debug(f"Message {i} ({msg.get('role')}): {content_len} chars")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,  # Low temperature for consistent results (same as KolosalAIService)
            )
            result = response.choices[0].message.content.strip()
            logger.debug(f"AI API response received: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Kolosal AI API error: {e}")
            logger.error(f"Model: {self.model}")
            logger.error(f"Base URL: {self.client.base_url}")
            # Log the actual messages being sent (truncated for safety)
            for i, msg in enumerate(messages):
                content = msg.get("content", "")
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.error(f"Message {i} ({msg.get('role')}): {len(content)} chars - {content_preview}")
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
            logger.info(f"Calling AI for product: {product_name}")
            response = self._call_ai(prompt, system_prompt)
            logger.info(f"AI response received, length: {len(response) if response else 0}")
            logger.debug(f"AI raw response: {response[:500] if response else 'None'}...")

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                logger.debug(f"JSON extracted, length: {len(json_str)}")
                result = json.loads(json_str)
                logger.info(f"JSON parsed successfully, keys: {list(result.keys())}")
                return {
                    "success": True,
                    "data": result
                }

            # If no valid JSON, return structured response
            logger.warning(f"No JSON found in AI response, using raw text")
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
            logger.error(f"Raw response that failed: {response[:500] if response else 'None'}...")
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "raw_response": response if 'response' in locals() else None
            }
        except Exception as e:
            logger.error(f"Error generating international description: {e}", exc_info=True)
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
        # Validate and sanitize inputs
        product_name = str(product_name or "").strip()[:200]
        description = str(description or "").strip()[:500]  # Limit length
        material_composition = str(material_composition or "").strip()[:200]
        category = str(category or "").strip()[:100]
        
        # Build prompt parts to avoid issues with f-string formatting
        system_prompt = """Kamu adalah ahli market intelligence dan perdagangan internasional.
Tugasmu adalah menganalisis produk dan memberikan rekomendasi pasar ekspor yang tepat.

ATURAN:
- Berikan rekomendasi berdasarkan data tren pasar terkini
- Pertimbangkan cultural preferences, regulasi, dan demand
- Sertakan alasan konkret untuk setiap rekomendasi
- Fokus pada pasar yang realistis untuk UMKM Indonesia
- Output HARUS dalam format JSON yang valid"""

        # Build prompt with proper escaping and length limits
        price_str = f"${current_price_usd:.2f}" if current_price_usd else "Belum ditentukan"
        capacity_str = f"{production_capacity} unit/bulan" if production_capacity else "N/A"
        
        prompt_parts = [
            "Analisis produk berikut dan berikan market intelligence:",
            "",
            "INFORMASI PRODUK:",
            f"- Nama Produk: {product_name}",
            f"- Deskripsi: {description}",
            f"- Material: {material_composition}",
            f"- Kategori: {category}",
            f"- Harga Saat Ini (USD): {price_str}",
            f"- Kapasitas Produksi: {capacity_str}",
            "",
            "OUTPUT FORMAT (dalam JSON):",
            '{"recommended_countries": [{"country": "Country Name", "country_code": "XX", "score": 85, "reason": "Alasan", "market_size": "Large/Medium/Small", "competition_level": "High/Medium/Low", "suggested_price_range": "$XX - $XX", "entry_strategy": "Strategi"}], "countries_to_avoid": [{"country": "Country Name", "country_code": "XX", "reason": "Alasan"}], "market_trends": ["Trend 1", "Trend 2"], "competitive_landscape": "Analisis", "growth_opportunities": ["Opportunity 1"], "risks_and_challenges": ["Risk 1"], "overall_recommendation": "Rekomendasi"}',
            "",
            "Berikan minimal 3 negara rekomendasi dan 2 negara yang sebaiknya dihindari.",
            "Output dalam format JSON yang valid."
        ]
        
        prompt = "\n".join(prompt_parts)

        try:
            # Use same temperature as successful KolosalAIService (0.1)
            response = self._call_ai(prompt, system_prompt, temperature=0.1)

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


# ============================================================================
# Catalog Storage Service (Supabase)
# ============================================================================

class CatalogStorageService:
    """
    Service for handling catalog image uploads to Supabase Storage.

    Falls back to Django's default storage if Supabase is not configured.
    """

    def __init__(self):
        self.supabase_url = getattr(settings, "SUPABASE_URL", "")
        self.supabase_key = getattr(settings, "SUPABASE_ANON_KEY", "")
        # Use dedicated bucket for catalog images
        self.bucket_name = getattr(settings, "SUPABASE_CATALOG_BUCKET", "catalogs")

        self.client = None
        try:
            from supabase import create_client, Client
            if self.supabase_url and self.supabase_key:
                self.client: Optional[Client] = create_client(self.supabase_url, self.supabase_key)
                logger.info(f"✅ Catalog Storage (Supabase) initialized - Bucket: {self.bucket_name}")
            else:
                logger.warning("⚠️ Supabase credentials not configured. Catalog images will use local storage.")
        except ImportError:
            logger.warning("⚠️ supabase-py not installed. Catalog images will use local storage.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")

    def upload_image(self, file, catalog_id: int) -> str:
        """
        Upload catalog image to Supabase Storage.

        Args:
            file: Django UploadedFile object
            catalog_id: ID of the catalog

        Returns:
            Public URL of the uploaded image, or None if upload failed
        """
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise ValueError(f"File size ({file.size} bytes) exceeds maximum allowed size (10MB)")
        
        # Generate unique filename
        file_ext = Path(file.name).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = f"catalogs/{catalog_id}/{unique_filename}"

        if self.client:
            try:
                file.seek(0)
                file_content = file.read()

                # Determine content type
                content_type = getattr(file, 'content_type', None)
                if not content_type:
                    content_type = self._get_content_type(file_ext)

                file_options = {
                    "content-type": content_type,
                    "upsert": "true"
                }

                logger.info(f"Uploading catalog image to Supabase: {storage_path} ({len(file_content)} bytes)")

                # Upload to Supabase
                response = self.client.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file_content,
                    file_options=file_options
                )

                # Check for errors in response
                if isinstance(response, dict) and "error" in response:
                    error_msg = response.get("error", "Unknown error")
                    raise Exception(f"Supabase upload error: {error_msg}")

                # Get public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
                logger.info(f"✅ Catalog image uploaded: {public_url}")
                return public_url

            except Exception as e:
                logger.error(f"❌ Supabase upload failed: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise  # Re-raise to let caller handle it
        else:
            # No Supabase client, return None to use local storage
            logger.warning("Supabase not available. Image should be stored locally via ImageField.")
            return None

    def _upload_local(self, file, storage_path: str) -> str:
        """
        Fallback to local filesystem storage.
        Returns None to indicate file should be saved via Django's ImageField instead.
        """
        # Return None to signal that we should use Django's ImageField
        # instead of storing URL in image_url
        logger.warning("Supabase not available. Image will be stored locally via ImageField.")
        return None

    def _get_content_type(self, file_ext: str) -> str:
        """Get MIME type from file extension. Supports all common image formats."""
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".ico": "image/x-icon",
            ".heic": "image/heic",
            ".heif": "image/heif",
        }
        return content_types.get(file_ext.lower(), "image/jpeg")  # Default to jpeg for unknown extensions

    def delete_image(self, file_url: str) -> bool:
        """
        Delete image from Supabase Storage.

        Args:
            file_url: Public URL of the image to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.client:
            return True

        try:
            if "supabase.co/storage" in file_url and f"/{self.bucket_name}/" in file_url:
                path = file_url.split(f"/{self.bucket_name}/")[-1].split("?")[0]
                self.client.storage.from_(self.bucket_name).remove([path])
                logger.info(f"Catalog image deleted from Supabase: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Supabase image deletion failed: {e}")
            return False


# Singleton instance for storage
_catalog_storage_service = None

def get_catalog_storage_service() -> CatalogStorageService:
    """Get or create CatalogStorageService singleton."""
    global _catalog_storage_service
    if _catalog_storage_service is None:
        _catalog_storage_service = CatalogStorageService()
    return _catalog_storage_service
