from rest_framework import serializers

from .models import Product, ProductEnrichment


# PBI-BE-M2-09, M2-10: ProductEnrichment Serializer
# Used for returning enriched product data
class ProductEnrichmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductEnrichment
        fields = [
            "hs_code_recommendation",
            "sku_generated",
            "name_english_b2b",
            "description_english_b2b",
            "marketing_highlights",
            "last_updated_ai",
        ]


# PBI-BE-M2-01, M2-02, M2-03, M2-04, M2-05: Product Serializer
# Main serializer for product CRUD operations
# Auto-assign business_id dari user's BusinessProfile
# Validasi: dimensions dan weight bernilai positif
class ProductSerializer(serializers.ModelSerializer):
    enrichment = ProductEnrichmentSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "business",
            "name_local",
            "category_id",
            "description_local",
            "material_composition",
            "production_technique",
            "finishing_type",
            "quality_specs",
            "durability_claim",
            "packaging_type",
            "dimensions_l_w_h",
            "weight_net",
            "weight_gross",
            "created_at",
            "updated_at",
            "enrichment",
        ]
        read_only_fields = ["id", "business", "created_at", "updated_at", "enrichment"]

    def validate(self, attrs):
        # Basic validation: ensure dimensions JSON has l, w, h when provided
        dims = attrs.get("dimensions_l_w_h") or {}
        if dims:
            for k in ("l", "w", "h"):
                if k not in dims:
                    raise serializers.ValidationError({"dimensions_l_w_h": "Must include l, w, h"})
        return attrs

    def create(self, validated_data):
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
