from django.contrib import admin
from .models import BuyerRequest, BuyerProfile


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "user", "business_type", "created_at"]
    list_filter = ["business_type", "created_at"]
    search_fields = ["company_name", "user__email", "business_type"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(BuyerRequest)
class BuyerRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer_user", "product_category", "destination_country", "status", "created_at"]
    list_filter = ["status", "product_category", "destination_country"]
    search_fields = ["product_category", "spec_requirements", "buyer_user__email"]
    readonly_fields = ["created_at", "updated_at"]

