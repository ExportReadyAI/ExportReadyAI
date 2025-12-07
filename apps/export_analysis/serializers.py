"""
Serializers for ExportReady.AI Module 3

Implements serializers for:
# PBI-BE-M3-01, M3-02: Export Analysis list and detail responses
# PBI-BE-M3-03: Export Analysis creation with validation
# PBI-BE-M3-11, M3-12: Country list and detail responses
# PBI-BE-M3-13: Multi-country comparison
"""

from rest_framework import serializers

from apps.products.models import Product

from .models import Country, CountryRegulation, ExportAnalysis


# PBI-BE-M3-11, M3-12: Country serializers
class CountryRegulationSerializer(serializers.ModelSerializer):
    """
    Serializer for CountryRegulation model.
    Used in country detail response.
    """

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


class CountryListSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M3-11: Country list serializer
    # [DONE] Include: regulations_count
    """

    regulations_count = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = [
            "country_code",
            "country_name",
            "region",
            "regulations_count",
        ]

    def get_regulations_count(self, obj):
        return obj.regulations.count()


class CountryDetailSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M3-12: Country detail serializer
    # [DONE] Include: semua CountryRegulation grouped by type
    """

    regulations = CountryRegulationSerializer(many=True, read_only=True)
    regulations_by_category = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = [
            "country_code",
            "country_name",
            "region",
            "regulations",
            "regulations_by_category",
            "created_at",
            "updated_at",
        ]

    def get_regulations_by_category(self, obj):
        """Group regulations by rule_category."""
        grouped = {}
        for reg in obj.regulations.all():
            category = reg.rule_category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(CountryRegulationSerializer(reg).data)
        return grouped


# PBI-BE-M3-01, M3-02: Export Analysis serializers
class ExportAnalysisListSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M3-01: Export Analysis list serializer
    # [DONE] Include: product name, country name
    """

    product_name = serializers.CharField(source="product.name_local", read_only=True)
    country_name = serializers.CharField(source="target_country.country_name", read_only=True)
    country_code = serializers.CharField(source="target_country.country_code", read_only=True)

    class Meta:
        model = ExportAnalysis
        fields = [
            "id",
            "product",
            "product_name",
            "target_country",
            "country_code",
            "country_name",
            "readiness_score",
            "status_grade",
            "analyzed_at",
            "created_at",
        ]


class ExportAnalysisDetailSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M3-02: Export Analysis detail serializer
    # [DONE] Include: product details, country details, compliance_issues, recommendations
    # [DONE] Include: product snapshot for audit trail
    """

    product_name = serializers.CharField(source="product.name_local", read_only=True)
    product_category = serializers.CharField(source="product.category_id", read_only=True)
    product_material = serializers.CharField(source="product.material_composition", read_only=True)
    product_packaging = serializers.CharField(source="product.packaging_type", read_only=True)
    country_name = serializers.CharField(source="target_country.country_name", read_only=True)
    country_code = serializers.CharField(source="target_country.country_code", read_only=True)
    country_region = serializers.CharField(source="target_country.region", read_only=True)
    
    # Snapshot information
    snapshot_product_name = serializers.SerializerMethodField()
    product_changed = serializers.SerializerMethodField()

    class Meta:
        model = ExportAnalysis
        fields = [
            "id",
            "product",
            "product_name",
            "product_category",
            "product_material",
            "product_packaging",
            "target_country",
            "country_code",
            "country_name",
            "country_region",
            "readiness_score",
            "status_grade",
            "compliance_issues",
            "recommendations",
            "product_snapshot",
            "snapshot_product_name",
            "product_changed",
            "analyzed_at",
            "created_at",
        ]
    
    def get_snapshot_product_name(self, obj):
        """Get product name from snapshot."""
        return obj.get_snapshot_product_name()
    
    def get_product_changed(self, obj):
        """Check if product has changed since analysis."""
        return obj.is_product_changed()


class ExportAnalysisCreateSerializer(serializers.Serializer):
    """
    # PBI-BE-M3-03: Export Analysis creation serializer
    # [DONE] Body: product_id, target_country_code
    # [DONE] Validasi: product milik user
    # [DONE] Validasi: product sudah punya ProductEnrichment
    # [DONE] Validasi: kombinasi product + country belum ada
    """

    product_id = serializers.IntegerField()
    target_country_code = serializers.CharField(max_length=2)

    def validate_product_id(self, value):
        """Validate product exists and belongs to user."""
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is required")

        try:
            product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

        # Check ownership (UMKM can only analyze their own products)
        if not request.user.is_staff:
            if not hasattr(request.user, "business_profile"):
                raise serializers.ValidationError("User does not have a business profile")
            if product.business_id != request.user.business_profile.id:
                raise serializers.ValidationError("You can only analyze your own products")

        # Check if product has enrichment
        if not hasattr(product, "enrichment"):
            raise serializers.ValidationError(
                "Product must be enriched first. Use /api/v1/products/{id}/enrich/"
            )

        return value

    def validate_target_country_code(self, value):
        """Validate country exists."""
        try:
            Country.objects.get(country_code=value.upper())
        except Country.DoesNotExist:
            raise serializers.ValidationError(f"Country '{value}' not found")
        return value.upper()

    def validate(self, attrs):
        """Validate combination doesn't exist."""
        product_id = attrs.get("product_id")
        country_code = attrs.get("target_country_code")

        if ExportAnalysis.objects.filter(
            product_id=product_id,
            target_country_id=country_code,
        ).exists():
            raise serializers.ValidationError(
                "Analysis for this product and country combination already exists"
            )

        return attrs


class ExportAnalysisCompareSerializer(serializers.Serializer):
    """
    # PBI-BE-M3-13: Multi-country comparison serializer
    # [DONE] Body: product_id, country_codes (array, max 5)
    """

    product_id = serializers.IntegerField()
    country_codes = serializers.ListField(
        child=serializers.CharField(max_length=2),
        min_length=1,
        max_length=5,
    )

    def validate_product_id(self, value):
        """Validate product exists and belongs to user."""
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is required")

        try:
            product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

        # Check ownership
        if not request.user.is_staff:
            if not hasattr(request.user, "business_profile"):
                raise serializers.ValidationError("User does not have a business profile")
            if product.business_id != request.user.business_profile.id:
                raise serializers.ValidationError("You can only analyze your own products")

        # Check if product has enrichment
        if not hasattr(product, "enrichment"):
            raise serializers.ValidationError(
                "Product must be enriched first. Use /api/v1/products/{id}/enrich/"
            )

        return value

    def validate_country_codes(self, value):
        """Validate all countries exist."""
        validated_codes = []
        for code in value:
            upper_code = code.upper()
            if not Country.objects.filter(country_code=upper_code).exists():
                raise serializers.ValidationError(f"Country '{code}' not found")
            validated_codes.append(upper_code)
        return validated_codes
