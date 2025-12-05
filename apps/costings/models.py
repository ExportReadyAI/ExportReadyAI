"""
Costing Model for ExportReady.AI Module 4

Stores cost breakdown and pricing calculations for products.
"""

from django.db import models
from apps.products.models import Product


class Costing(models.Model):
    """
    Costing model for product pricing and container optimization.
    
    PBI-BE-M4-03, PBI-BE-M4-04, PBI-BE-M4-05, PBI-BE-M4-14
    
    Relationships:
    - FK to Product (1-to-many: one product can have multiple costing versions)
    - Stores input costs and AI-calculated prices (EXW, FOB, CIF)
    - Includes container capacity estimation
    """
    
    # PBI-BE-M4-14: Foreign key to Product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="costings",
        help_text="Product this costing is calculated for"
    )
    
    # PBI-BE-M4-03, PBI-BE-M4-04: Cost inputs
    cogs_per_unit = models.DecimalField(
        "Cost of Goods Sold per unit (IDR)",
        max_digits=15,
        decimal_places=2,
        help_text="Biaya produksi per unit dalam IDR"
    )
    
    packing_cost = models.DecimalField(
        "Packing cost per unit (IDR)",
        max_digits=15,
        decimal_places=2,
        help_text="Biaya packing/kemasan ekspor per unit dalam IDR"
    )
    
    target_margin_percent = models.DecimalField(
        "Target profit margin (%)",
        max_digits=5,
        decimal_places=2,
        default=30.00,
        help_text="Target margin keuntungan dalam persen"
    )
    
    # PBI-BE-M4-06, PBI-BE-M4-07, PBI-BE-M4-08: AI-calculated prices
    recommended_exw_price = models.DecimalField(
        "Recommended Ex-Works price (USD)",
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Harga Ex-Works yang direkomendasikan (USD)"
    )
    
    recommended_fob_price = models.DecimalField(
        "Recommended FOB price (USD)",
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Harga FOB yang direkomendasikan (USD)"
    )
    
    recommended_cif_price = models.DecimalField(
        "Recommended CIF price (USD)",
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Harga CIF (dengan freight & insurance) dalam USD"
    )
    
    # PBI-BE-M4-09: Container optimization
    container_20ft_capacity = models.IntegerField(
        "20ft Container capacity (units)",
        null=True,
        blank=True,
        help_text="Estimasi jumlah unit yang muat dalam 20ft container"
    )
    
    optimization_notes = models.TextField(
        "Container optimization notes",
        blank=True,
        help_text="Saran dari AI untuk optimasi container/packaging"
    )
    
    # Timestamps
    calculated_at = models.DateTimeField(
        "Last calculated timestamp",
        auto_now=True,
        help_text="Waktu terakhir perhitungan dilakukan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Costing"
        verbose_name_plural = "Costings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product_id"]),
            models.Index(fields=["-calculated_at"]),
        ]
    
    def __str__(self):
        return f"Costing for {self.product.name_local} - EXW: ${self.recommended_exw_price}"


class ExchangeRate(models.Model):
    """
    Current IDR-USD exchange rate for costing calculations.
    
    PBI-BE-M4-10, PBI-BE-M4-11, PBI-BE-M4-12
    
    Usually only one active record at a time.
    Stores rate, source, and update timestamp.
    """
    
    rate = models.DecimalField(
        "IDR to USD exchange rate",
        max_digits=10,
        decimal_places=2,
        help_text="Nilai tukar IDR ke USD (e.g., 15800)"
    )
    
    source = models.CharField(
        "Rate source",
        max_length=100,
        default="manual",
        choices=[
            ("manual", "Manual Update by Admin"),
            ("api", "External API"),
            ("bank", "Bank Source"),
        ],
        help_text="Sumber data nilai tukar"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Waktu terakhir update rate"
    )
    
    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"IDR/USD: {self.rate} ({self.source}) - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
