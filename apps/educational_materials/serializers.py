"""
Simplified Serializers for Module 7: Educational Materials

Only Modules and Articles (simple CRUD)
"""

from rest_framework import serializers
from django.db.models import Max

from .models import Module, Article


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article (READ operations)."""

    class Meta:
        model = Article
        fields = [
            "id",
            "module",
            "title",
            "content",
            "video_url",
            "file_url",
            "order_index",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "module", "created_at", "updated_at"]


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module (READ operations)."""

    article_count = serializers.IntegerField(read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "order_index",
            "article_count",
            "articles",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CreateModuleSerializer(serializers.Serializer):
    """Serializer for creating Module."""

    title = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    order_index = serializers.IntegerField(required=False, default=0)

    def create(self, validated_data):
        """Create Module with auto-assigned order_index if not provided."""
        if "order_index" not in validated_data or validated_data["order_index"] == 0:
            max_order = Module.objects.aggregate(max_order=Max("order_index"))["max_order"] or 0
            validated_data["order_index"] = max_order + 1

        return Module.objects.create(**validated_data)


class UpdateModuleSerializer(serializers.Serializer):
    """Serializer for updating Module."""

    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    order_index = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        """Update Module fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CreateArticleSerializer(serializers.Serializer):
    """Serializer for creating Article."""

    module_id = serializers.IntegerField(required=True)
    title = serializers.CharField(required=True, max_length=255)
    content = serializers.CharField(required=True)
    video_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    file_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    order_index = serializers.IntegerField(required=False, default=0)

    def validate_module_id(self, value):
        """Validate module_id exists."""
        if not Module.objects.filter(id=value).exists():
            raise serializers.ValidationError("Module does not exist")
        return value

    def create(self, validated_data):
        """Create Article with auto-assigned order_index if not provided."""
        module_id = validated_data.pop("module_id")
        module = Module.objects.get(id=module_id)

        if "order_index" not in validated_data or validated_data["order_index"] == 0:
            max_order = Article.objects.filter(module=module).aggregate(
                max_order=Max("order_index")
            )["max_order"] or 0
            validated_data["order_index"] = max_order + 1

        return Article.objects.create(module=module, **validated_data)


class UpdateArticleSerializer(serializers.Serializer):
    """Serializer for updating Article."""

    title = serializers.CharField(required=False, max_length=255)
    content = serializers.CharField(required=False)
    video_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    file_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, max_length=500)
    order_index = serializers.IntegerField(required=False)

    def update(self, instance, validated_data):
        """Update Article fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
