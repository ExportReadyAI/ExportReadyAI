from django.contrib import admin

from .models import HSCode, HSSection


@admin.register(HSSection)
class HSSectionAdmin(admin.ModelAdmin):
    list_display = ["section", "name"]
    search_fields = ["section", "name"]
    ordering = ["section"]


@admin.register(HSCode)
class HSCodeAdmin(admin.ModelAdmin):
    list_display = ["hs_code", "description_short", "level", "hs_chapter", "section"]
    list_filter = ["level", "section"]
    search_fields = ["hs_code", "description"]
    ordering = ["hs_code"]
    raw_id_fields = ["parent"]

    def description_short(self, obj):
        return obj.description[:80] + "..." if len(obj.description) > 80 else obj.description
    description_short.short_description = "Description"
