"""
User Serializers for ExportReady.AI
"""

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (read operations).
    Excludes sensitive fields like password.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "created_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at"]


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (Admin view).
    """

    has_business_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "created_at",
            "is_active",
            "has_business_profile",
        ]
        read_only_fields = fields

    def get_has_business_profile(self, obj):
        return hasattr(obj, "business_profile") and obj.business_profile is not None


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for User including related data.
    """

    has_business_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "created_at",
            "updated_at",
            "is_active",
            "has_business_profile",
        ]
        read_only_fields = fields

    def get_has_business_profile(self, obj):
        return hasattr(obj, "business_profile") and obj.business_profile is not None

