"""
Admin configuration for Product Catalog Module
"""

from django.contrib import admin
from .models import ProductCatalog, ProductCatalogImage, CatalogVariantType, CatalogVariantOption


class ProductCatalogImageInline(admin.TabularInline):
    model = ProductCatalogImage
    extra = 1
    fields = ("image_url", "alt_text", "sort_order", "is_primary")


class CatalogVariantOptionInline(admin.TabularInline):
    model = CatalogVariantOption
    extra = 1
    fields = ("option_name", "sort_order", "is_available")


class CatalogVariantTypeInline(admin.TabularInline):
    model = CatalogVariantType
    extra = 1
    fields = ("type_code", "type_name", "sort_order")
    show_change_link = True


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
    inlines = [ProductCatalogImageInline, CatalogVariantTypeInline]

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


@admin.register(CatalogVariantType)
class CatalogVariantTypeAdmin(admin.ModelAdmin):
    list_display = ("catalog", "type_code", "type_name", "sort_order", "created_at")
    list_filter = ("type_code", "created_at")
    search_fields = ("catalog__display_name", "type_name")
    inlines = [CatalogVariantOptionInline]


@admin.register(CatalogVariantOption)
class CatalogVariantOptionAdmin(admin.ModelAdmin):
    list_display = ("variant_type", "option_name", "sort_order", "is_available", "created_at")
    list_filter = ("is_available", "created_at")
    search_fields = ("variant_type__type_name", "option_name")
