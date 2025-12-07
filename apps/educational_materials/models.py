"""
Simplified Models for Module 7: Educational Materials

Only Modules and Articles (simple CRUD, no progress tracking)
"""

from django.core.validators import MinValueValidator
from django.conf import settings
from django.db import models


class Module(models.Model):
    """
    Module model - represents a category/topic for articles.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="title",
        help_text="Title of the module",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="description",
        help_text="Description of the module",
    )
    order_index = models.IntegerField(
        default=0,
        verbose_name="order index",
        help_text="Order for display",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "modules"
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["order_index", "-created_at"]
        indexes = [
            models.Index(fields=["order_index"]),
        ]

    def __str__(self):
        return self.title

    @property
    def article_count(self):
        """Get total number of articles in this module."""
        return self.articles.count()


class Article(models.Model):
    """
    Article model - represents educational content/articles.
    """

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="module",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="title",
        help_text="Title of the article",
    )
    content = models.TextField(
        verbose_name="content",
        help_text="Article content (Markdown supported)",
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="video url",
        help_text="Optional video URL (YouTube, Vimeo, etc.)",
    )
    file_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="file url",
        help_text="Optional file URL (PDF, image, etc.)",
    )
    order_index = models.IntegerField(
        default=0,
        verbose_name="order index",
        help_text="Order within the module",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "articles"
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ["order_index", "-created_at"]
        indexes = [
            models.Index(fields=["module", "order_index"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.module.title})"
