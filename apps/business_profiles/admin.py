"""
BusinessProfile Admin Configuration
"""

from django.contrib import admin

from .models import BusinessProfile


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for BusinessProfile model.
    """

    list_display = [
        "company_name",
        "user",
        "year_established",
        "production_capacity_per_month",
        "certification_count",
        "created_at",
    ]
    list_filter = ["year_established", "created_at"]
    search_fields = ["company_name", "user__email", "user__full_name"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("user", "company_name")}),
        ("Business Details", {"fields": ("address", "production_capacity_per_month", "year_established")}),
        ("Certifications", {"fields": ("certifications",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def certification_count(self, obj):
        return obj.certification_count

    certification_count.short_description = "Certifications"

