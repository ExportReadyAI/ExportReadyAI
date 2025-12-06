"""
Services for ExportReady.AI Module 4 - Costing & Financial Calculator

Implements AI Services for Costing:
# PBI-BE-M4-06: AI Price Calculator - EXW
# PBI-BE-M4-07: AI Price Calculator - FOB
# PBI-BE-M4-08: AI Price Calculator - CIF
# PBI-BE-M4-09: AI Container Optimizer
"""

import logging
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.conf import settings

from .models import ExchangeRate

logger = logging.getLogger(__name__)


# Container dimensions in meters (internal dimensions)
CONTAINER_20FT = {
    "length": Decimal("5.9"),
    "width": Decimal("2.35"),
    "height": Decimal("2.39"),
    "max_weight_kg": 28000,
}

CONTAINER_40FT = {
    "length": Decimal("12.0"),
    "width": Decimal("2.35"),
    "height": Decimal("2.39"),
    "max_weight_kg": 28000,
}

# Estimated costs (can be configured)
DEFAULT_TRUCKING_COST_USD = Decimal("150.00")  # Per shipment to port
DEFAULT_DOCUMENT_COST_USD = Decimal("75.00")  # Documentation fees
DEFAULT_INSURANCE_RATE = Decimal("0.005")  # 0.5% of goods value

# Freight estimates by region (per CBM)
FREIGHT_RATES_PER_CBM = {
    "US": Decimal("85.00"),
    "EU": Decimal("80.00"),
    "JP": Decimal("65.00"),
    "CN": Decimal("45.00"),
    "AU": Decimal("70.00"),
    "SG": Decimal("35.00"),
    "MY": Decimal("30.00"),
    "DEFAULT": Decimal("75.00"),
}


class CostingService:
    """
    Service class for costing calculations.
    Implements PBI-BE-M4-06 to M4-09.
    """

    def __init__(self):
        self.exchange_rate = self._get_exchange_rate()

    def _get_exchange_rate(self) -> Decimal:
        """Get current IDR to USD exchange rate."""
        return Decimal(str(ExchangeRate.get_current_rate("IDR", "USD")))

    def _to_decimal(self, value) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def calculate_exw_price(
        self,
        cogs_per_unit: Decimal,
        packing_cost: Decimal,
        target_margin_percent: Decimal,
    ) -> dict:
        """
        # PBI-BE-M4-06: AI Price Calculator - EXW
        #
        # Acceptance Criteria:
        # ✅ Input: cogs_per_unit, packing_cost, target_margin_percent
        # ✅ Formula: EXW = (cogs + packing) × (1 + margin/100)
        # ✅ Convert IDR to USD using exchange rate
        # ✅ Output: recommended_exw_price (decimal, USD)

        Args:
            cogs_per_unit: Cost of goods sold per unit (IDR)
            packing_cost: Packing cost per unit (IDR)
            target_margin_percent: Target profit margin percentage

        Returns:
            Dictionary with EXW price calculation details
        """
        cogs = self._to_decimal(cogs_per_unit)
        packing = self._to_decimal(packing_cost)
        margin = self._to_decimal(target_margin_percent)

        # Calculate base cost in IDR
        base_cost_idr = cogs + packing

        # Apply margin
        margin_multiplier = Decimal("1") + (margin / Decimal("100"))
        exw_price_idr = base_cost_idr * margin_multiplier

        # Convert to USD
        exw_price_usd = (exw_price_idr * self.exchange_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "base_cost_idr": base_cost_idr,
            "exw_price_idr": exw_price_idr,
            "exw_price_usd": exw_price_usd,
            "exchange_rate": self.exchange_rate,
        }

    def calculate_fob_price(
        self,
        exw_price_usd: Decimal,
        business_address: str = "",
    ) -> dict:
        """
        # PBI-BE-M4-07: AI Price Calculator - FOB
        #
        # Acceptance Criteria:
        # ✅ Input: EXW price, business address (for trucking estimate)
        # ✅ Estimate trucking cost based on location to nearest port
        # ✅ Estimate document cost (flat rate or percentage)
        # ✅ Formula: FOB = EXW + trucking + document
        # ✅ Output: recommended_fob_price (decimal, USD)

        Args:
            exw_price_usd: EXW price in USD
            business_address: Business address for trucking estimate

        Returns:
            Dictionary with FOB price calculation details
        """
        exw = self._to_decimal(exw_price_usd)

        # Estimate trucking cost based on location
        # In production, this could be more sophisticated based on actual address
        trucking_cost = self._estimate_trucking_cost(business_address)

        # Document cost
        document_cost = DEFAULT_DOCUMENT_COST_USD

        # Calculate FOB
        fob_price_usd = exw + trucking_cost + document_cost

        return {
            "exw_price_usd": exw,
            "trucking_cost_usd": trucking_cost,
            "document_cost_usd": document_cost,
            "fob_price_usd": fob_price_usd.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
        }

    def _estimate_trucking_cost(self, address: str) -> Decimal:
        """
        Estimate trucking cost to nearest port based on address.
        Simplified version - in production, could use actual distance calculations.
        """
        if not address:
            return DEFAULT_TRUCKING_COST_USD

        address_lower = address.lower()

        # Major port cities have lower trucking costs
        port_cities = ["jakarta", "surabaya", "semarang", "makassar", "medan"]
        for city in port_cities:
            if city in address_lower:
                return Decimal("75.00")  # Near port

        # Inner islands (Java, Sumatra) moderate cost
        inner_regions = ["jawa", "java", "sumatra", "sumatera", "bali"]
        for region in inner_regions:
            if region in address_lower:
                return Decimal("150.00")

        # Outer islands higher cost
        return Decimal("250.00")

    def calculate_cif_price(
        self,
        fob_price_usd: Decimal,
        target_country_code: str = None,
        product_volume_cbm: Decimal = Decimal("0.01"),
    ) -> dict:
        """
        # PBI-BE-M4-08: AI Price Calculator - CIF
        #
        # Acceptance Criteria:
        # ✅ Input: FOB price, target_country (if available from ExportAnalysis)
        # ✅ Estimate freight based on destination country
        # ✅ Insurance = 0.5% of goods value (default)
        # ✅ Formula: CIF = FOB + freight + insurance
        # ✅ Output: recommended_cif_price (decimal, USD)
        # ✅ If no target country, CIF = null

        Args:
            fob_price_usd: FOB price in USD
            target_country_code: Target country code (optional)
            product_volume_cbm: Product volume in cubic meters

        Returns:
            Dictionary with CIF price calculation details or None if no target country
        """
        if not target_country_code:
            return None

        fob = self._to_decimal(fob_price_usd)
        volume = self._to_decimal(product_volume_cbm)

        # Get freight rate for destination
        freight_rate = FREIGHT_RATES_PER_CBM.get(
            target_country_code.upper(),
            FREIGHT_RATES_PER_CBM["DEFAULT"]
        )

        # Calculate freight (minimum 1 CBM)
        effective_volume = max(volume, Decimal("0.1"))
        freight_cost = freight_rate * effective_volume

        # Calculate insurance (0.5% of FOB value)
        insurance_cost = fob * DEFAULT_INSURANCE_RATE

        # Calculate CIF
        cif_price_usd = fob + freight_cost + insurance_cost

        return {
            "fob_price_usd": fob,
            "freight_cost_usd": freight_cost.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "insurance_cost_usd": insurance_cost.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "cif_price_usd": cif_price_usd.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "target_country": target_country_code,
        }

    def calculate_container_capacity(
        self,
        dimensions: dict,
        weight_per_unit: Decimal = Decimal("1.0"),
    ) -> dict:
        """
        # PBI-BE-M4-09: AI Container Optimizer
        #
        # Acceptance Criteria:
        # ✅ Input: dimensions_l_w_h (from Product)
        # ✅ Container 20ft dimensions: 5.9m × 2.35m × 2.39m internal
        # ✅ Algorithm: 3D bin packing calculation
        # ✅ Output: container_20ft_capacity (integer, units)
        # ✅ Generate optimization_notes if ada saran improvement

        Args:
            dimensions: Product dimensions {"l": cm, "w": cm, "h": cm}
            weight_per_unit: Weight per unit in kg

        Returns:
            Dictionary with container capacity and optimization notes
        """
        # Get dimensions, default to reasonable size if not provided
        dim_l = Decimal(str(dimensions.get("l", 30))) / Decimal("100")  # cm to m
        dim_w = Decimal(str(dimensions.get("w", 20))) / Decimal("100")
        dim_h = Decimal(str(dimensions.get("h", 10))) / Decimal("100")

        weight = self._to_decimal(weight_per_unit)

        # Calculate capacity for 20ft container
        capacity_20ft, notes_20ft = self._calculate_single_container_capacity(
            CONTAINER_20FT, dim_l, dim_w, dim_h, weight
        )

        # Calculate capacity for 40ft container
        capacity_40ft, notes_40ft = self._calculate_single_container_capacity(
            CONTAINER_40FT, dim_l, dim_w, dim_h, weight
        )

        # Generate optimization suggestions
        optimization_notes = self._generate_optimization_notes(
            dim_l, dim_w, dim_h, capacity_20ft, CONTAINER_20FT
        )

        return {
            "container_20ft_capacity": capacity_20ft,
            "container_40ft_capacity": capacity_40ft,
            "optimization_notes": optimization_notes,
            "product_dimensions_m": {
                "l": float(dim_l),
                "w": float(dim_w),
                "h": float(dim_h),
            },
        }

    def _calculate_single_container_capacity(
        self,
        container: dict,
        dim_l: Decimal,
        dim_w: Decimal,
        dim_h: Decimal,
        weight_per_unit: Decimal,
    ) -> tuple:
        """
        Calculate how many units fit in a container using simple 3D packing.
        Returns (capacity, notes)
        """
        if dim_l <= 0 or dim_w <= 0 or dim_h <= 0:
            return 0, "Invalid product dimensions"

        cont_l = container["length"]
        cont_w = container["width"]
        cont_h = container["height"]
        max_weight = container["max_weight_kg"]

        # Try different orientations and find the best fit
        orientations = [
            (dim_l, dim_w, dim_h),
            (dim_l, dim_h, dim_w),
            (dim_w, dim_l, dim_h),
            (dim_w, dim_h, dim_l),
            (dim_h, dim_l, dim_w),
            (dim_h, dim_w, dim_l),
        ]

        max_capacity = 0
        best_orientation = None

        for l, w, h in orientations:
            if l > cont_l or w > cont_w or h > cont_h:
                continue

            # Calculate units per dimension
            units_l = int(cont_l / l)
            units_w = int(cont_w / w)
            units_h = int(cont_h / h)

            capacity = units_l * units_w * units_h

            if capacity > max_capacity:
                max_capacity = capacity
                best_orientation = (l, w, h)

        # Check weight constraint
        if weight_per_unit > 0:
            max_by_weight = int(max_weight / float(weight_per_unit))
            if max_by_weight < max_capacity:
                return max_by_weight, "Limited by weight capacity"

        notes = f"Best orientation: {best_orientation}" if best_orientation else ""
        return max_capacity, notes

    def _generate_optimization_notes(
        self,
        dim_l: Decimal,
        dim_w: Decimal,
        dim_h: Decimal,
        current_capacity: int,
        container: dict,
    ) -> str:
        """Generate optimization suggestions."""
        notes = []

        cont_l = container["length"]
        cont_w = container["width"]
        cont_h = container["height"]

        # Check for wasted space
        # Try reducing each dimension by 1cm and see if capacity increases
        test_reduction = Decimal("0.01")  # 1cm

        for dim_name, dim_val in [("length", dim_l), ("width", dim_w), ("height", dim_h)]:
            if dim_val > test_reduction:
                new_dim = dim_val - test_reduction

                # Recalculate with reduced dimension
                dims = {"l": dim_l, "w": dim_w, "h": dim_h}
                dims[dim_name[0]] = new_dim

                new_capacity, _ = self._calculate_single_container_capacity(
                    container,
                    dims["l"], dims["w"], dims["h"],
                    Decimal("1.0")
                )

                if new_capacity > current_capacity:
                    increase = new_capacity - current_capacity
                    notes.append(
                        f"Reducing {dim_name} by 1cm could add +{increase} units per container"
                    )

        # Check total utilization
        product_volume = dim_l * dim_w * dim_h
        container_volume = cont_l * cont_w * cont_h
        total_product_volume = product_volume * current_capacity
        utilization = (total_product_volume / container_volume) * 100

        if utilization < 70:
            notes.append(
                f"Container utilization is {utilization:.1f}%. Consider adjusting packaging."
            )

        return " | ".join(notes) if notes else "Dimensions are well optimized for container shipping."

    def calculate_full_costing(
        self,
        cogs_per_unit: Decimal,
        packing_cost: Decimal,
        target_margin_percent: Decimal,
        business_address: str = "",
        target_country_code: str = None,
        product_dimensions: dict = None,
        product_weight: Decimal = None,
    ) -> dict:
        """
        Calculate full costing including EXW, FOB, CIF, and container optimization.

        Returns complete costing data for saving to database.
        """
        # Calculate EXW
        exw_result = self.calculate_exw_price(
            cogs_per_unit, packing_cost, target_margin_percent
        )

        # Calculate FOB
        fob_result = self.calculate_fob_price(
            exw_result["exw_price_usd"], business_address
        )

        # Calculate product volume for CIF
        product_volume = Decimal("0.01")  # Default
        if product_dimensions:
            l = Decimal(str(product_dimensions.get("l", 30))) / Decimal("100")
            w = Decimal(str(product_dimensions.get("w", 20))) / Decimal("100")
            h = Decimal(str(product_dimensions.get("h", 10))) / Decimal("100")
            product_volume = l * w * h

        # Calculate CIF (if target country provided)
        cif_result = None
        if target_country_code:
            cif_result = self.calculate_cif_price(
                fob_result["fob_price_usd"],
                target_country_code,
                product_volume
            )

        # Calculate container capacity
        container_result = {"container_20ft_capacity": None, "container_40ft_capacity": None, "optimization_notes": ""}
        if product_dimensions:
            container_result = self.calculate_container_capacity(
                product_dimensions,
                product_weight or Decimal("1.0")
            )

        return {
            "recommended_exw_price": exw_result["exw_price_usd"],
            "recommended_fob_price": fob_result["fob_price_usd"],
            "recommended_cif_price": cif_result["cif_price_usd"] if cif_result else None,
            "trucking_cost_usd": fob_result["trucking_cost_usd"],
            "document_cost_usd": fob_result["document_cost_usd"],
            "freight_cost_usd": cif_result["freight_cost_usd"] if cif_result else None,
            "insurance_cost_usd": cif_result["insurance_cost_usd"] if cif_result else None,
            "container_20ft_capacity": container_result["container_20ft_capacity"],
            "container_40ft_capacity": container_result["container_40ft_capacity"],
            "optimization_notes": container_result["optimization_notes"],
            "exchange_rate_used": self.exchange_rate,
            "target_country_code": target_country_code,
        }
