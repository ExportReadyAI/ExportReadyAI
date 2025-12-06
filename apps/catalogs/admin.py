"""
Admin configuration for Product Catalog Module
"""

from django.contrib import admin
from .models import ProductCatalog, ProductCatalogImage, CatalogVariant


class ProductCatalogImageInline(admin.TabularInline):
    model = ProductCatalogImage
    extra = 1
    fields = ("image_url", "alt_text", "sort_order", "is_primary")


class CatalogVariantInline(admin.TabularInline):
    model = CatalogVariant
    extra = 1
    fields = ("variant_name", "attributes", "variant_price", "moq_variant", "sku", "is_available")


@admin.register(ProductCatalog)
class ProductCatalogAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "product",
        "is_published",
        "base_price_exw",
        "min_order_quantity",
        "unit_type",
        "updated_at",
    )
    list_filter = ("is_published", "unit_type", "created_at")
    search_fields = ("display_name", "product__name_local", "marketing_description")
    readonly_fields = ("published_at", "created_at", "updated_at")
    inlines = [ProductCatalogImageInline, CatalogVariantInline]

    fieldsets = (
        ("Product Link", {
            "fields": ("product",)
        }),
        ("Display Information", {
            "fields": ("display_name", "marketing_description", "tags")
        }),
        ("Publishing", {
            "fields": ("is_published", "published_at")
        }),
        ("Pricing", {
            "fields": ("base_price_exw", "base_price_fob", "base_price_cif")
        }),
        ("Order Settings", {
            "fields": ("min_order_quantity", "unit_type", "lead_time_days", "available_stock")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ProductCatalogImage)
class ProductCatalogImageAdmin(admin.ModelAdmin):
    list_display = ("catalog", "image_url", "sort_order", "is_primary", "created_at")
    list_filter = ("is_primary", "created_at")
    search_fields = ("catalog__display_name", "alt_text")


@admin.register(CatalogVariant)
class CatalogVariantAdmin(admin.ModelAdmin):
    list_display = ("catalog", "variant_name", "variant_price", "moq_variant", "sku", "is_available")
    list_filter = ("is_available", "created_at")
    search_fields = ("catalog__display_name", "variant_name", "sku")
