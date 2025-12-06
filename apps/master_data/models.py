"""
Master Data Models for ExportReady.AI
HSCode database for product classification
"""

from django.db import models


# PBI-BE-M5-14: Database - HSSection Table
class HSSection(models.Model):
    """
    HS Code Sections (21 sections total)
    Example: Section I = Live animals; animal products
    """
    section = models.CharField(max_length=5, primary_key=True)  # Roman numerals: I, II, III...
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "master_hs_sections"
        ordering = ["section"]
        verbose_name = "HS Section"
        verbose_name_plural = "HS Sections"

    def __str__(self):
        return f"Section {self.section}: {self.name}"


# PBI-BE-M5-14: Database - HSCode Table
class HSCode(models.Model):
    """
    Harmonized System Codes for international trade classification
    Data source: https://github.com/datasets/harmonized-system

    Structure:
    - Level 2: Chapter (2 digits) - e.g., "01" = Live animals
    - Level 4: Heading (4 digits) - e.g., "0101" = Horses, asses, mules
    - Level 6: Subheading (6 digits) - e.g., "010121" = Pure-bred breeding horses
    """
    hs_code = models.CharField(max_length=16, primary_key=True)  # The HS code itself
    section = models.ForeignKey(
        HSSection,
        on_delete=models.CASCADE,
        related_name="hs_codes",
        null=True,
        blank=True
    )
    description = models.TextField()  # English description from dataset
    description_id = models.TextField(blank=True, default="")  # Indonesian translation (optional)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )
    level = models.IntegerField(default=6)  # 2, 4, or 6

    # Derived fields for easy querying
    hs_chapter = models.CharField(max_length=2, blank=True, default="")  # First 2 digits
    hs_heading = models.CharField(max_length=4, blank=True, default="")  # First 4 digits
    hs_subheading = models.CharField(max_length=6, blank=True, default="")  # First 6 digits

    # For AI matching
    keywords = models.JSONField(default=list, blank=True)  # Keywords for AI matching

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "master_hs_codes"
        ordering = ["hs_code"]
        verbose_name = "HS Code"
        verbose_name_plural = "HS Codes"
        indexes = [
            models.Index(fields=["hs_chapter"]),
            models.Index(fields=["hs_heading"]),
            models.Index(fields=["level"]),
        ]

    def save(self, *args, **kwargs):
        # Auto-populate derived fields based on hs_code length
        code = self.hs_code.replace(".", "").replace(" ", "")
        if len(code) >= 2:
            self.hs_chapter = code[:2]
        if len(code) >= 4:
            self.hs_heading = code[:4]
        if len(code) >= 6:
            self.hs_subheading = code[:6]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hs_code} - {self.description[:50]}"

    @property
    def full_hierarchy(self):
        """Get full hierarchy from chapter to this code"""
        hierarchy = []
        current = self
        while current:
            hierarchy.insert(0, {
                "code": current.hs_code,
                "description": current.description,
                "level": current.level
            })
            current = current.parent
        return hierarchy
