"""
Serializers for Product Catalog Module

Implements CRUD serializers for:
- ProductCatalog
- ProductCatalogImage
- CatalogVariant
"""

from rest_framework import serializers
from .models import ProductCatalog, ProductCatalogImage, CatalogVariant


class CatalogImageSerializer(serializers.ModelSerializer):
    """Serializer for catalog images"""

    class Meta:
        model = ProductCatalogImage
        fields = (
            "id",
            "image_url",
            "alt_text",
            "sort_order",
            "is_primary",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class CatalogVariantSerializer(serializers.ModelSerializer):
    """Serializer for catalog variants"""

    class Meta:
        model = CatalogVariant
        fields = (
            "id",
            "variant_name",
            "attributes",
            "variant_price",
            "moq_variant",
            "sku",
            "is_available",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductCatalogSerializer(serializers.ModelSerializer):
    """
    Full serializer for ProductCatalog with nested images and variants.
    Used for detail views.
    """

    images = CatalogImageSerializer(many=True, read_only=True)
    variants = CatalogVariantSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="product.name_local", read_only=True)
    product_hs_code = serializers.CharField(
        source="product.enrichment.hs_code_recommendation",
        read_only=True,
        default=None
    )

    class Meta:
        model = ProductCatalog
        fields = (
            "id",
            "product",
            "product_name",
            "product_hs_code",
            "is_published",
            "display_name",
            "marketing_description",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "base_price_cif",
            "lead_time_days",
            "available_stock",
            "tags",
            "published_at",
            "created_at",
            "updated_at",
            "images",
            "variants",
        )
        read_only_fields = ("id", "published_at", "created_at", "updated_at")


class ProductCatalogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for catalog list views.
    Excludes nested relations for performance.
    """

    product_name = serializers.CharField(source="product.name_local", read_only=True)
    primary_image = serializers.SerializerMethodField()
    variant_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCatalog
        fields = (
            "id",
            "product",
            "product_name",
            "is_published",
            "display_name",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "lead_time_days",
            "available_stock",
            "tags",
            "primary_image",
            "variant_count",
            "updated_at",
        )

    def get_primary_image(self, obj):
        """Get the primary image URL"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image_url
        first = obj.images.first()
        return first.image_url if first else None

    def get_variant_count(self, obj):
        """Get count of variants"""
        return obj.variants.count()


class ProductCatalogCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new catalog entry.
    """

    product_id = serializers.IntegerField(write_only=True)
    images = CatalogImageSerializer(many=True, required=False)
    variants = CatalogVariantSerializer(many=True, required=False)

    class Meta:
        model = ProductCatalog
        fields = (
            "product_id",
            "is_published",
            "display_name",
            "marketing_description",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "base_price_cif",
            "lead_time_days",
            "available_stock",
            "tags",
            "images",
            "variants",
        )

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        variants_data = validated_data.pop("variants", [])
        product_id = validated_data.pop("product_id")

        # Create catalog
        catalog = ProductCatalog.objects.create(
            product_id=product_id,
            **validated_data
        )

        # Create images
        for image_data in images_data:
            ProductCatalogImage.objects.create(catalog=catalog, **image_data)

        # Create variants
        for variant_data in variants_data:
            CatalogVariant.objects.create(catalog=catalog, **variant_data)

        return catalog


class ProductCatalogUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating catalog entries.
    All fields optional for partial updates.
    """

    class Meta:
        model = ProductCatalog
        fields = (
            "is_published",
            "display_name",
            "marketing_description",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "base_price_cif",
            "lead_time_days",
            "available_stock",
            "tags",
        )
        extra_kwargs = {
            "is_published": {"required": False},
            "display_name": {"required": False},
            "marketing_description": {"required": False},
            "min_order_quantity": {"required": False},
            "unit_type": {"required": False},
            "base_price_exw": {"required": False},
            "base_price_fob": {"required": False},
            "base_price_cif": {"required": False},
            "lead_time_days": {"required": False},
            "available_stock": {"required": False},
            "tags": {"required": False},
        }


class CatalogImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding images to a catalog"""

    catalog_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProductCatalogImage
        fields = (
            "catalog_id",
            "image_url",
            "alt_text",
            "sort_order",
            "is_primary",
        )

    def create(self, validated_data):
        catalog_id = validated_data.pop("catalog_id")
        return ProductCatalogImage.objects.create(
            catalog_id=catalog_id,
            **validated_data
        )


class CatalogVariantCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding variants to a catalog"""

    catalog_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CatalogVariant
        fields = (
            "catalog_id",
            "variant_name",
            "attributes",
            "variant_price",
            "moq_variant",
            "sku",
            "is_available",
        )

    def create(self, validated_data):
        catalog_id = validated_data.pop("catalog_id")
        return CatalogVariant.objects.create(
            catalog_id=catalog_id,
            **validated_data
        )


class PublicCatalogSerializer(serializers.ModelSerializer):
    """
    Public serializer for buyer-facing catalog views.
    Only shows published catalogs with relevant info.
    """

    images = CatalogImageSerializer(many=True, read_only=True)
    variants = CatalogVariantSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(
        source="product.business.company_name",
        read_only=True
    )

    class Meta:
        model = ProductCatalog
        fields = (
            "id",
            "display_name",
            "marketing_description",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "base_price_cif",
            "lead_time_days",
            "available_stock",
            "tags",
            "seller_name",
            "images",
            "variants",
            "published_at",
        )
