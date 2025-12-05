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
from .models import ExchangeRate

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
        """
        try:
            rate = ExchangeRate.objects.latest("updated_at")
            return rate.rate
        except ExchangeRate.DoesNotExist:
            # Fallback rate
            logger.warning("No exchange rate found, using fallback rate 15800")
            return Decimal("15800.00")
    
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
        exw_usd = exw_idr / exchange_rate
        
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


class CostingService:
    """
    Orchestrator service untuk menghitung semua costs sekaligus
    Menggunakan PriceCalculator dan ContainerOptimizer
    """
    
    @staticmethod
    def calculate_full_costing(product, cogs_per_unit_idr, packing_cost_idr, target_margin_percent, target_country_code=None):
        """
        Calculate complete costing with all prices and container optimization
        
        Args:
            product: Product instance
            cogs_per_unit_idr: Decimal
            packing_cost_idr: Decimal
            target_margin_percent: Decimal
            target_country_code: str (optional, for CIF calculation)
        
        Returns:
            dict: Full costing result
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
            
            return {
                "recommended_exw_price": exw_usd,
                "recommended_fob_price": fob_usd,
                "recommended_cif_price": cif_usd,
                "container_20ft_capacity": container_result["capacity"],
                "optimization_notes": container_result["notes"],
            }
        except Exception as e:
            logger.error(f"Error calculating costing: {e}")
            raise
