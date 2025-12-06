from django.contrib import admin

from .models import Product, ProductEnrichment


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name_local", "business", "category_id", "created_at")
    search_fields = ("name_local", "business__user__email")


@admin.register(ProductEnrichment)
class ProductEnrichmentAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "hs_code_recommendation", "sku_generated", "last_updated_ai")
    search_fields = ("product__name_local", "hs_code_recommendation", "sku_generated")
