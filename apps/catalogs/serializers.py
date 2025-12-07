"""
Serializers for Product Catalog Module

Implements CRUD serializers for:
- ProductCatalog
- ProductCatalogImage
- CatalogVariantType & CatalogVariantOption
"""

from rest_framework import serializers
from .models import ProductCatalog, ProductCatalogImage, CatalogVariantType, CatalogVariantOption


class CatalogImageSerializer(serializers.ModelSerializer):
    """Serializer for catalog images - supports both file upload and URL"""

    # Read-only field that returns the final URL (from uploaded file or external URL)
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductCatalogImage
        fields = (
            "id",
            "image",
            "image_url",
            "url",
            "alt_text",
            "sort_order",
            "is_primary",
            "created_at",
        )
        read_only_fields = ("id", "url", "created_at")

    def get_url(self, obj):
        """Return the image URL - either from uploaded file or external URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return obj.image_url


class CatalogVariantOptionSerializer(serializers.ModelSerializer):
    """Serializer for variant options (e.g., Merah, Biru for Color)"""

    class Meta:
        model = CatalogVariantOption
        fields = (
            "id",
            "option_name",
            "sort_order",
            "is_available",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class CatalogVariantTypeSerializer(serializers.ModelSerializer):
    """Serializer for variant types with nested options"""

    options = CatalogVariantOptionSerializer(many=True, read_only=True)

    class Meta:
        model = CatalogVariantType
        fields = (
            "id",
            "type_code",
            "type_name",
            "sort_order",
            "options",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    @staticmethod
    def get_predefined_types():
        """Return list of predefined variant types for dropdown"""
        return [
            {"code": code, "label": label}
            for code, label in CatalogVariantType.VARIANT_TYPE_CHOICES
        ]


class ProductCatalogSerializer(serializers.ModelSerializer):
    """
    Full serializer for ProductCatalog with nested images and variant_types.
    Used for detail views.
    """

    images = CatalogImageSerializer(many=True, read_only=True)
    variant_types = CatalogVariantTypeSerializer(many=True, read_only=True)
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
            "export_description",
            "technical_specs",
            "safety_info",
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
            "variant_types",
        )
        read_only_fields = ("id", "published_at", "created_at", "updated_at")


class ProductCatalogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for catalog list views.
    Excludes nested relations for performance.
    """

    product_name = serializers.CharField(source="product.name_local", read_only=True)
    primary_image = serializers.SerializerMethodField()
    variant_type_count = serializers.SerializerMethodField()
    has_ai_description = serializers.SerializerMethodField()

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
            "variant_type_count",
            "has_ai_description",
            "updated_at",
        )

    def get_primary_image(self, obj):
        """Get the primary image URL (from uploaded file or external URL)"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.url  # Uses the model's url property
        first = obj.images.first()
        return first.url if first else None

    def get_variant_type_count(self, obj):
        """Get count of variant types"""
        return obj.variant_types.count()

    def get_has_ai_description(self, obj):
        """Check if catalog has AI-generated description"""
        return bool(obj.export_description and obj.export_description.strip())


class VariantOptionInputSerializer(serializers.Serializer):
    """Serializer for variant option input when creating catalog"""
    option_name = serializers.CharField(max_length=100)
    sort_order = serializers.IntegerField(default=0, required=False)
    is_available = serializers.BooleanField(default=True, required=False)


class VariantTypeInputSerializer(serializers.Serializer):
    """Serializer for variant type input when creating catalog"""
    type_code = serializers.ChoiceField(
        choices=CatalogVariantType.VARIANT_TYPE_CHOICES,
        default="custom"
    )
    type_name = serializers.CharField(max_length=100)
    sort_order = serializers.IntegerField(default=0, required=False)
    options = VariantOptionInputSerializer(many=True, required=False)


class ProductCatalogCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new catalog entry.
    """

    product_id = serializers.IntegerField(write_only=True)
    images = CatalogImageSerializer(many=True, required=False)
    variant_types = VariantTypeInputSerializer(many=True, required=False)

    class Meta:
        model = ProductCatalog
        fields = (
            "product_id",
            "is_published",
            "display_name",
            "marketing_description",
            "export_description",
            "technical_specs",
            "safety_info",
            "min_order_quantity",
            "unit_type",
            "base_price_exw",
            "base_price_fob",
            "base_price_cif",
            "lead_time_days",
            "available_stock",
            "tags",
            "images",
            "variant_types",
        )

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        variant_types_data = validated_data.pop("variant_types", [])
        product_id = validated_data.pop("product_id")

        # Create catalog
        catalog = ProductCatalog.objects.create(
            product_id=product_id,
            **validated_data
        )

        # Create images
        for image_data in images_data:
            ProductCatalogImage.objects.create(catalog=catalog, **image_data)

        # Create variant types and options
        for vt_data in variant_types_data:
            options_data = vt_data.pop("options", [])
            variant_type = CatalogVariantType.objects.create(
                catalog=catalog,
                **vt_data
            )
            for opt_data in options_data:
                CatalogVariantOption.objects.create(
                    variant_type=variant_type,
                    **opt_data
                )

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
            "export_description",
            "technical_specs",
            "safety_info",
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
            "export_description": {"required": False},
            "technical_specs": {"required": False},
            "safety_info": {"required": False},
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
    """
    Serializer for adding images to a catalog.
    Supports both file upload (image) and external URL (image_url).
    At least one of image or image_url must be provided.
    """

    catalog_id = serializers.IntegerField(write_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = ProductCatalogImage
        fields = (
            "catalog_id",
            "image",
            "image_url",
            "alt_text",
            "sort_order",
            "is_primary",
        )

    def validate(self, attrs):
        """Ensure at least one of image or image_url is provided"""
        image = attrs.get("image")
        image_url = attrs.get("image_url")

        if not image and not image_url:
            raise serializers.ValidationError(
                "Either 'image' (file upload) or 'image_url' must be provided."
            )

        return attrs

    def create(self, validated_data):
        catalog_id = validated_data.pop("catalog_id")
        return ProductCatalogImage.objects.create(
            catalog_id=catalog_id,
            **validated_data
        )


class CatalogVariantTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding variant types to a catalog"""

    catalog_id = serializers.IntegerField(write_only=True)
    options = VariantOptionInputSerializer(many=True, required=False)

    class Meta:
        model = CatalogVariantType
        fields = (
            "catalog_id",
            "type_code",
            "type_name",
            "sort_order",
            "options",
        )

    def create(self, validated_data):
        catalog_id = validated_data.pop("catalog_id")
        options_data = validated_data.pop("options", [])

        variant_type = CatalogVariantType.objects.create(
            catalog_id=catalog_id,
            **validated_data
        )

        for opt_data in options_data:
            CatalogVariantOption.objects.create(
                variant_type=variant_type,
                **opt_data
            )

        return variant_type


class CatalogVariantOptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding options to a variant type"""

    variant_type_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CatalogVariantOption
        fields = (
            "variant_type_id",
            "option_name",
            "sort_order",
            "is_available",
        )

    def create(self, validated_data):
        variant_type_id = validated_data.pop("variant_type_id")
        return CatalogVariantOption.objects.create(
            variant_type_id=variant_type_id,
            **validated_data
        )


class PublicCatalogSerializer(serializers.ModelSerializer):
    """
    Public serializer for buyer-facing catalog views.
    Only shows published catalogs with relevant info.
    """

    images = CatalogImageSerializer(many=True, read_only=True)
    variant_types = CatalogVariantTypeSerializer(many=True, read_only=True)
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
            "export_description",
            "technical_specs",
            "safety_info",
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
            "variant_types",
            "published_at",
        )
