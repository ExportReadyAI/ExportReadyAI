"""
Models for Product Catalog Module

Implements:
- ProductCatalog: Main catalog entry for public display
- ProductCatalogImage: Multiple images per catalog
- CatalogVariant: Product variants (size, color, flavor, etc.)
"""

from django.db import models
from django.utils import timezone
from apps.products.models import Product


class ProductCatalog(models.Model):
    """
    Main catalog model for publishing products to buyers.
    Links to Product model and contains commercial/marketing information.
    """

    UNIT_TYPE_CHOICES = [
        ("pcs", "Pieces"),
        ("pack", "Pack"),
        ("kg", "Kilogram"),
        ("set", "Set"),
        ("box", "Box"),
        ("carton", "Carton"),
        ("dozen", "Dozen"),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="catalog",
        help_text="Product this catalog entry belongs to"
    )

    # Publishing status
    is_published = models.BooleanField(
        default=False,
        help_text="Whether this catalog is visible to buyers"
    )

    # Commercial display info
    display_name = models.CharField(
        max_length=255,
        help_text="Commercial name displayed to buyers"
    )
    marketing_description = models.TextField(
        blank=True,
        help_text="Marketing description (commercial, not technical)"
    )

    # Ordering info
    min_order_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text="Minimum order quantity"
    )
    unit_type = models.CharField(
        max_length=20,
        choices=UNIT_TYPE_CHOICES,
        default="pcs",
        help_text="Unit type for ordering"
    )

    # Pricing (from costing calculations)
    base_price_exw = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="EXW price in USD"
    )
    base_price_fob = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="FOB price in USD (optional)"
    )
    base_price_cif = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CIF price in USD (optional)"
    )

    # AI-Generated Content (from AI Description Generator)
    export_description = models.TextField(
        blank=True,
        help_text="AI-generated English B2B description for international buyers"
    )
    technical_specs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible technical specifications (e.g., material, moisture_level, finishing, dimensions, weight, certifications)"
    )
    safety_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Material/Food safety information (flexible based on product type)"
    )

    # Additional catalog fields
    lead_time_days = models.PositiveIntegerField(
        default=14,
        help_text="Production lead time in days"
    )
    available_stock = models.PositiveIntegerField(
        default=0,
        help_text="Available stock for immediate order"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for search/filter (e.g., ['eco-friendly', 'handmade'])"
    )

    # Timestamps
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the catalog was first published"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_catalogs"
        ordering = ["-updated_at"]
        verbose_name = "Product Catalog"
        verbose_name_plural = "Product Catalogs"

    def __str__(self):
        return f"{self.display_name} ({'Published' if self.is_published else 'Draft'})"

    def save(self, *args, **kwargs):
        # Set published_at when first published
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class ProductCatalogImage(models.Model):
    """
    Multiple images for a catalog entry.
    Supports sorting for display order.
    """

    catalog = models.ForeignKey(
        ProductCatalog,
        on_delete=models.CASCADE,
        related_name="images",
        help_text="Catalog this image belongs to"
    )
    image_url = models.URLField(
        max_length=500,
        help_text="URL to the image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for accessibility"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower = first)"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary image for thumbnail"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_catalog_images"
        ordering = ["sort_order", "id"]
        verbose_name = "Catalog Image"
        verbose_name_plural = "Catalog Images"

    def __str__(self):
        return f"Image {self.sort_order} for {self.catalog.display_name}"


class CatalogVariant(models.Model):
    """
    Product variants for a catalog entry.
    Supports different sizes, colors, flavors, etc.
    """

    catalog = models.ForeignKey(
        ProductCatalog,
        on_delete=models.CASCADE,
        related_name="variants",
        help_text="Catalog this variant belongs to"
    )
    variant_name = models.CharField(
        max_length=100,
        help_text="Variant name (e.g., 'Large', 'Spicy', 'Red')"
    )
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Variant attributes (e.g., {'color': 'red', 'size': 'L'})"
    )
    variant_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price for this variant in USD"
    )
    moq_variant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        help_text="Minimum order quantity for this variant"
    )
    sku = models.CharField(
        max_length=50,
        blank=True,
        help_text="SKU for this variant"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether this variant is available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_variants"
        ordering = ["variant_name"]
        verbose_name = "Catalog Variant"
        verbose_name_plural = "Catalog Variants"

    def __str__(self):
        return f"{self.catalog.display_name} - {self.variant_name}"


class ProductMarketIntelligence(models.Model):
    """
    AI-generated Market Intelligence for a product.
    OneToOne relationship - each product can only have ONE market intelligence result.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="market_intelligence",
        help_text="Product this market intelligence belongs to"
    )

    # Recommended countries (stored as JSON array)
    recommended_countries = models.JSONField(
        default=list,
        help_text="List of recommended target countries with details"
    )

    # Countries to avoid
    countries_to_avoid = models.JSONField(
        default=list,
        help_text="List of countries to avoid with reasons"
    )

    # Market trends
    market_trends = models.JSONField(
        default=list,
        help_text="List of relevant market trends"
    )

    # Analysis text fields
    competitive_landscape = models.TextField(
        blank=True,
        help_text="Competitive landscape analysis"
    )
    growth_opportunities = models.JSONField(
        default=list,
        help_text="List of growth opportunities"
    )
    risks_and_challenges = models.JSONField(
        default=list,
        help_text="List of risks and challenges"
    )
    overall_recommendation = models.TextField(
        blank=True,
        help_text="Overall strategic recommendation"
    )

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_market_intelligence"
        verbose_name = "Product Market Intelligence"
        verbose_name_plural = "Product Market Intelligence"

    def __str__(self):
        return f"Market Intelligence for {self.product.name_local}"


class ProductPricingResult(models.Model):
    """
    AI-generated Pricing Result for a product.
    OneToOne relationship - each product can only have ONE pricing result.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="pricing_result",
        help_text="Product this pricing result belongs to"
    )

    # Input parameters
    cogs_per_unit_idr = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cost of goods sold per unit in IDR"
    )
    target_margin_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Target margin percentage"
    )
    target_country_code = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Target country for CIF calculation"
    )

    # Calculated prices
    exchange_rate_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Exchange rate used for calculation"
    )
    exw_price_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="EXW price in USD"
    )
    fob_price_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="FOB price in USD"
    )
    cif_price_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="CIF price in USD (if target country provided)"
    )

    # AI Insight
    pricing_insight = models.TextField(
        blank=True,
        help_text="AI-generated pricing insight and recommendations"
    )

    # Pricing breakdown (JSON)
    pricing_breakdown = models.JSONField(
        default=dict,
        help_text="Detailed pricing breakdown"
    )

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_pricing_results"
        verbose_name = "Product Pricing Result"
        verbose_name_plural = "Product Pricing Results"

    def __str__(self):
        return f"Pricing for {self.product.name_local}: EXW ${self.exw_price_usd}"
