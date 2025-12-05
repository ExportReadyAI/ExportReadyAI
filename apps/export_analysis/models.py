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
