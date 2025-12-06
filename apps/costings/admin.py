from django.contrib import admin
from .models import Costing, ExchangeRate


@admin.register(Costing)
class CostingAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "recommended_exw_price", "recommended_fob_price", "calculated_at")
    list_filter = ("calculated_at", "created_at")
    search_fields = ("product__name_local",)
    readonly_fields = ("calculated_at", "created_at", "updated_at")
    
    fieldsets = (
        ("Product", {
            "fields": ("product",)
        }),
        ("Cost Inputs", {
            "fields": ("cogs_per_unit", "packing_cost", "target_margin_percent")
        }),
        ("Calculated Prices", {
            "fields": ("recommended_exw_price", "recommended_fob_price", "recommended_cif_price")
        }),
        ("Container Optimization", {
            "fields": ("container_20ft_capacity", "optimization_notes")
        }),
        ("Timestamps", {
            "fields": ("calculated_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("rate", "source", "updated_at")
    list_filter = ("source", "updated_at")
    readonly_fields = ("updated_at",)
    
    fieldsets = (
        ("Exchange Rate", {
            "fields": ("rate", "source", "updated_at")
        }),
    )
