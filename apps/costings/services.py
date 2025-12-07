"""
AI Services for Module 4: Costing & Pricing Calculations

Services:
- PBI-BE-M4-06: AI Price Calculator - EXW (Ex-Works)
- PBI-BE-M4-07: AI Price Calculator - FOB (Free on Board)
- PBI-BE-M4-08: AI Price Calculator - CIF (Cost Insurance Freight)
- PBI-BE-M4-09: AI Container Optimizer
- PBI-BE-M4-10: Currency Exchange Rate Service
"""

import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from .models import ExchangeRate

# Import KolosalAI for pricing recommendations
try:
    from core.services import KolosalAIService
except ImportError:
    KolosalAIService = None

logger = logging.getLogger(__name__)


class PriceCalculatorService:
    """
    Service untuk menghitung harga ekspor (EXW, FOB, CIF)
    
    PBI-BE-M4-06, PBI-BE-M4-07, PBI-BE-M4-08
    """
    
    # Estimasi biaya tetap
    DOCUMENT_COST_USD = Decimal("50.00")  # Biaya dokumen ekspor (estimasi)
    INSURANCE_RATE = Decimal("0.005")  # 0.5% insurance
    
    # Estimasi trucking berdasarkan jarak ke pelabuhan (dalam km)
    # Format: (min_km, max_km, cost_per_km)
    TRUCKING_RATES = [
        (0, 50, Decimal("0.50")),      # Dekat: IDR 500/km
        (50, 150, Decimal("0.40")),    # Sedang: IDR 400/km
        (150, 300, Decimal("0.30")),   # Jauh: IDR 300/km
        (300, 9999, Decimal("0.25")),  # Sangat jauh: IDR 250/km
    ]
    
    # Estimasi freight berdasarkan negara tujuan (per USD value)
    # Format: (region, freight_percent)
    FREIGHT_RATES = {
        "ASEAN": Decimal("0.08"),        # 8% untuk ASEAN
        "Asia": Decimal("0.12"),         # 12% untuk Asia lainnya
        "Middle_East": Decimal("0.15"),  # 15% untuk Timur Tengah
        "Europe": Decimal("0.18"),       # 18% untuk Eropa
        "Americas": Decimal("0.20"),     # 20% untuk Amerika
        "Africa": Decimal("0.16"),       # 16% untuk Afrika
        "default": Decimal("0.15"),      # Default
    }
    
    @staticmethod
    def get_exchange_rate():
        """
        PBI-BE-M4-10: Get current IDR-USD exchange rate
        
        Priority:
        1. Database (manual/cached)
        2. Auto-fetch from external API if stale (>24h)
        3. Fallback rate
        """
        try:
            rate = ExchangeRate.objects.latest("updated_at")
            
            # Check if rate is stale (older than 24 hours)
            from django.utils import timezone
            from datetime import timedelta
            
            if timezone.now() - rate.updated_at > timedelta(hours=24):
                logger.info("Exchange rate is stale (>24h), attempting auto-fetch...")
                fresh_rate = PriceCalculatorService.fetch_live_exchange_rate()
                if fresh_rate:
                    rate.rate = fresh_rate
                    rate.source = "auto_fetched"
                    rate.save()
                    logger.info(f"Exchange rate updated automatically: {fresh_rate}")
            
            return rate.rate
        except ExchangeRate.DoesNotExist:
            # Try to fetch fresh rate
            logger.warning("No exchange rate found, attempting to fetch from API...")
            fresh_rate = PriceCalculatorService.fetch_live_exchange_rate()
            
            if fresh_rate:
                ExchangeRate.objects.create(rate=fresh_rate, source="auto_fetched")
                return fresh_rate
            
            # Fallback rate
            logger.warning("Failed to fetch exchange rate, using fallback rate 15800")
            return Decimal("15800.00")
    
    @staticmethod
    def fetch_live_exchange_rate():
        """
        Fetch live IDR/USD exchange rate from external API
        
        Uses exchangerate-api.com (free tier: 1500 requests/month)
        Fallback to currencyapi.com if primary fails
        
        Returns:
            Decimal: Current IDR/USD rate, or None if failed
        """
        import requests
        from decimal import Decimal
        
        # Option 1: exchangerate-api.com (no API key needed for basic)
        try:
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                idr_rate = data.get("rates", {}).get("IDR")
                
                if idr_rate:
                    logger.info(f"Fetched live rate from exchangerate-api: {idr_rate}")
                    return Decimal(str(idr_rate))
        except Exception as e:
            logger.warning(f"Failed to fetch from exchangerate-api: {e}")
        
        # Option 2: Fallback to another API (could add more here)
        try:
            # Example: fixer.io, currencyapi.com, etc (requires API key)
            # For now, just log and return None
            logger.warning("All exchange rate APIs failed")
        except Exception as e:
            logger.warning(f"Fallback API failed: {e}")
        
        return None
    
    @staticmethod
    def calculate_exw(cogs_per_unit_idr, packing_cost_idr, target_margin_percent):
        """
        PBI-BE-M4-06: Calculate Ex-Works price (Harga di pabrik)
        
        Formula:
        1. Total cost IDR = COGS + Packing
        2. Apply margin: Total × (1 + margin%)
        3. Convert IDR → USD using current exchange rate
        
        Args:
            cogs_per_unit_idr: Decimal, cost dalam IDR
            packing_cost_idr: Decimal, biaya packing dalam IDR
            target_margin_percent: Decimal, target margin %
        
        Returns:
            Decimal: EXW price in USD
        """
        # Total cost in IDR
        total_cost_idr = cogs_per_unit_idr + packing_cost_idr
        
        # Apply margin
        margin_multiplier = 1 + (target_margin_percent / 100)
        exw_idr = total_cost_idr * margin_multiplier
        
        # Convert to USD
        exchange_rate = PriceCalculatorService.get_exchange_rate()
        exw_usd = Decimal(str(exw_idr)) / exchange_rate
        
        return exw_usd.quantize(Decimal("0.01"))
    
    @staticmethod
    def calculate_fob(exw_usd, business_address_estimate_km=100):
        """
        PBI-BE-M4-07: Calculate FOB price (Free on Board)
        
        FOB = EXW + Trucking (estimasi ke pelabuhan) + Document Cost
        
        Args:
            exw_usd: Decimal, EXW price in USD
            business_address_estimate_km: int, estimated distance to port in km
        
        Returns:
            Decimal: FOB price in USD
        """
        # Estimate trucking cost (convert USD → IDR, calculate, convert back)
        exchange_rate = PriceCalculatorService.get_exchange_rate()
        exw_idr = exw_usd * exchange_rate
        
        # Find applicable trucking rate
        trucking_rate_per_km = Decimal("0.40")  # Default rate
        for min_km, max_km, rate in PriceCalculatorService.TRUCKING_RATES:
            if min_km <= business_address_estimate_km <= max_km:
                trucking_rate_per_km = rate
                break
        
        trucking_cost_idr = Decimal(business_address_estimate_km) * trucking_rate_per_km * 1000  # Convert to IDR
        trucking_cost_usd = trucking_cost_idr / exchange_rate
        
        # Total FOB
        fob_usd = exw_usd + trucking_cost_usd + PriceCalculatorService.DOCUMENT_COST_USD
        
        return fob_usd.quantize(Decimal("0.01"))
    
    @staticmethod
    def get_ai_pricing_recommendation(product_name, exw_usd, target_country_code=None, product_category=None, material=None):
        """
        PBI-BE-M4-03-AI: Get AI-powered pricing recommendations
        
        Uses KolosalAI to analyze market conditions and suggest:
        - Competitive pricing adjustments
        - Market positioning strategy
        - Risk/opportunity assessment
        
        Args:
            product_name: str, product name for market context
            exw_usd: Decimal, calculated EXW price
            target_country_code: str, target market country code
            product_category: str, product category for industry context
            material: str, material composition for value assessment
        
        Returns:
            dict: {"recommendation": str, "risk_level": str, "market_position": str, 
                   "price_adjustment_suggestion": str, "competitive_insights": str}
                  or fallback if AI unavailable
        """
        if KolosalAIService is None:
            logger.warning("KolosalAI not available, skipping AI pricing recommendation")
            return {
                "recommendation": f"Calculated EXW price: ${exw_usd}. Consider market research for pricing validation.",
                "risk_level": "medium",
                "market_position": "competitive",
                "price_adjustment_suggestion": "No adjustment needed",
                "competitive_insights": "Manual market analysis recommended"
            }
        
        try:
            ai_service = KolosalAIService()
            
            # Enhanced context for better AI analysis
            product_context = f"{product_name}"
            if material:
                product_context += f" (Material: {material})"
            if product_category:
                product_context += f" - Category: {product_category}"
            
            target_market = target_country_code if target_country_code else "International/General Export Market"
            
            prompt = f"""Sebagai expert pricing strategist untuk ekspor UMKM Indonesia, analisis harga berikut:

PRODUK: {product_context}
HARGA KALKULASI: EXW ${exw_usd} USD
PASAR TARGET: {target_market}

Berikan analisis terstruktur:

1. COMPETITIVE ANALYSIS (2-3 kalimat):
   - Apakah harga ini kompetitif dibanding produk sejenis dari Indonesia/Asia?
   - Faktor apa yang mempengaruhi daya saing di pasar target?

2. POSITIONING STRATEGY (1 kalimat):
   - Rekomendasi positioning: Premium / Mid-Range / Value / Budget-Friendly?

3. PRICE ADJUSTMENT (1-2 kalimat):
   - Perlu adjustment? Jika ya, berapa persen dan alasannya?
   - Range harga optimal untuk pasar target?

4. RISK ASSESSMENT (1 kalimat):
   - Risk level: LOW/MEDIUM/HIGH dan faktor risiko utama?

Format response: Jelas, actionable, maksimal 150 kata total."""
            
            system_prompt = """Kamu adalah senior pricing consultant yang fokus pada ekspor UMKM Indonesia. 
Expertise: competitive pricing analysis, international market positioning, export cost optimization.
Berikan insight praktis, data-driven, dan actionable recommendations dengan bahasa profesional namun mudah dipahami UMKM."""
            
            recommendation = ai_service._call_ai(prompt, system_prompt)
            
            # Enhanced parsing with more intelligent extraction
            risk_level = "medium"
            if any(keyword in recommendation.lower() for keyword in ["high risk", "risiko tinggi", "berisiko tinggi"]):
                risk_level = "high"
            elif any(keyword in recommendation.lower() for keyword in ["low risk", "risiko rendah", "aman"]):
                risk_level = "low"
            
            market_position = "competitive"
            if any(keyword in recommendation.lower() for keyword in ["premium", "high-end", "kelas atas"]):
                market_position = "premium"
            elif any(keyword in recommendation.lower() for keyword in ["mid-range", "menengah"]):
                market_position = "mid-range"
            elif any(keyword in recommendation.lower() for keyword in ["value", "economy", "budget", "ekonomis"]):
                market_position = "value"
            
            # Extract price adjustment suggestions
            price_adjustment = "Maintain current price"
            if any(keyword in recommendation.lower() for keyword in ["naik", "increase", "tingkatkan", "tambah"]):
                price_adjustment = "Consider price increase (review market tolerance)"
            elif any(keyword in recommendation.lower() for keyword in ["turun", "decrease", "kurangi", "lower"]):
                price_adjustment = "Consider price reduction (market entry strategy)"
            
            # Extract competitive insights
            competitive_insights = "Market analysis indicates standard competitive positioning"
            if "kompetitif" in recommendation.lower() or "competitive" in recommendation.lower():
                competitive_insights = "Pricing is competitive within target market range"
            if "premium" in recommendation.lower():
                competitive_insights = "Product positioned for premium market segment"
            
            return {
                "recommendation": recommendation,
                "risk_level": risk_level,
                "market_position": market_position,
                "price_adjustment_suggestion": price_adjustment,
                "competitive_insights": competitive_insights
            }
        except Exception as e:
            logger.error(f"Error getting AI pricing recommendation: {e}")
            logger.exception("Full traceback:")
            return {
                "recommendation": f"Calculated EXW: ${exw_usd}. AI analysis temporarily unavailable - manual review recommended.",
                "risk_level": "medium",
                "market_position": "competitive",
                "price_adjustment_suggestion": "No adjustment (pending analysis)",
                "competitive_insights": "AI service error - please retry or consult market data"
            }
    
    @staticmethod
    def calculate_cif(fob_usd, target_country_code=None):
        """
        PBI-BE-M4-08: Calculate CIF price (Cost, Insurance, Freight)
        
        CIF = FOB + Freight (estimasi berdasarkan negara) + Insurance (0.5%)
        
        Args:
            fob_usd: Decimal, FOB price in USD
            target_country_code: str, target country code (e.g., "US", "JP")
        
        Returns:
            Decimal: CIF price in USD, or None if no country specified
        """
        if not target_country_code:
            logger.info("No target country specified, CIF cannot be calculated")
            return None
        
        # Estimate freight based on country region
        # Simple mapping (could be enhanced with master data table)
        region_map = {
            "ID": "ASEAN", "MY": "ASEAN", "SG": "ASEAN", "TH": "ASEAN", "PH": "ASEAN",
            "JP": "Asia", "KR": "Asia", "CN": "Asia", "IN": "Asia",
            "AE": "Middle_East", "SA": "Middle_East",
            "GB": "Europe", "DE": "Europe", "FR": "Europe",
            "US": "Americas", "CA": "Americas",
            "ZA": "Africa", "EG": "Africa",
        }
        
        region = region_map.get(target_country_code, "default")
        freight_rate = PriceCalculatorService.FREIGHT_RATES.get(region, PriceCalculatorService.FREIGHT_RATES["default"])
        
        # Calculate freight as percentage of FOB
        freight_cost_usd = fob_usd * freight_rate
        
        # Calculate insurance (0.5% of FOB value)
        insurance_usd = fob_usd * PriceCalculatorService.INSURANCE_RATE
        
        # Total CIF
        cif_usd = fob_usd + freight_cost_usd + insurance_usd
        
        return cif_usd.quantize(Decimal("0.01"))


class ContainerOptimizerService:
    """
    Service untuk optimasi container 20ft
    
    PBI-BE-M4-09
    """
    
    # 20ft Container internal dimensions (in meters)
    CONTAINER_20FT_LENGTH = 5.9
    CONTAINER_20FT_WIDTH = 2.35
    CONTAINER_20FT_HEIGHT = 2.39
    
    # Convert to cm for easier calculation
    CONTAINER_VOLUME_CM3 = (CONTAINER_20FT_LENGTH * 100) * (CONTAINER_20FT_WIDTH * 100) * (CONTAINER_20FT_HEIGHT * 100)
    
    @staticmethod
    def calculate_container_capacity(product_length_cm, product_width_cm, product_height_cm, weight_per_unit_kg=None):
        """
        PBI-BE-M4-09: Calculate 20ft container capacity using 3D bin packing
        
        Simplified calculation: assume efficient stacking with 85% space utilization
        (Real 3D bin packing is complex; this is practical estimate)
        
        Args:
            product_length_cm: Decimal/int, product length in cm
            product_width_cm: Decimal/int, product width in cm
            product_height_cm: Decimal/int, product height in cm
            weight_per_unit_kg: float, weight per unit (optional, for weight limit check)
        
        Returns:
            dict: {capacity: int, notes: str}
        """
        # Product volume in cm³
        product_volume = float(product_length_cm) * float(product_width_cm) * float(product_height_cm)
        
        if product_volume == 0:
            return {"capacity": 0, "notes": "Invalid product dimensions"}
        
        # Calculate capacity (assuming 85% space utilization efficiency)
        theoretical_capacity = ContainerOptimizerService.CONTAINER_VOLUME_CM3 * 0.85 / product_volume
        capacity = int(theoretical_capacity)
        
        # Check weight limit (20ft container max payload ~17,500 kg)
        max_payload_kg = 17500
        notes = ""
        
        if weight_per_unit_kg:
            weight_based_capacity = int(max_payload_kg / float(weight_per_unit_kg))
            if weight_based_capacity < capacity:
                capacity = weight_based_capacity
                notes = f"Weight-limited: max {capacity} units ({float(weight_per_unit_kg)} kg each)"
        
        # Generate optimization suggestions
        if capacity < 500:
            notes += " | Tip: Reduce product height by 1-2cm untuk +50-100 units" if not notes else " | Tip: Reduce height for more capacity"
        elif capacity < 1000:
            notes += " | Tip: Optimize stacking pattern untuk maksimal utilization"
        
        return {
            "capacity": capacity,
            "notes": notes if notes else "Good packing efficiency achieved"
        }
    
    @staticmethod
    def get_ai_container_optimization(product_name, dimensions_lwh, capacity, weight_per_unit=None):
        """
        Get AI-powered suggestions for container optimization
        
        Args:
            product_name: str, product name
            dimensions_lwh: dict, {l, w, h} in cm
            capacity: int, calculated capacity
            weight_per_unit: float, weight in kg
        
        Returns:
            str: AI suggestions for optimization or empty if unavailable
        """
        if KolosalAIService is None:
            return ""
        
        try:
            ai_service = KolosalAIService()
            
            l, w, h = dimensions_lwh.get("l", 0), dimensions_lwh.get("w", 0), dimensions_lwh.get("h", 0)
            weight_info = f", berat {weight_per_unit} kg/unit" if weight_per_unit else ""
            
            prompt = f"""Sebagai expert packaging & logistics untuk ekspor, berikan saran optimasi container 20ft:

PRODUK: {product_name}
DIMENSI: {l}cm × {w}cm × {h}cm{weight_info}
KAPASITAS KALKULASI: {capacity} units per 20ft container

Berikan 2-3 saran PRAKTIS untuk:
1. Optimasi packaging (cara lipat/susun yang lebih efisien)
2. Peningkatan kapasitas (perubahan dimensi atau material)
3. Cost saving opportunities (misalnya: bulk packaging, pallet configuration)

Format: Bullet points, max 80 kata total, fokus actionable."""
            
            system_prompt = """Kamu adalah logistics & packaging consultant untuk ekspor UMKM.
Expertise: container optimization, packaging efficiency, freight cost reduction.
Berikan saran yang realistis dan mudah diimplementasikan UMKM."""
            
            suggestions = ai_service._call_ai(prompt, system_prompt)
            # Return clean AI text without prefix
            return suggestions
            
        except Exception as e:
            logger.warning(f"AI container optimization unavailable: {e}")
            return None


class CostingService:
    """
    Orchestrator service untuk menghitung semua costs sekaligus
    Menggunakan PriceCalculator dan ContainerOptimizer
    """
    
    @staticmethod
    def calculate_full_costing(product, cogs_per_unit_idr, packing_cost_idr, target_margin_percent, target_country_code=None):
        """
        Calculate complete costing with all prices and container optimization
        
        PBI-BE-M4-03-AI: Includes AI pricing recommendations
        
        Args:
            product: Product instance
            cogs_per_unit_idr: Decimal
            packing_cost_idr: Decimal
            target_margin_percent: Decimal
            target_country_code: str (optional, for CIF calculation)
        
        Returns:
            dict: Full costing result with AI recommendations
        """
        try:
            # Calculate prices
            exw_usd = PriceCalculatorService.calculate_exw(
                cogs_per_unit_idr, packing_cost_idr, target_margin_percent
            )
            
            fob_usd = PriceCalculatorService.calculate_fob(exw_usd, business_address_estimate_km=100)
            
            cif_usd = None
            if target_country_code:
                cif_usd = PriceCalculatorService.calculate_cif(fob_usd, target_country_code)
            
            # Calculate container capacity
            dimensions = product.dimensions_l_w_h  # {l, w, h} in cm
            weight = float(product.weight_net) if product.weight_net else None
            
            container_result = ContainerOptimizerService.calculate_container_capacity(
                dimensions.get("l", 10),
                dimensions.get("w", 10),
                dimensions.get("h", 10),
                weight
            )
            
            # Get enhanced AI pricing recommendations with product context
            ai_recommendation = PriceCalculatorService.get_ai_pricing_recommendation(
                product_name=product.name_local,
                exw_usd=exw_usd,
                target_country_code=target_country_code,
                product_category=str(product.category_id) if hasattr(product, 'category_id') else None,
                material=product.material_composition if hasattr(product, 'material_composition') else None
            )
            
            # Get AI container optimization suggestions
            ai_container_suggestions = ContainerOptimizerService.get_ai_container_optimization(
                product_name=product.name_local,
                dimensions_lwh=dimensions,
                capacity=container_result["capacity"],
                weight_per_unit=weight
            )
            
            # Keep optimization notes clean (without AI text)
            optimization_notes = container_result["notes"]
            
            return {
                "recommended_exw_price": exw_usd,
                "recommended_fob_price": fob_usd,
                "recommended_cif_price": cif_usd,
                "container_20ft_capacity": container_result["capacity"],
                "optimization_notes": optimization_notes,
                "ai_container_optimization": ai_container_suggestions,  # Separate field for FE
                "ai_pricing_recommendation": ai_recommendation,  # Enhanced with more fields
            }
        except Exception as e:
            logger.error(f"Error calculating costing: {e}")
            logger.exception("Full traceback:")
            raise
