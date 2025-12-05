"""
Tests for Module 4 Services (Price Calculator, Container Optimizer)
"""

import pytest
from decimal import Decimal
from apps.costings.services import PriceCalculatorService, ContainerOptimizerService, CostingService
from apps.costings.tests.factories import ExchangeRateFactory
from apps.products.tests.factories import ProductFactory


@pytest.mark.django_db
class TestPriceCalculatorService:
    """Test PBI-BE-M4-06, M4-07, M4-08: Price calculation services"""
    
    def setup_method(self):
        """Setup exchange rate for tests"""
        ExchangeRateFactory(rate=Decimal("15800.00"))
    
    def test_calculate_exw(self):
        """PBI-BE-M4-06: Test EXW price calculation"""
        # Input: COGS 50k, packing 5k, margin 30%
        # Calculation: (50k + 5k) × 1.30 = 71.5k IDR = ~4.52 USD
        exw = PriceCalculatorService.calculate_exw(
            cogs_per_unit_idr=Decimal("50000"),
            packing_cost_idr=Decimal("5000"),
            target_margin_percent=Decimal("30")
        )
        
        assert exw > 0
        assert exw < Decimal("10")  # Should be reasonable USD price
        assert isinstance(exw, Decimal)
    
    def test_calculate_fob(self):
        """PBI-BE-M4-07: Test FOB price calculation"""
        exw = Decimal("5.00")
        fob = PriceCalculatorService.calculate_fob(exw, business_address_estimate_km=100)
        
        assert fob > exw  # FOB should be higher than EXW
        assert fob < Decimal("100")  # Reasonable upper bound
        assert isinstance(fob, Decimal)
    
    def test_calculate_cif_with_country(self):
        """PBI-BE-M4-08: Test CIF price calculation with country"""
        fob = Decimal("10.00")
        cif = PriceCalculatorService.calculate_cif(fob, target_country_code="US")
        
        assert cif is not None
        assert cif > fob  # CIF should be higher than FOB
        assert isinstance(cif, Decimal)
    
    def test_calculate_cif_without_country(self):
        """Test CIF returns None without target country"""
        fob = Decimal("10.00")
        cif = PriceCalculatorService.calculate_cif(fob, target_country_code=None)
        
        assert cif is None


@pytest.mark.django_db
class TestContainerOptimizerService:
    """Test PBI-BE-M4-09: Container optimization"""
    
    def test_calculate_container_capacity(self):
        """Test 20ft container capacity calculation"""
        # Small box: 20cm × 15cm × 10cm
        result = ContainerOptimizerService.calculate_container_capacity(
            product_length_cm=20,
            product_width_cm=15,
            product_height_cm=10
        )
        
        assert "capacity" in result
        assert "notes" in result
        assert result["capacity"] > 0
        assert isinstance(result["capacity"], int)
    
    def test_container_capacity_with_weight_limit(self):
        """Test container capacity with weight constraint"""
        # Heavy item: 30kg per unit
        result = ContainerOptimizerService.calculate_container_capacity(
            product_length_cm=50,
            product_width_cm=40,
            product_height_cm=30,
            weight_per_unit_kg=30
        )
        
        # Should be limited by weight (17500/30 ≈ 583 units max)
        assert result["capacity"] <= 600
        assert "Weight-limited" in result["notes"] or result["capacity"] > 0


@pytest.mark.django_db
class TestCostingService:
    """Test PBI-BE-M4-03, M4-04: Full costing orchestration"""
    
    def setup_method(self):
        """Setup exchange rate"""
        ExchangeRateFactory(rate=Decimal("15800.00"))
    
    def test_calculate_full_costing(self):
        """Test complete costing calculation"""
        product = ProductFactory()
        
        result = CostingService.calculate_full_costing(
            product=product,
            cogs_per_unit_idr=Decimal("50000"),
            packing_cost_idr=Decimal("5000"),
            target_margin_percent=Decimal("30"),
            target_country_code="US"
        )
        
        assert "recommended_exw_price" in result
        assert "recommended_fob_price" in result
        assert "recommended_cif_price" in result
        assert "container_20ft_capacity" in result
        assert "optimization_notes" in result
        
        assert result["recommended_exw_price"] > 0
        assert result["recommended_fob_price"] > result["recommended_exw_price"]
        assert result["recommended_cif_price"] > result["recommended_fob_price"]
        assert result["container_20ft_capacity"] > 0
