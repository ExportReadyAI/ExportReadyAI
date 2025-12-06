"""
Django Admin configuration for Module 7: Educational Materials (Simplified)
"""

from django.contrib import admin

from .models import Module, Article


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "order_index", "article_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["title", "description"]
    ordering = ["order_index", "-created_at"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "module", "order_index", "created_at"]
    list_filter = ["module", "created_at"]
    search_fields = ["title", "content"]
    ordering = ["module", "order_index", "-created_at"]
