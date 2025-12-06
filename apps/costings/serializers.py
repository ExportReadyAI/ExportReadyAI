"""
Serializers for Module 4: Costing & Pricing

Includes:
- PBI-BE-M4-03, PBI-BE-M4-04, PBI-BE-M4-11, PBI-BE-M4-12
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Costing, ExchangeRate


class CostingSerializer(serializers.ModelSerializer):
    """
    PBI-BE-M4-01, PBI-BE-M4-02, PBI-BE-M4-03, PBI-BE-M4-04
    
    Serializer untuk Costing dengan validasi input costs dan AI-calculated prices
    """
    
    product_name = serializers.CharField(source="product.name_local", read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    target_country_code = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_null=True,
        help_text="2-letter country code (e.g., US, JP, SG) for CIF calculation. Optional."
    )
    
    class Meta:
        model = Costing
        fields = (
            "id",
            "product_id",
            "product_name",
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
            "target_country_code",
            "recommended_exw_price",
            "recommended_fob_price",
            "recommended_cif_price",
            "container_20ft_capacity",
            "optimization_notes",
            "calculated_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "recommended_exw_price",
            "recommended_fob_price",
            "recommended_cif_price",
            "container_20ft_capacity",
            "optimization_notes",
            "calculated_at",
            "created_at",
            "updated_at",
        )
    
    def validate_cogs_per_unit(self, value):
        """Validasi COGS harus positif"""
        if value <= 0:
            raise serializers.ValidationError("COGS per unit must be greater than 0")
        return value
    
    def validate_packing_cost(self, value):
        """Validasi packing cost harus positif"""
        if value <= 0:
            raise serializers.ValidationError("Packing cost must be greater than 0")
        return value
    
    def validate_target_margin_percent(self, value):
        """Validasi margin harus antara 0-100%"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Margin must be between 0 and 100%")
        return value
    
    def create(self, validated_data):
        """
        Custom create method to handle write-only fields like target_country_code.
        These fields are removed from validated_data before model creation.
        """
        # Remove write-only fields that don't exist in the model
        validated_data.pop('target_country_code', None)
        validated_data.pop('product_id', None)
        
        # Create instance with remaining validated data
        return super().create(validated_data)


class UpdateCostingSerializer(serializers.ModelSerializer):
    """
    PBI-BE-M4-04: Serializer untuk update costing inputs saja
    """
    
    class Meta:
        model = Costing
        fields = (
            "cogs_per_unit",
            "packing_cost",
            "target_margin_percent",
        )
    
    def validate_cogs_per_unit(self, value):
        if value <= 0:
            raise serializers.ValidationError("COGS per unit must be greater than 0")
        return value
    
    def validate_packing_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError("Packing cost must be greater than 0")
        return value
    
    def validate_target_margin_percent(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Margin must be between 0 and 100%")
        return value


class ExchangeRateSerializer(serializers.ModelSerializer):
    """
    PBI-BE-M4-10, PBI-BE-M4-11, PBI-BE-M4-12
    
    Serializer untuk exchange rate IDR-USD
    """
    
    class Meta:
        model = ExchangeRate
        fields = (
            "id",
            "rate",
            "source",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "updated_at",
        )
    
    def validate_rate(self, value):
        """Validasi rate harus positif"""
        if value <= 0:
            raise serializers.ValidationError("Exchange rate must be greater than 0")
        return value
