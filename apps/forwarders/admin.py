from django.contrib import admin
from .models import ForwarderProfile, ForwarderReview


@admin.register(ForwarderProfile)
class ForwarderProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "user", "average_rating", "total_reviews", "created_at"]
    list_filter = ["average_rating", "created_at"]
    search_fields = ["company_name", "user__email"]
    readonly_fields = ["created_at", "updated_at", "average_rating", "total_reviews"]


@admin.register(ForwarderReview)
class ForwarderReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "forwarder", "umkm", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["forwarder__company_name", "umkm__email", "review_text"]
    readonly_fields = ["created_at", "updated_at"]

