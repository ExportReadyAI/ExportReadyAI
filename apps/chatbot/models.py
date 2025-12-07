"""
Chatbot Models for ExportReady.AI

Models:
- ChatSession: Represents a chat conversation session
- ChatMessage: Individual messages within a session
"""

from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """
    Chat session/conversation untuk user.
    Setiap session menyimpan context dan history.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self):
        return f"Chat {self.id} - {self.user.email}"

    def get_messages_for_context(self, limit=10):
        """
        Get recent messages for AI context.
        Returns list of dicts with role and content.
        """
        messages = self.messages.order_by("-created_at")[:limit]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]


class ChatMessage(models.Model):
    """
    Individual chat message.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: store metadata (tokens used, response time, etc.)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
