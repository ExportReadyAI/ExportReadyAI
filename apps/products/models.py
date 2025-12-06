from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.business_profiles.models import BusinessProfile


# PBI-BE-M2-11: Database - Product Table
# Create table dengan schema sesuai ER Diagram
class Product(models.Model):
    business = models.ForeignKey(
        BusinessProfile, on_delete=models.CASCADE, related_name="products"
    )
    name_local = models.CharField(max_length=255)
    category_id = models.IntegerField()
    description_local = models.TextField()
    material_composition = models.TextField(blank=True)
    production_technique = models.CharField(max_length=50, blank=True)
    finishing_type = models.CharField(max_length=50, blank=True)
    quality_specs = models.JSONField(default=dict, blank=True)
    durability_claim = models.CharField(max_length=255, blank=True)
    packaging_type = models.CharField(max_length=100, blank=True)
    dimensions_l_w_h = models.JSONField(default=dict, blank=True)
    weight_net = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)])
    weight_gross = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_product"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name_local} ({self.business.user.email})"


# PBI-BE-M2-12: Database - ProductEnrichment Table
# Create table dengan schema sesuai ER Diagram
# Foreign key ke Product (1-to-1), Foreign key ke HSCode (nullable), Timestamp: last_updated_ai
class ProductEnrichment(models.Model):
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="enrichment"
    )
    hs_code_recommendation = models.CharField(max_length=16, blank=True, null=True)
    sku_generated = models.CharField(max_length=64, blank=True, null=True)
    name_english_b2b = models.CharField(max_length=255, blank=True, null=True)
    description_english_b2b = models.TextField(blank=True, null=True)
    marketing_highlights = models.JSONField(default=list, blank=True)
    last_updated_ai = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "products_productenrichment"

    def __str__(self):
        return f"Enrichment for {self.product_id}"
