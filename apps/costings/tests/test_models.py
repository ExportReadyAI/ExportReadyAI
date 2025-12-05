"""
Tests for Module 4 Models
"""

import pytest
from decimal import Decimal
from apps.costings.models import Costing, ExchangeRate
from .factories import CostingFactory, ExchangeRateFactory


@pytest.mark.django_db
class TestCostingModel:
    """Test cases for Costing model"""
    
    def test_costing_creation(self):
        """PBI-BE-M4-14: Test creating a costing record"""
        costing = CostingFactory()
        assert costing.id is not None
        assert costing.product is not None
        assert costing.cogs_per_unit == Decimal("50000.00")
        assert costing.recommended_exw_price == Decimal("2.50")
    
    def test_costing_str_representation(self):
        """Test costing string representation"""
        costing = CostingFactory(
            recommended_exw_price=Decimal("10.00")
        )
        assert "Costing for" in str(costing)
        assert "EXW: $10.00" in str(costing)
    
    def test_costing_timestamps(self):
        """Test that timestamps are set correctly"""
        costing = CostingFactory()
        assert costing.created_at is not None
        assert costing.updated_at is not None
        assert costing.calculated_at is not None


@pytest.mark.django_db
class TestExchangeRateModel:
    """Test cases for ExchangeRate model"""
    
    def test_exchange_rate_creation(self):
        """PBI-BE-M4-10: Test creating exchange rate record"""
        rate = ExchangeRateFactory(rate=Decimal("15800.00"))
        assert rate.id is not None
        assert rate.rate == Decimal("15800.00")
        assert rate.source == "manual"
    
    def test_exchange_rate_str_representation(self):
        """Test exchange rate string representation"""
        rate = ExchangeRateFactory()
        assert "IDR/USD" in str(rate)
        assert "15800.00" in str(rate)
    
    def test_latest_exchange_rate(self):
        """Test retrieving latest exchange rate"""
        import time
        rate1 = ExchangeRateFactory(rate=Decimal("15500.00"))
        time.sleep(0.01)  # Ensure timestamp difference
        rate2 = ExchangeRateFactory(rate=Decimal("16000.00"))
        
        latest = ExchangeRate.objects.latest("updated_at")
        assert latest.rate == Decimal("16000.00")
