"""
Export Analysis Models for ExportReady.AI

Implements:
# PBI-BE-M3-14: Database: ExportAnalysis Table
# - Create table sesuai ER Diagram
# - Foreign key ke Product dan Country
# - Unique constraint pada (product_id, target_country_code)
# - JSON column untuk compliance_issues
# - Index pada product_id dan target_country_code

All database models for Module 3 are implemented in this module.
"""

from django.db import models


class Country(models.Model):
    """
    # PBI-BE-M3-11, M3-12: Country master data
    # - country_code: ISO 3166-1 alpha-2 (e.g., "US", "JP", "AU")
    # - country_name: Full country name
    # - region: Geographic region for grouping
    """

    country_code = models.CharField(max_length=2, primary_key=True)
    country_name = models.CharField(max_length=100)
    region = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "countries"
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["country_name"]

    def __str__(self):
        return f"{self.country_code} - {self.country_name}"


class RuleCategory(models.TextChoices):
    """
    Rule category choices for CountryRegulation.
    Based on ER Diagram: Enum: Ingredient, Labeling, Physical
    """

    INGREDIENT = "Ingredient", "Ingredient"
    LABELING = "Labeling", "Labeling"
    PHYSICAL = "Physical", "Physical"


class CountryRegulation(models.Model):
    """
    # PBI-BE-M3-04, M3-05, M3-06: Country regulations for compliance checking
    # Based on ER Diagram:
    # - rule_category: Enum (Ingredient, Labeling, Physical)
    # - forbidden_keywords: e.g., "Pewarna K10", "Sawit Non-RSPO"
    # - required_specs: e.g., "Allergen Info", "Presisi 1mm"
    # - description_rule: Full description of the rule
    """

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="regulations",
    )
    rule_category = models.CharField(
        max_length=20,
        choices=RuleCategory.choices,
    )
    forbidden_keywords = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated banned keywords, e.g., 'Pewarna K10, Sawit Non-RSPO'",
    )
    required_specs = models.TextField(
        blank=True,
        default="",
        help_text="Required specifications, e.g., 'Allergen Info, Presisi 1mm'",
    )
    description_rule = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "country_regulations"
        verbose_name = "Country Regulation"
        verbose_name_plural = "Country Regulations"
        indexes = [
            models.Index(fields=["country", "rule_category"]),
        ]

    def __str__(self):
        return f"{self.country_id} - {self.rule_category}"


class StatusGrade(models.TextChoices):
    """
    Status grade for ExportAnalysis.
    Based on ER Diagram: Enum: Ready, Warning, Critical
    """

    READY = "Ready", "Ready"
    WARNING = "Warning", "Warning"
    CRITICAL = "Critical", "Critical"


class ExportAnalysis(models.Model):
    """
    # PBI-BE-M3-14: ExportAnalysis Table
    #
    # Acceptance Criteria:
    # [DONE] Foreign key ke Product dan Country
    # [DONE] Unique constraint pada (product_id, target_country_code)
    # [DONE] JSON column untuk compliance_issues
    # [DONE] Index pada product_id dan target_country_code
    # [DONE] status_grade: Enum (Ready, Warning, Critical)
    # [DONE] Product snapshot for audit trail
    # [DONE] Regulation recommendations cache
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="export_analyses",
    )
    target_country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="export_analyses",
    )
    readiness_score = models.IntegerField(default=0, help_text="Score 0-100")
    status_grade = models.CharField(
        max_length=10,
        choices=StatusGrade.choices,
        default=StatusGrade.WARNING,
    )
    compliance_issues = models.JSONField(
        default=list,
        help_text="Detail temuan AI (Missing Spec, Banned Item)",
    )
    recommendations = models.TextField(blank=True, default="")
    
    # Product snapshot for audit trail and proper versioning
    product_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of product data at analysis time (includes product and enrichment data)",
    )
    
    # Regulation snapshot for historical record
    regulation_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of regulations checked at analysis time",
    )
    
    # Cached regulation recommendations to avoid regenerating
    regulation_recommendations_cache = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached detailed regulation recommendations",
    )
    
    analyzed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "export_analyses"
        verbose_name = "Export Analysis"
        verbose_name_plural = "Export Analyses"
        unique_together = ["product", "target_country"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["target_country"]),
            models.Index(fields=["readiness_score"]),
        ]

    def __str__(self):
        return f"Analysis: {self.product.name_local} -> {self.target_country.country_name}"
    
    def create_product_snapshot(self, product):
        """
        Create a snapshot of product data for audit trail.
        Captures both product base data and enrichment data.
        
        Args:
            product: Product model instance
        
        Returns:
            dict: Product snapshot with all relevant data
        """
        snapshot = {
            # Basic product information
            "product_id": product.id,
            "business_id": product.business_id,
            "name_local": product.name_local,
            "category_id": product.category_id,
            "description_local": product.description_local,
            "material_composition": product.material_composition,
            "production_technique": product.production_technique,
            "finishing_type": product.finishing_type,
            "quality_specs": product.quality_specs,
            "durability_claim": product.durability_claim,
            "packaging_type": product.packaging_type,
            "dimensions_l_w_h": product.dimensions_l_w_h,
            "weight_net": str(product.weight_net),
            "weight_gross": str(product.weight_gross),
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat(),
        }
        
        # Add enrichment data if available
        if hasattr(product, "enrichment") and product.enrichment:
            enrichment = product.enrichment
            snapshot["enrichment"] = {
                "hs_code_recommendation": enrichment.hs_code_recommendation,
                "sku_generated": enrichment.sku_generated,
                "name_english_b2b": enrichment.name_english_b2b,
                "description_english_b2b": enrichment.description_english_b2b,
                "marketing_highlights": enrichment.marketing_highlights,
                "last_updated_ai": enrichment.last_updated_ai.isoformat(),
            }
        else:
            snapshot["enrichment"] = None
        
        return snapshot
    
    def get_snapshot_product_name(self):
        """Get product name from snapshot, fallback to current product."""
        if self.product_snapshot and "name_local" in self.product_snapshot:
            return self.product_snapshot["name_local"]
        return self.product.name_local if self.product else "Unknown Product"
    
    def is_product_changed(self):
        """
        Check if the current product data differs from the snapshot.
        Returns True if product has been updated after analysis.
        """
        if not self.product_snapshot:
            return False
        
        try:
            product = self.product
            snapshot_updated = self.product_snapshot.get("updated_at")
            if snapshot_updated:
                from dateutil import parser
                snapshot_time = parser.isoparse(snapshot_updated)
                return product.updated_at > snapshot_time
        except Exception:
            pass
        
        return False
