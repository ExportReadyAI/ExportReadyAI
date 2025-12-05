"""
Serializers for ExportReady.AI Module 5 - Master Data

# PBI-BE-M5-01 to M5-05: HSCode serializers
# PBI-BE-M5-06 to M5-08: Country admin serializers
# PBI-BE-M5-09 to M5-13: Regulation admin serializers
"""

from rest_framework import serializers

from apps.export_analysis.models import Country, CountryRegulation

from .models import HSCode, HSSection


# ============================================================================
# HSSection Serializers
# ============================================================================

class HSSectionSerializer(serializers.ModelSerializer):
    """Serializer for HS Sections"""

    class Meta:
        model = HSSection
        fields = ["section", "name"]


# ============================================================================
# HSCode Serializers
# ============================================================================

# PBI-BE-M5-01: [DONE] GET /hs-codes - List serializer
class HSCodeListSerializer(serializers.ModelSerializer):
    """Serializer for listing HS Codes"""
    section_name = serializers.CharField(source="section.name", read_only=True, default="")

    class Meta:
        model = HSCode
        fields = [
            "hs_code",
            "description",
            "description_id",
            "level",
            "hs_chapter",
            "hs_heading",
            "hs_subheading",
            "section",
            "section_name",
        ]


# PBI-BE-M5-01: [DONE] GET /hs-codes/:code - Detail serializer
class HSCodeDetailSerializer(serializers.ModelSerializer):
    """Serializer for HS Code detail"""
    section_detail = HSSectionSerializer(source="section", read_only=True)
    parent_code = serializers.CharField(source="parent.hs_code", read_only=True, default=None)
    children = serializers.SerializerMethodField()

    class Meta:
        model = HSCode
        fields = [
            "hs_code",
            "description",
            "description_id",
            "level",
            "hs_chapter",
            "hs_heading",
            "hs_subheading",
            "section",
            "section_detail",
            "parent_code",
            "children",
            "keywords",
            "created_at",
            "updated_at",
        ]

    def get_children(self, obj):
        children = obj.children.all()[:10]  # Limit to 10 children
        return [{"hs_code": c.hs_code, "description": c.description} for c in children]


# PBI-BE-M5-02: [DONE] POST /hs-codes - Create serializer
class HSCodeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating HS Code

    Acceptance Criteria:
    - Body: hs_code, description_id, description_en, keywords
    - Auto-extract: hs_chapter, hs_heading, hs_subheading
    - Validasi: hs_code format (2-8 digit)
    - Validasi: hs_code unique
    """
    description_en = serializers.CharField(write_only=True, source="description")

    class Meta:
        model = HSCode
        fields = [
            "hs_code",
            "description_en",
            "description_id",
            "keywords",
            "section",
            "parent",
        ]

    def validate_hs_code(self, value):
        """Validate HS code format"""
        # Remove dots and spaces
        clean_code = value.replace(".", "").replace(" ", "")

        if not clean_code.isdigit():
            raise serializers.ValidationError("HS Code must contain only digits")

        if len(clean_code) < 2 or len(clean_code) > 8:
            raise serializers.ValidationError("HS Code must be 2-8 digits")

        # Check uniqueness
        if HSCode.objects.filter(hs_code=clean_code).exists():
            raise serializers.ValidationError("HS Code already exists")

        return clean_code

    def create(self, validated_data):
        # Auto-determine level based on code length
        code = validated_data["hs_code"]
        if len(code) <= 2:
            validated_data["level"] = 2
        elif len(code) <= 4:
            validated_data["level"] = 4
        else:
            validated_data["level"] = 6

        return super().create(validated_data)


# PBI-BE-M5-03: [DONE] PUT /hs-codes/:code - Update serializer
class HSCodeUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating HS Code

    Note: hs_code cannot be changed
    """

    class Meta:
        model = HSCode
        fields = [
            "description",
            "description_id",
            "keywords",
            "section",
            "parent",
        ]


# PBI-BE-M5-05: [DONE] POST /hs-codes/import - Bulk import serializer
class HSCodeImportSerializer(serializers.Serializer):
    """Serializer for CSV import validation"""
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV")
        return value


# ============================================================================
# Country Admin Serializers (extend Module 3)
# ============================================================================

# PBI-BE-M5-06: [DONE] POST /countries - Create country
class CountryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Country (Admin)

    Acceptance Criteria:
    - Body: country_code, country_name, region
    - Validasi: country_code format (2 char ISO)
    - Validasi: country_code unique
    """

    class Meta:
        model = Country
        fields = ["country_code", "country_name", "region"]

    def validate_country_code(self, value):
        """Validate country code format"""
        if len(value) != 2:
            raise serializers.ValidationError("Country code must be 2 characters (ISO 3166)")

        if not value.isalpha():
            raise serializers.ValidationError("Country code must contain only letters")

        value = value.upper()

        if Country.objects.filter(country_code=value).exists():
            raise serializers.ValidationError("Country code already exists")

        return value


# PBI-BE-M5-07: [DONE] PUT /countries/:code - Update country
class CountryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Country (Admin)

    Note: country_code cannot be changed
    """

    class Meta:
        model = Country
        fields = ["country_name", "region"]


# ============================================================================
# Regulation Admin Serializers
# ============================================================================

# PBI-BE-M5-09: [DONE] GET /countries/:code/regulations
class RegulationListSerializer(serializers.ModelSerializer):
    """Serializer for listing regulations"""

    class Meta:
        model = CountryRegulation
        fields = [
            "id",
            "rule_category",
            "forbidden_keywords",
            "required_specs",
            "description_rule",
            "created_at",
            "updated_at",
        ]


# PBI-BE-M5-10: [DONE] POST /countries/:code/regulations - Create regulation
class RegulationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Regulation (Admin)

    Acceptance Criteria:
    - Body: rule_category, forbidden_keywords, required_specs, description_rule
    - Validasi: rule_category enum valid
    """

    class Meta:
        model = CountryRegulation
        fields = [
            "rule_category",
            "forbidden_keywords",
            "required_specs",
            "description_rule",
        ]

    def validate_rule_category(self, value):
        """Validate rule category is valid enum"""
        from apps.export_analysis.models import RuleCategory
        valid_categories = [choice[0] for choice in RuleCategory.choices]
        if value not in valid_categories:
            raise serializers.ValidationError(
                f"Invalid rule_category. Must be one of: {valid_categories}"
            )
        return value


# PBI-BE-M5-11: [DONE] PUT /regulations/:id - Update regulation
class RegulationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Regulation (Admin)"""

    class Meta:
        model = CountryRegulation
        fields = [
            "rule_category",
            "forbidden_keywords",
            "required_specs",
            "description_rule",
        ]


# PBI-BE-M5-13: [DONE] POST /regulations/import - Bulk import
class RegulationImportSerializer(serializers.Serializer):
    """Serializer for CSV import validation"""
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV")
        return value
