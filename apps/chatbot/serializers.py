"""
Serializers for Chatbot API
"""

from rest_framework import serializers

from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at", "metadata"]
        read_only_fields = ["id", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""

    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ["id", "title", "is_active", "created_at", "updated_at", "messages", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sessions."""

    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ["id", "title", "is_active", "created_at", "updated_at", "message_count", "last_message"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                "role": last.role,
                "content": last.content[:100] + "..." if len(last.content) > 100 else last.content,
                "created_at": last.created_at,
            }
        return None


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a chat message."""

    message = serializers.CharField(max_length=5000)
    session_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response."""

    message = serializers.CharField()
    session_id = serializers.IntegerField()
    response_time = serializers.FloatField()
