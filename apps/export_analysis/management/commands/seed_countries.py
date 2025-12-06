"""
Management command to seed country and regulation data for testing.
"""

from django.core.management.base import BaseCommand

from apps.export_analysis.models import Country, CountryRegulation, RuleCategory


class Command(BaseCommand):
    help = "Seed country and regulation data for Module 3 testing"

    def handle(self, *args, **options):
        self.stdout.write("Seeding countries and regulations...")

        # Define countries
        countries_data = [
            {"country_code": "US", "country_name": "United States", "region": "North America"},
            {"country_code": "JP", "country_name": "Japan", "region": "Asia"},
            {"country_code": "DE", "country_name": "Germany", "region": "Europe"},
            {"country_code": "AU", "country_name": "Australia", "region": "Oceania"},
            {"country_code": "SG", "country_name": "Singapore", "region": "Asia"},
            {"country_code": "CN", "country_name": "China", "region": "Asia"},
            {"country_code": "KR", "country_name": "South Korea", "region": "Asia"},
            {"country_code": "GB", "country_name": "United Kingdom", "region": "Europe"},
            {"country_code": "NL", "country_name": "Netherlands", "region": "Europe"},
            {"country_code": "AE", "country_name": "United Arab Emirates", "region": "Middle East"},
        ]

        # Create countries
        for data in countries_data:
            country, created = Country.objects.get_or_create(
                country_code=data["country_code"],
                defaults={
                    "country_name": data["country_name"],
                    "region": data["region"],
                },
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  {status}: {country}")

        # Define regulations
        regulations_data = [
            # United States
            {
                "country_code": "US",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Pewarna K10, Formalin, Boraks, Rhodamine B",
                "required_specs": "",
                "description_rule": "FDA regulations prohibit certain food additives and colorings",
            },
            {
                "country_code": "US",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "Nutrition Facts, Allergen Info, Country of Origin",
                "description_rule": "FDA requires nutrition labeling and allergen declaration",
            },
            {
                "country_code": "US",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "ISPM-15 (wood packaging), FDA Registration",
                "description_rule": "Wood packaging must comply with ISPM-15 standards",
            },
            # Japan
            {
                "country_code": "JP",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Pewarna Buatan, MSG berlebih, Bahan Non-Halal",
                "required_specs": "",
                "description_rule": "Japan Food Sanitation Act regulates food additives strictly",
            },
            {
                "country_code": "JP",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "Japanese Language Label, Allergen Info (28 items), Best Before Date",
                "description_rule": "Labels must be in Japanese with specific allergen declarations",
            },
            {
                "country_code": "JP",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "JAS Certification, Presisi 1mm",
                "description_rule": "Japanese Agricultural Standard (JAS) may be required",
            },
            # Germany/EU
            {
                "country_code": "DE",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Sawit Non-RSPO, Pewarna Azo, GMO",
                "required_specs": "",
                "description_rule": "EU regulations on sustainable palm oil and GMO-free requirements",
            },
            {
                "country_code": "DE",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "CE Marking, Allergen Info, Nutritional Info, German/English Label",
                "description_rule": "EU labeling regulations with CE marking requirements",
            },
            {
                "country_code": "DE",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "CE Certification, EU Conformity Assessment",
                "description_rule": "Products must meet EU safety and quality standards",
            },
            # Australia
            {
                "country_code": "AU",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Propolis mentah, Madu non-standar, Bahan dari tanaman invasif",
                "required_specs": "",
                "description_rule": "Strict biosecurity requirements for food imports",
            },
            {
                "country_code": "AU",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "Country of Origin, Allergen Declaration, Nutritional Info Panel",
                "description_rule": "Australian Consumer Law requires specific labeling",
            },
            {
                "country_code": "AU",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "ISPM-15, Fumigation Certificate, Biosecurity Clearance",
                "description_rule": "Strict quarantine and biosecurity requirements for all packaging",
            },
            # Singapore
            {
                "country_code": "SG",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Pewarna Terlarang, Bahan Non-Halal (untuk produk Halal)",
                "required_specs": "",
                "description_rule": "Singapore Food Agency regulates food additives",
            },
            {
                "country_code": "SG",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "English Label, Nutrition Information Panel, Allergen Info",
                "description_rule": "Labels must be in English with nutrition panel",
            },
            {
                "country_code": "SG",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "SFA Import License, Halal Certification (if applicable)",
                "description_rule": "Import license from SFA required for food products",
            },
            # China
            {
                "country_code": "CN",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Bahan Terlarang China, Pewarna Sintetis Tertentu",
                "required_specs": "",
                "description_rule": "GACC regulations on food safety",
            },
            {
                "country_code": "CN",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "Chinese Language Label, GB Standards Compliance, CIQ Inspection",
                "description_rule": "Must comply with GB national standards, labels in Chinese",
            },
            {
                "country_code": "CN",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "CCC Certification, GACC Registration",
                "description_rule": "China Compulsory Certification for certain products",
            },
            # UAE
            {
                "country_code": "AE",
                "rule_category": RuleCategory.INGREDIENT,
                "forbidden_keywords": "Babi, Alkohol, Gelatin Non-Halal, Lemak Hewani Non-Halal",
                "required_specs": "",
                "description_rule": "All food products must be Halal compliant",
            },
            {
                "country_code": "AE",
                "rule_category": RuleCategory.LABELING,
                "forbidden_keywords": "",
                "required_specs": "Arabic Label, Halal Certification, Expiry Date, Country of Origin",
                "description_rule": "Labels must include Arabic text and Halal certification",
            },
            {
                "country_code": "AE",
                "rule_category": RuleCategory.PHYSICAL,
                "forbidden_keywords": "",
                "required_specs": "ESMA Certification, Halal Certificate from approved body",
                "description_rule": "Emirates Authority for Standardization requirements",
            },
        ]

        # Create regulations
        for data in regulations_data:
            country = Country.objects.get(country_code=data["country_code"])
            reg, created = CountryRegulation.objects.get_or_create(
                country=country,
                rule_category=data["rule_category"],
                defaults={
                    "forbidden_keywords": data["forbidden_keywords"],
                    "required_specs": data["required_specs"],
                    "description_rule": data["description_rule"],
                },
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  {status}: {country.country_code} - {reg.rule_category}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded countries and regulations!"))
