"""
Test factories for Module 4 (Costing)
"""

import factory
from faker import Faker
from decimal import Decimal
from apps.costings.models import Costing, ExchangeRate
from apps.products.tests.factories import ProductFactory

fake = Faker()


class CostingFactory(factory.django.DjangoModelFactory):
    """Factory untuk membuat test data Costing"""
    
    class Meta:
        model = Costing
    
    product = factory.SubFactory(ProductFactory)
    cogs_per_unit = Decimal("50000.00")
    packing_cost = Decimal("5000.00")
    target_margin_percent = Decimal("30.00")
    recommended_exw_price = Decimal("2.50")
    recommended_fob_price = Decimal("3.00")
    recommended_cif_price = Decimal("3.50")
    container_20ft_capacity = 800
    optimization_notes = "Good packing efficiency achieved"


class ExchangeRateFactory(factory.django.DjangoModelFactory):
    """Factory untuk membuat test data ExchangeRate"""
    
    class Meta:
        model = ExchangeRate
    
    rate = Decimal("15800.00")
    source = "manual"
