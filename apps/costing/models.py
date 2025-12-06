"""
Models for ExportReady.AI Module 4 - Costing & Financial Calculator

PBI-BE-M4-14: Database - Costing Table
PBI-BE-M4-10: Currency Exchange Rate Storage
"""

from django.db import models
from django.core.validators import MinValueValidator

from apps.products.models import Product


class ExchangeRate(models.Model):
    """
    Store currency exchange rates (IDR to USD).

    PBI-BE-M4-10: Currency Exchange Rate
    - Option 1: Fetch from external API
    - Option 2: Manual update by Admin
    - Cache rate to reduce API calls
    """

    currency_from = models.CharField(max_length=3, default="IDR")
    currency_to = models.CharField(max_length=3, default="USD")
    rate = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(0)],
        help_text="Exchange rate (e.g., 0.000063 for IDR to USD)"
    )
    source = models.CharField(
        max_length=50,
        default="manual",
        help_text="Source of rate: 'manual', 'api', etc."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "costing_exchangerate"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.currency_from}/{self.currency_to}: {self.rate}"

    @classmethod
    def get_current_rate(cls, from_currency="IDR", to_currency="USD"):
        """Get the most recent exchange rate."""
        rate = cls.objects.filter(
            currency_from=from_currency,
            currency_to=to_currency
        ).first()
        if rate:
            return rate.rate
        # Default fallback rate (approximately 1 USD = 15,800 IDR)
        return 0.0000633


class Costing(models.Model):
    """
    Costing model for financial calculations.

    PBI-BE-M4-14: Database - Costing Table
    - Foreign key to Product
    - Decimal columns with proper precision
    - Index on product_id
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="costings"
    )

    # Input fields (from user)
    cogs_per_unit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Cost of Goods Sold per unit (IDR)"
    )
    packing_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Packing cost per unit (IDR)"
    )
    target_margin_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Target profit margin percentage"
    )

    # Calculated fields - Prices in USD
    recommended_exw_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="EXW price in USD"
    )
    recommended_fob_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="FOB price in USD"
    )
    recommended_cif_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CIF price in USD (if target country available)"
    )

    # Cost breakdown in USD
    trucking_cost_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated trucking cost to port (USD)"
    )
    document_cost_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Documentation cost (USD)"
    )
    freight_cost_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Freight cost to destination (USD)"
    )
    insurance_cost_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Insurance cost (USD)"
    )

    # Container optimization
    container_20ft_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of units that fit in 20ft container"
    )
    container_40ft_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of units that fit in 40ft container"
    )
    optimization_notes = models.TextField(
        blank=True,
        help_text="AI suggestions for optimization"
    )

    # Exchange rate used for calculation
    exchange_rate_used = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="IDR to USD rate used for calculation"
    )

    # Target country for CIF calculation (optional)
    target_country_code = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Target country for CIF calculation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "costing_costing"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"Costing for {self.product.name_local}"
