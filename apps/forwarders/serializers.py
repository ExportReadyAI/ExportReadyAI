"""
Serializers for Module 6B: Forwarders

Includes:
- PBI-BE-M6-16 to M6-22: Forwarder Profile and Review serializers
- PBI-BE-M6-25, M6-26: Recommendation and Statistics serializers
"""

from rest_framework import serializers
from apps.users.models import User

from .models import ForwarderProfile, ForwarderReview


class ForwarderReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for ForwarderReview (READ operations).
    """

    umkm_name = serializers.CharField(source="umkm.full_name", read_only=True)
    umkm_email = serializers.EmailField(source="umkm.email", read_only=True)

    class Meta:
        model = ForwarderReview
        fields = [
            "id",
            "forwarder",
            "umkm",
            "umkm_name",
            "umkm_email",
            "rating",
            "review_text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "forwarder", "umkm", "created_at", "updated_at"]


class ForwarderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for ForwarderProfile (READ operations).
    
    PBI-BE-M6-17, M6-18: GET /forwarders
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()

    class Meta:
        model = ForwarderProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "company_name",
            "contact_info",
            "specialization_routes",
            "service_types",
            "average_rating",
            "total_reviews",
            "recent_reviews",
            "rating_distribution",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "average_rating",
            "total_reviews",
            "created_at",
            "updated_at",
        ]

    def get_recent_reviews(self, obj):
        """Get latest 5 reviews."""
        reviews = obj.reviews.all()[:5]
        return ForwarderReviewSerializer(reviews, many=True).data

    def get_rating_distribution(self, obj):
        """Get rating distribution (5 stars: x%, 4 stars: y%, etc)."""
        from django.db.models import Count
        distribution = (
            ForwarderReview.objects.filter(forwarder=obj)
            .values("rating")
            .annotate(count=Count("id"))
        )
        total = obj.total_reviews
        if total == 0:
            return {str(i): 0 for i in range(1, 6)}
        
        result = {str(i): 0 for i in range(1, 6)}
        for item in distribution:
            result[str(item["rating"])] = round((item["count"] / total) * 100, 1)
        return result


class CreateForwarderProfileSerializer(serializers.Serializer):
    """
    Serializer for creating ForwarderProfile.
    
    PBI-BE-M6-16: POST /forwarder-profile
    """

    company_name = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Company name is required",
        },
    )
    contact_info = serializers.DictField(
        required=True,
        error_messages={
            "required": "Contact info is required",
        },
    )
    specialization_routes = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        error_messages={
            "required": "Specialization routes is required",
        },
    )
    service_types = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        error_messages={
            "required": "Service types is required",
        },
    )

    def validate_specialization_routes(self, value):
        """Validate route format (e.g., 'ID-JP', 'ID-US')."""
        for route in value:
            if not isinstance(route, str) or "-" not in route:
                raise serializers.ValidationError(
                    "Routes must be in format 'ORIGIN-DEST' (e.g., 'ID-JP')"
                )
        return value

    def create(self, validated_data):
        """Create ForwarderProfile with user_id from request."""
        user = self.context["request"].user
        
        # Check if profile already exists
        if hasattr(user, "forwarder_profile"):
            from core.exceptions import ConflictException
            raise ConflictException("Forwarder profile already exists for this user")
        
        return ForwarderProfile.objects.create(
            user=user,
            **validated_data
        )


class UpdateForwarderProfileSerializer(serializers.Serializer):
    """
    Serializer for updating ForwarderProfile.
    
    PBI-BE-M6-19: PUT /forwarder-profile/:id
    """

    company_name = serializers.CharField(required=False, max_length=255)
    contact_info = serializers.DictField(required=False)
    specialization_routes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    service_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    def update(self, instance, validated_data):
        """Update ForwarderProfile fields (exclude rating fields)."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CreateForwarderReviewSerializer(serializers.Serializer):
    """
    Serializer for creating ForwarderReview.
    
    PBI-BE-M6-20: POST /forwarders/:id/reviews
    """

    rating = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=5,
        error_messages={
            "required": "Rating is required",
            "min_value": "Rating must be between 1 and 5",
            "max_value": "Rating must be between 1 and 5",
        },
    )
    review_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def create(self, validated_data):
        """Create ForwarderReview with umkm_id from request."""
        forwarder = self.context["forwarder"]
        umkm = self.context["request"].user
        
        # Check if review already exists
        if ForwarderReview.objects.filter(forwarder=forwarder, umkm=umkm).exists():
            from core.exceptions import ConflictException
            raise ConflictException("You have already reviewed this forwarder")
        
        return ForwarderReview.objects.create(
            forwarder=forwarder,
            umkm=umkm,
            **validated_data
        )


class UpdateForwarderReviewSerializer(serializers.Serializer):
    """
    Serializer for updating ForwarderReview.
    
    PBI-BE-M6-21: PUT /forwarders/:forwarder_id/reviews/:review_id
    """

    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    review_text = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """Update ForwarderReview fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ForwarderRecommendationSerializer(serializers.Serializer):
    """
    Serializer for forwarder recommendations.
    
    PBI-BE-M6-25: GET /forwarders/recommendations
    """

    id = serializers.IntegerField()
    company_name = serializers.CharField()
    contact_info = serializers.DictField()
    specialization_routes = serializers.ListField(child=serializers.CharField())
    service_types = serializers.ListField(child=serializers.CharField())
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=1)
    total_reviews = serializers.IntegerField()


class ForwarderStatisticsSerializer(serializers.Serializer):
    """
    Serializer for forwarder statistics.
    
    PBI-BE-M6-26: GET /forwarders/:id/statistics
    """

    total_reviews = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=1)
    rating_distribution = serializers.DictField()
    total_umkm_partnerships = serializers.IntegerField()
    recent_review_trend = serializers.ListField()

