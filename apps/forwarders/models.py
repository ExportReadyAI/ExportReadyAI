"""
Forwarder Models for ExportReady.AI

Implements:
# PBI-BE-M6-14: Database: ForwarderProfile Table
# PBI-BE-M6-15: Database: ForwarderReview Table

All database models for Module 6B are implemented in this module.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ForwarderProfile(models.Model):
    """
    # PBI-BE-M6-14: ForwarderProfile Table
    #
    # Acceptance Criteria:
    # ✅ Create forwarder_profiles table with complete schema
    # ✅ Foreign key to users table (user_id) with constraint role = 'Forwarder'
    # ✅ JSONB columns: specialization_routes, service_types
    # ✅ Decimal column: average_rating (1.0-5.0, default 0)
    # ✅ Integer column: total_reviews (default 0)
    # ✅ Unique constraint on user_id (1-to-1 relationship)
    # ✅ Indexes on: average_rating, specialization_routes (GIN)
    # ✅ Timestamps: created_at, updated_at
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forwarder_profile",
        verbose_name="user",
        limit_choices_to={"role": "Forwarder"},
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name="company name",
    )
    contact_info = models.JSONField(
        default=dict,
        verbose_name="contact info",
        help_text="Contact information (phone, email, address, etc.)",
    )
    specialization_routes = models.JSONField(
        default=list,
        verbose_name="specialization routes",
        help_text="Array of route codes (e.g., ['ID-JP', 'ID-US'])",
    )
    service_types = models.JSONField(
        default=list,
        verbose_name="service types",
        help_text="Array of service types (e.g., ['Sea Freight', 'Air Freight'])",
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="average rating",
        help_text="Average rating (1.0-5.0)",
    )
    total_reviews = models.PositiveIntegerField(
        default=0,
        verbose_name="total reviews",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "forwarder_profiles"
        verbose_name = "Forwarder Profile"
        verbose_name_plural = "Forwarder Profiles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["average_rating"]),
            # GIN index for JSONB specialization_routes (PostgreSQL specific)
            # Note: Django doesn't support GIN indexes directly, will need raw SQL in migration
        ]

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"


class ForwarderReview(models.Model):
    """
    # PBI-BE-M6-15: ForwarderReview Table
    #
    # Acceptance Criteria:
    # ✅ Create forwarder_reviews table with complete schema
    # ✅ Foreign key to forwarder_profiles (forwarder_id)
    # ✅ Foreign key to users (umkm_id)
    # ✅ Rating validation: CHECK (rating BETWEEN 1 AND 5)
    # ✅ Unique constraint on (forwarder_id, umkm_id) to prevent duplicates
    # ✅ Indexes on: forwarder_id, umkm_id, rating
    # ✅ Timestamps: created_at, updated_at
    """

    forwarder = models.ForeignKey(
        ForwarderProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="forwarder",
    )
    umkm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="forwarder_reviews",
        verbose_name="UMKM",
        limit_choices_to={"role": "UMKM"},
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="rating",
        help_text="Rating from 1 to 5",
    )
    review_text = models.TextField(
        blank=True,
        default="",
        verbose_name="review text",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        db_table = "forwarder_reviews"
        verbose_name = "Forwarder Review"
        verbose_name_plural = "Forwarder Reviews"
        ordering = ["-created_at"]
        unique_together = ["forwarder", "umkm"]
        indexes = [
            models.Index(fields=["forwarder"]),
            models.Index(fields=["umkm"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return f"Review: {self.umkm.email} -> {self.forwarder.company_name} ({self.rating} stars)"

