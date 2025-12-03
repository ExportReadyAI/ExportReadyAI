"""
BusinessProfile Serializers for ExportReady.AI
"""

from datetime import datetime

from rest_framework import serializers

from .models import BusinessProfile, CertificationType


class BusinessProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for BusinessProfile model.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = BusinessProfile
        fields = [
            "id",
            "user_id",
            "user_email",
            "user_full_name",
            "company_name",
            "address",
            "production_capacity_per_month",
            "certifications",
            "year_established",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "user_email", "user_full_name", "created_at", "updated_at"]


class CreateBusinessProfileSerializer(serializers.Serializer):
    """
    Serializer for creating a new BusinessProfile.
    
    PBI-BE-M1-04:
    - Accepts: company_name, address, production_capacity_per_month, year_established
    - Validates: all fields required, year_established <= current year
    - Auto-assign user_id from token
    - Default certifications = []
    """

    company_name = serializers.CharField(
        max_length=255,
        required=True,
        error_messages={
            "required": "Company name is required",
            "max_length": "Company name must be less than 255 characters",
        },
    )
    address = serializers.CharField(
        required=True,
        error_messages={
            "required": "Address is required",
        },
    )
    production_capacity_per_month = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "Production capacity per month is required",
            "min_value": "Production capacity must be at least 1",
        },
    )
    year_established = serializers.IntegerField(
        required=True,
        min_value=1900,
        error_messages={
            "required": "Year established is required",
            "min_value": "Year established must be 1900 or later",
        },
    )

    def validate_year_established(self, value):
        """Ensure year_established is not in the future."""
        current_year = datetime.now().year
        if value > current_year:
            raise serializers.ValidationError(
                f"Year established cannot be in the future (current year: {current_year})"
            )
        return value

    def create(self, validated_data):
        """Create a new BusinessProfile."""
        user = self.context["request"].user
        return BusinessProfile.objects.create(
            user=user,
            certifications=[],  # Default empty array
            **validated_data,
        )


class UpdateBusinessProfileSerializer(serializers.Serializer):
    """
    Serializer for updating a BusinessProfile.
    
    PBI-BE-M1-06:
    - Accepts: company_name, address, production_capacity_per_month, year_established
    - Update only fields that are sent
    """

    company_name = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(required=False)
    production_capacity_per_month = serializers.IntegerField(min_value=1, required=False)
    year_established = serializers.IntegerField(min_value=1900, required=False)

    def validate_year_established(self, value):
        """Ensure year_established is not in the future."""
        if value is not None:
            current_year = datetime.now().year
            if value > current_year:
                raise serializers.ValidationError(
                    f"Year established cannot be in the future (current year: {current_year})"
                )
        return value

    def update(self, instance, validated_data):
        """Update BusinessProfile with only provided fields."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class UpdateCertificationsSerializer(serializers.Serializer):
    """
    Serializer for updating certifications.
    
    PBI-BE-M1-07:
    - Accepts: certifications (array of strings)
    - Validates: values only ["Halal", "ISO", "HACCP", "SVLK"]
    - Replace entire array
    """

    certifications = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=True,
        error_messages={
            "required": "Certifications field is required",
        },
    )

    def validate_certifications(self, value):
        """Validate that all certifications are valid."""
        valid_certifications = [c.value for c in CertificationType]
        invalid = [cert for cert in value if cert not in valid_certifications]
        
        if invalid:
            raise serializers.ValidationError(
                f"Invalid certifications: {invalid}. "
                f"Valid options are: {valid_certifications}"
            )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_certs = []
        for cert in value:
            if cert not in seen:
                seen.add(cert)
                unique_certs.append(cert)
        
        return unique_certs

    def update(self, instance, validated_data):
        """Update certifications."""
        instance.certifications = validated_data["certifications"]
        instance.save()
        return instance

