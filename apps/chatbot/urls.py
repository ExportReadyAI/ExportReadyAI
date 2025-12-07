"""
URL Configuration for Chatbot Module

Endpoints:
- POST /chat/send/                  - Send message and get AI response
- GET  /chat/sessions/              - List chat sessions
- POST /chat/sessions/              - Create new session
- GET  /chat/sessions/:id/          - Get session with messages
- DELETE /chat/sessions/:id/        - Delete session
- GET  /chat/suggestions/           - Get suggested questions
"""

from django.urls import path

from .views import (
    ChatSendView,
    ChatSessionListCreateView,
    ChatSessionDetailView,
    ChatSuggestionsView,
)

app_name = "chatbot"

urlpatterns = [
    # Main chat endpoint
    path("send/", ChatSendView.as_view(), name="chat-send"),

    # Session management
    path("sessions/", ChatSessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<int:session_id>/", ChatSessionDetailView.as_view(), name="session-detail"),

    # Suggestions
    path("suggestions/", ChatSuggestionsView.as_view(), name="chat-suggestions"),
]
