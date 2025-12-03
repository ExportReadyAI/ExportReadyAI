"""
BusinessProfile Model for ExportReady.AI

One-to-one relationship with User model.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class CertificationType(models.TextChoices):
    """
    Valid certification types for business profiles.
    """

    HALAL = "Halal", "Halal"
    ISO = "ISO", "ISO"
    HACCP = "HACCP", "HACCP"
    SVLK = "SVLK", "SVLK"


class BusinessProfile(models.Model):
    """
    Business Profile model for UMKM users.
    
    Fields:
        - id: Primary key (auto-generated)
        - user: One-to-one relationship with User
        - company_name: Name of the company
        - address: Business address
        - production_capacity_per_month: Monthly production capacity
        - certifications: JSON array of certifications (Halal, ISO, HACCP, SVLK)
        - year_established: Year the business was established
        - created_at: Timestamp when profile was created
        - updated_at: Timestamp when profile was last updated
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_profile",
        verbose_name="user",
    )
    company_name = models.CharField("company name", max_length=255)
    address = models.TextField("address")
    production_capacity_per_month = models.PositiveIntegerField(
        "production capacity per month",
        validators=[MinValueValidator(1)],
    )
    certifications = models.JSONField(
        "certifications",
        default=list,
        blank=True,
        help_text="Array of certifications: Halal, ISO, HACCP, SVLK",
    )
    year_established = models.PositiveIntegerField(
        "year established",
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2100),
        ],
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        verbose_name = "business profile"
        verbose_name_plural = "business profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"

    @property
    def certification_count(self):
        return len(self.certifications) if self.certifications else 0

