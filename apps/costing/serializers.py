"""
Serializers for ExportReady.AI Module 4 - Costing & Financial Calculator

# PBI-BE-M4-01 to M4-05: Costing CRUD serializers
# PBI-BE-M4-11, M4-12: Exchange Rate serializers
"""

from rest_framework import serializers

from apps.products.models import Product

from .models import Costing, ExchangeRate


# ============================================================================
# Exchange Rate Serializers
# ============================================================================

class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M4-11: GET /exchange-rate
    Serializer for reading exchange rate.
    """

    class Meta:
        model = ExchangeRate
        fields = ["rate", "source", "updated_at", "currency_from", "currency_to"]
        read_only_fields = fields


class ExchangeRateUpdateSerializer(serializers.Serializer):
    """
    # PBI-BE-M4-12: PUT /exchange-rate (Admin)
    Serializer for updating exchange rate.
    """
    rate = serializers.DecimalField(max_digits=15, decimal_places=10)

    def validate_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError("Rate must be positive")
        return value


# ============================================================================
# Costing Serializers
# ============================================================================

class CostingListSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M4-01: GET /costings
    Serializer for listing costings.
    """
    product_name = serializers.CharField(source="product.name_local", read_only=True)
    business_name = serializers.CharField(
        source="product.business.company_name", read_only=True
    )

    class Meta:
        model = Costing
        fields = [
            "id",
            "product",
            "product_name",
            "business_name",
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
            "recommended_exw_price",
            "recommended_fob_price",
            "recommended_cif_price",
            "container_20ft_capacity",
            "target_country_code",
            "created_at",
            "updated_at",
        ]


class CostingDetailSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M4-02: GET /costings/:id
    Serializer for costing detail.
    """
    product_name = serializers.CharField(source="product.name_local", read_only=True)
    product_dimensions = serializers.JSONField(
        source="product.dimensions_l_w_h", read_only=True
    )
    product_weight = serializers.DecimalField(
        source="product.weight_gross", max_digits=10, decimal_places=3, read_only=True
    )
    business_name = serializers.CharField(
        source="product.business.company_name", read_only=True
    )
    business_address = serializers.CharField(
        source="product.business.address", read_only=True
    )

    class Meta:
        model = Costing
        fields = [
            "id",
            "product",
            "product_name",
            "product_dimensions",
            "product_weight",
            "business_name",
            "business_address",
            # Input fields
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
            # Calculated prices
            "recommended_exw_price",
            "recommended_fob_price",
            "recommended_cif_price",
            # Cost breakdown
            "trucking_cost_usd",
            "document_cost_usd",
            "freight_cost_usd",
            "insurance_cost_usd",
            # Container optimization
            "container_20ft_capacity",
            "container_40ft_capacity",
            "optimization_notes",
            # Metadata
            "exchange_rate_used",
            "target_country_code",
            "created_at",
            "updated_at",
        ]


class CostingCreateSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M4-03: POST /costings
    Serializer for creating costing.

    Acceptance Criteria:
    - Body: product_id, cogs_per_unit, packing_cost, target_margin_percent
    - Validate: product belongs to user
    - Validate: all values are positive
    - Trigger AI Price Calculation
    - Trigger AI Container Optimizer
    """
    target_country_code = serializers.CharField(
        max_length=2, required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Costing
        fields = [
            "product",
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
            "target_country_code",
        ]

    def validate_product(self, value):
        """Validate product belongs to user."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            # Admin can create for any product
            if user.role == "Admin":
                return value
            # UMKM can only create for their products
            if not hasattr(user, "business_profile"):
                raise serializers.ValidationError(
                    "You must have a business profile to create costing"
                )
            if value.business != user.business_profile:
                raise serializers.ValidationError(
                    "You can only create costing for your own products"
                )
        return value

    def validate_cogs_per_unit(self, value):
        if value <= 0:
            raise serializers.ValidationError("COGS must be positive")
        return value

    def validate_packing_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Packing cost cannot be negative")
        return value

    def validate_target_margin_percent(self, value):
        if value < 0:
            raise serializers.ValidationError("Target margin cannot be negative")
        if value > 500:
            raise serializers.ValidationError("Target margin seems too high (max 500%)")
        return value


class CostingUpdateSerializer(serializers.ModelSerializer):
    """
    # PBI-BE-M4-04: PUT /costings/:id
    Serializer for updating costing.
    """
    target_country_code = serializers.CharField(
        max_length=2, required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Costing
        fields = [
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
            "target_country_code",
        ]

    def validate_cogs_per_unit(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("COGS must be positive")
        return value

    def validate_packing_cost(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Packing cost cannot be negative")
        return value

    def validate_target_margin_percent(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Target margin cannot be negative")
            if value > 500:
                raise serializers.ValidationError("Target margin seems too high (max 500%)")
        return value
