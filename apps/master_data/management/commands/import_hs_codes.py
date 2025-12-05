"""
Management Command to Import HS Codes from GitHub Dataset
Source: https://github.com/datasets/harmonized-system

PBI-BE-M5-05: Bulk import HS codes
"""

import csv
import os
import urllib.request
from io import StringIO

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.master_data.models import HSCode, HSSection


class Command(BaseCommand):
    help = "Import HS Codes from GitHub datasets/harmonized-system repository"

    SECTIONS_URL = "https://raw.githubusercontent.com/datasets/harmonized-system/master/data/sections.csv"
    HS_CODES_URL = "https://raw.githubusercontent.com/datasets/harmonized-system/master/data/harmonized-system.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing HS codes before import",
        )
        parser.add_argument(
            "--local",
            type=str,
            help="Path to local CSV file instead of downloading from GitHub",
        )
        parser.add_argument(
            "--sections-only",
            action="store_true",
            help="Import only sections",
        )
        parser.add_argument(
            "--codes-only",
            action="store_true",
            help="Import only HS codes (assumes sections exist)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting HS Code import..."))

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            HSCode.objects.all().delete()
            HSSection.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing data"))

        try:
            with transaction.atomic():
                if not options["codes_only"]:
                    self.import_sections()

                if not options["sections_only"]:
                    if options["local"]:
                        self.import_hs_codes_from_file(options["local"])
                    else:
                        self.import_hs_codes_from_url()

            self.stdout.write(self.style.SUCCESS("HS Code import completed successfully!"))
            self.print_summary()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import failed: {str(e)}"))
            raise

    def fetch_csv(self, url):
        """Fetch CSV content from URL"""
        self.stdout.write(f"Fetching {url}...")
        with urllib.request.urlopen(url, timeout=30) as response:
            # Use utf-8-sig to handle BOM character
            content = response.read().decode("utf-8-sig")
        return content

    def import_sections(self):
        """Import HS sections"""
        self.stdout.write(self.style.NOTICE("Importing sections..."))

        content = self.fetch_csv(self.SECTIONS_URL)
        reader = csv.DictReader(StringIO(content))

        sections_created = 0
        sections_updated = 0

        for row in reader:
            section, created = HSSection.objects.update_or_create(
                section=row["section"],
                defaults={"name": row["name"]}
            )
            if created:
                sections_created += 1
            else:
                sections_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sections: {sections_created} created, {sections_updated} updated"
            )
        )

    def import_hs_codes_from_url(self):
        """Import HS codes from GitHub URL"""
        content = self.fetch_csv(self.HS_CODES_URL)
        self.process_hs_codes_csv(StringIO(content))

    def import_hs_codes_from_file(self, filepath):
        """Import HS codes from local file"""
        self.stdout.write(f"Reading from {filepath}...")
        with open(filepath, "r", encoding="utf-8") as f:
            self.process_hs_codes_csv(f)

    def process_hs_codes_csv(self, csv_file):
        """Process HS codes CSV data"""
        self.stdout.write(self.style.NOTICE("Importing HS codes..."))

        reader = csv.DictReader(csv_file)
        rows = list(reader)
        total = len(rows)

        self.stdout.write(f"Found {total} HS code entries to process...")

        # First pass: Create all HS codes without parent references
        codes_created = 0
        codes_updated = 0
        batch_size = 500

        # Process in batches for progress reporting
        for i, row in enumerate(rows):
            section_id = row.get("section")
            hs_code = row.get("hscode", "").strip()
            description = row.get("description", "").strip()
            level = int(row.get("level", 6))

            if not hs_code:
                continue

            # Get section reference
            section = None
            if section_id:
                try:
                    section = HSSection.objects.get(section=section_id)
                except HSSection.DoesNotExist:
                    pass

            obj, created = HSCode.objects.update_or_create(
                hs_code=hs_code,
                defaults={
                    "section": section,
                    "description": description,
                    "level": level,
                }
            )

            if created:
                codes_created += 1
            else:
                codes_updated += 1

            # Progress update
            if (i + 1) % batch_size == 0:
                self.stdout.write(f"  Processed {i + 1}/{total} entries...")

        self.stdout.write(
            self.style.SUCCESS(
                f"HS Codes: {codes_created} created, {codes_updated} updated"
            )
        )

        # Second pass: Update parent references
        self.stdout.write(self.style.NOTICE("Setting up parent-child relationships..."))

        # Reset CSV reader
        if hasattr(csv_file, "seek"):
            csv_file.seek(0)
            reader = csv.DictReader(csv_file)
            rows = list(reader)

        parents_set = 0
        for row in rows:
            hs_code = row.get("hscode", "").strip()
            parent_code = row.get("parent", "").strip()

            if not hs_code or not parent_code or parent_code == "TOTAL":
                continue

            try:
                code_obj = HSCode.objects.get(hs_code=hs_code)
                parent_obj = HSCode.objects.filter(hs_code=parent_code).first()

                if parent_obj and code_obj.parent_id != parent_obj.hs_code:
                    code_obj.parent = parent_obj
                    code_obj.save(update_fields=["parent"])
                    parents_set += 1
            except HSCode.DoesNotExist:
                continue

        self.stdout.write(
            self.style.SUCCESS(f"Parent relationships: {parents_set} set")
        )

    def print_summary(self):
        """Print import summary"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("IMPORT SUMMARY")
        self.stdout.write("=" * 50)

        sections_count = HSSection.objects.count()
        codes_count = HSCode.objects.count()
        chapters_count = HSCode.objects.filter(level=2).count()
        headings_count = HSCode.objects.filter(level=4).count()
        subheadings_count = HSCode.objects.filter(level=6).count()

        self.stdout.write(f"Total Sections:    {sections_count}")
        self.stdout.write(f"Total HS Codes:    {codes_count}")
        self.stdout.write(f"  - Chapters (L2): {chapters_count}")
        self.stdout.write(f"  - Headings (L4): {headings_count}")
        self.stdout.write(f"  - Subheadings (L6): {subheadings_count}")
        self.stdout.write("=" * 50 + "\n")
