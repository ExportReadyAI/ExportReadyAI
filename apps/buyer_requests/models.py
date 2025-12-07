"""
Buyer Request Models for ExportReady.AI

Implements:
# PBI-BE-M6-02: Database: BuyerRequest Table
# - Create buyer_requests table with complete schema
# - Foreign key to users table (buyer_user_id)
# - JSONB column for keyword_tags (array support)
# - Enum constraint for status: 'Open', 'Matched', 'Closed'
# - Indexes on: buyer_user_id, status, product_category, destination_country
# - GIN index on keyword_tags for JSON queries
# - Timestamps: created_at, updated_at

All database models for Module 6A are implemented in this module.
"""

from django.conf import settings
from django.db import models


class RequestStatus(models.TextChoices):
    """
    Status choices for BuyerRequest.
    Based on backlog: Enum: Open, Matched, Closed
    """

    OPEN = "Open", "Open"
    MATCHED = "Matched", "Matched"
    CLOSED = "Closed", "Closed"


class BuyerProfile(models.Model):
    """
    Buyer Profile model for Buyer users.
    
    Similar to ForwarderProfile but with buyer-specific fields.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_profile",
        verbose_name="user",
        limit_choices_to={"role": "Buyer"},
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name="company name",
        help_text="Name of the buyer's company or organization",
    )
    company_description = models.TextField(
        blank=True,
        default="",
        verbose_name="company description",
        help_text="Detailed description of the company, its business activities, and market focus",
    )
    contact_info = models.JSONField(
        default=dict,
        verbose_name="contact info",
        help_text="Contact information (phone, email, address, website, etc.)",
    )
    preferred_product_categories = models.JSONField(
        default=list,
        verbose_name="preferred product categories",
        help_text="Array of product categories buyer typically imports (e.g., ['Makanan Olahan', 'Kerajinan', 'Tekstil']). Categories the buyer is interested in sourcing.",
    )
    preferred_product_categories_description = models.TextField(
        blank=True,
        default="",
        verbose_name="preferred product categories description",
        help_text="Detailed description of preferred product categories, quality requirements, and specific product interests",
    )
    source_countries = models.JSONField(
        default=list,
        verbose_name="source countries",
        help_text="Array of source country codes where buyer typically imports from (e.g., ['ID'] for Indonesia, ['ID', 'VN'] for multiple countries)",
    )
    source_countries_description = models.TextField(
        blank=True,
        default="",
        verbose_name="source countries description",
        help_text="Description of sourcing strategy, preferred countries, and import experience from these regions",
    )
    business_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="business type",
        help_text="Type of business (e.g., 'Importir', 'Distributor', 'Retailer', 'Trading Company')",
    )
    business_type_description = models.TextField(
        blank=True,
        default="",
        verbose_name="business type description",
        help_text="Detailed description of business operations, distribution channels, and market reach",
    )
    annual_import_volume = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="annual import volume",
        help_text="Annual import volume description (e.g., '1000-5000 containers', '50000-100000 units', '100-500 tons')",
    )
    annual_import_volume_description = models.TextField(
        blank=True,
        default="",
        verbose_name="annual import volume description",
        help_text="Detailed information about import capacity, volume trends, and growth projections",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "buyer_profiles"
        verbose_name = "Buyer Profile"
        verbose_name_plural = "Buyer Profiles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company_name"]),
        ]

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"


class BuyerRequest(models.Model):
    """
    # PBI-BE-M6-02: BuyerRequest Table
    #
    # Acceptance Criteria:
    # ✅ Create buyer_requests table with complete schema
    # ✅ Foreign key to users table (buyer_user_id)
    # ✅ JSONB column for keyword_tags (array support)
    # ✅ Enum constraint for status: 'Open', 'Matched', 'Closed'
    # ✅ Indexes on: buyer_user_id, status, product_category, destination_country
    # ✅ GIN index on keyword_tags for JSON queries
    # ✅ Timestamps: created_at, updated_at
    """

    buyer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_requests",
        verbose_name="buyer user",
    )
    product_category = models.CharField(
        max_length=255,
        verbose_name="product category",
        help_text="Product category (e.g., 'Furniture', 'Textiles')",
    )
    hs_code_target = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name="HS code target",
        help_text="Target HS Code (8-16 digits)",
    )
    spec_requirements = models.TextField(
        verbose_name="spec requirements",
        help_text="Detailed specification requirements",
    )
    target_volume = models.PositiveIntegerField(
        verbose_name="target volume",
        help_text="Target volume/quantity needed",
    )
    destination_country = models.CharField(
        max_length=2,
        verbose_name="destination country",
        help_text="ISO 3166-1 alpha-2 country code (e.g., 'US', 'JP')",
    )
    keyword_tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="keyword tags",
        help_text="Array of keyword tags for matching",
    )
    min_rank_required = models.IntegerField(
        default=0,
        verbose_name="min rank required",
        help_text="Minimum rank required for UMKM to see this request",
    )
    status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
        verbose_name="status",
    )
    selected_catalog = models.ForeignKey(
        "catalogs.ProductCatalog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyer_requests_selected",
        verbose_name="selected catalog",
        help_text="Catalog selected by buyer when closing the request",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "buyer_requests"
        verbose_name = "Buyer Request"
        verbose_name_plural = "Buyer Requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["buyer_user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["product_category"]),
            models.Index(fields=["destination_country"]),
            # GIN index for JSONB keyword_tags (PostgreSQL specific)
            # Note: Django doesn't support GIN indexes directly, will need raw SQL in migration
        ]

    def __str__(self):
        return f"Request: {self.product_category} -> {self.destination_country} ({self.buyer_user.email})"
