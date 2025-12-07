"""
Serializers for Module 6A: Buyer Requests

Includes:
- PBI-BE-M6-03 to M6-08: BuyerRequest CRUD serializers
- PBI-BE-M6-13: Matched UMKM serializer
"""

from rest_framework import serializers
from apps.business_profiles.models import BusinessProfile
from apps.users.models import User

from .models import BuyerRequest, BuyerProfile, RequestStatus


class BuyerRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for BuyerRequest (READ operations).
    
    PBI-BE-M6-04, M6-05: GET /buyer-requests
    """

    buyer_company_name = serializers.SerializerMethodField()
    buyer_email = serializers.CharField(source="buyer_user.email", read_only=True)
    buyer_full_name = serializers.CharField(source="buyer_user.full_name", read_only=True)
    selected_catalog_id = serializers.IntegerField(source="selected_catalog.id", read_only=True, allow_null=True)
    selected_catalog_name = serializers.CharField(source="selected_catalog.display_name", read_only=True, allow_null=True)

    class Meta:
        model = BuyerRequest
        fields = [
            "id",
            "buyer_user",
            "buyer_company_name",
            "buyer_email",
            "buyer_full_name",
            "product_category",
            "hs_code_target",
            "spec_requirements",
            "target_volume",
            "destination_country",
            "keyword_tags",
            "min_rank_required",
            "status",
            "selected_catalog_id",
            "selected_catalog_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "buyer_user", "created_at", "updated_at"]

    def get_buyer_company_name(self, obj):
        """Get buyer company name if available."""
        try:
            buyer_profile = obj.buyer_user.buyer_profile
            return buyer_profile.company_name
        except BuyerProfile.DoesNotExist:
            return obj.buyer_user.full_name


class CreateBuyerRequestSerializer(serializers.Serializer):
    """
    Serializer for creating BuyerRequest.
    
    PBI-BE-M6-03: POST /buyer-requests
    """

    product_category = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Product category is required",
        },
    )
    hs_code_target = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=16,
    )
    spec_requirements = serializers.CharField(
        required=True,
        error_messages={
            "required": "Spec requirements is required",
        },
    )
    target_volume = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "Target volume is required",
            "min_value": "Target volume must be at least 1",
        },
    )
    destination_country = serializers.CharField(
        required=True,
        max_length=2,
        error_messages={
            "required": "Destination country is required",
        },
    )
    keyword_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list,
    )
    min_rank_required = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
    )

    def create(self, validated_data):
        """Create BuyerRequest with buyer_user from request."""
        buyer_user = self.context["request"].user
        return BuyerRequest.objects.create(
            buyer_user=buyer_user,
            **validated_data
        )


class UpdateBuyerRequestSerializer(serializers.Serializer):
    """
    Serializer for updating BuyerRequest.
    
    PBI-BE-M6-06: PUT /buyer-requests/:id
    """

    product_category = serializers.CharField(required=False, max_length=255)
    hs_code_target = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=16)
    spec_requirements = serializers.CharField(required=False)
    target_volume = serializers.IntegerField(required=False, min_value=1)
    destination_country = serializers.CharField(required=False, max_length=2)
    keyword_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )
    min_rank_required = serializers.IntegerField(required=False, min_value=0)

    def update(self, instance, validated_data):
        """Update BuyerRequest fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UpdateBuyerRequestStatusSerializer(serializers.Serializer):
    """
    Serializer for updating BuyerRequest status only.
    
    PBI-BE-M6-07: PATCH /buyer-requests/:id/status
    """

    status = serializers.ChoiceField(
        choices=RequestStatus.choices,
        required=True,
        error_messages={
            "required": "Status is required",
            "invalid_choice": "Status must be one of: Open, Matched, Closed",
        },
    )

    def update(self, instance, validated_data):
        """Update BuyerRequest status."""
        instance.status = validated_data["status"]
        instance.save()
        return instance


class SelectCatalogSerializer(serializers.Serializer):
    """
    Serializer for selecting a catalog and closing buyer request.
    """

    catalog_id = serializers.IntegerField(
        required=True,
        help_text="ID of the selected catalog",
        error_messages={"required": "catalog_id is required"},
    )


class MatchedCatalogSerializer(serializers.Serializer):
    """
    Serializer for catalog details in matched results.
    """
    id = serializers.IntegerField()
    display_name = serializers.CharField()
    export_description = serializers.CharField(allow_null=True)
    marketing_description = serializers.CharField(allow_null=True)
    technical_specs = serializers.DictField()
    tags = serializers.ListField(child=serializers.CharField())
    min_order_quantity = serializers.FloatField()
    unit_type = serializers.CharField()
    available_stock = serializers.IntegerField()
    base_price_exw = serializers.FloatField()
    base_price_fob = serializers.FloatField(allow_null=True)
    base_price_cif = serializers.FloatField(allow_null=True)
    lead_time_days = serializers.IntegerField()
    primary_image_url = serializers.URLField(allow_null=True)


class MatchedUMSerializer(serializers.Serializer):
    """
    Serializer for matched UMKM with catalog details in buyer request.
    
    PBI-BE-M6-13: GET /buyer-requests/:id/matched-umkm
    
    Simplified to category-only matching.
    Multiple catalogs per UMKM are returned if they match.
    """

    umkm_id = serializers.IntegerField()
    company_name = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    match = serializers.CharField()
    contact_info = serializers.DictField()
    catalog = MatchedCatalogSerializer()


class BuyerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for BuyerProfile (READ operations).
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    total_requests = serializers.SerializerMethodField()

    class Meta:
        model = BuyerProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "company_name",
            "company_description",
            "contact_info",
            "preferred_product_categories",
            "preferred_product_categories_description",
            "source_countries",
            "source_countries_description",
            "business_type",
            "business_type_description",
            "annual_import_volume",
            "annual_import_volume_description",
            "total_requests",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]

    def get_total_requests(self, obj):
        """Get total number of buyer requests."""
        return obj.user.buyer_requests.count()


class CreateBuyerProfileSerializer(serializers.Serializer):
    """
    Serializer for creating BuyerProfile.
    """

    company_name = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Company name is required",
        },
    )
    company_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed description of the company, its business activities, and market focus",
    )
    contact_info = serializers.DictField(
        required=True,
        error_messages={
            "required": "Contact info is required",
        },
    )
    preferred_product_categories = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        error_messages={
            "required": "Preferred product categories is required",
        },
    )
    preferred_product_categories_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed description of preferred product categories, quality requirements, and specific product interests",
    )
    source_countries = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        error_messages={
            "required": "Source countries is required",
        },
    )
    source_countries_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description of sourcing strategy, preferred countries, and import experience from these regions",
    )
    business_type = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )
    business_type_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed description of business operations, distribution channels, and market reach",
    )
    annual_import_volume = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )
    annual_import_volume_description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Detailed information about import capacity, volume trends, and growth projections",
    )

    def create(self, validated_data):
        """Create BuyerProfile with user_id from request."""
        user = self.context["request"].user
        
        # Check if profile already exists
        if hasattr(user, "buyer_profile"):
            from core.exceptions import ConflictException
            raise ConflictException("Buyer profile already exists for this user")
        
        return BuyerProfile.objects.create(
            user=user,
            **validated_data
        )


class UpdateBuyerProfileSerializer(serializers.Serializer):
    """
    Serializer for updating BuyerProfile.
    """

    company_name = serializers.CharField(required=False, max_length=255)
    company_description = serializers.CharField(required=False, allow_blank=True)
    contact_info = serializers.DictField(required=False)
    preferred_product_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    preferred_product_categories_description = serializers.CharField(required=False, allow_blank=True)
    source_countries = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    source_countries_description = serializers.CharField(required=False, allow_blank=True)
    business_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    business_type_description = serializers.CharField(required=False, allow_blank=True)
    annual_import_volume = serializers.CharField(required=False, allow_blank=True, max_length=100)
    annual_import_volume_description = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Update BuyerProfile fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

