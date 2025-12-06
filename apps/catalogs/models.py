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
