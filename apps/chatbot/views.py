"""
Chatbot API Views for ExportReady.AI

Endpoints:
- POST /chat/send/ - Send a message and get AI response
- GET /chat/sessions/ - List user's chat sessions
- GET /chat/sessions/:id/ - Get session with messages
- POST /chat/sessions/ - Create new session
- DELETE /chat/sessions/:id/ - Delete session
- GET /chat/suggestions/ - Get suggested questions
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.permissions import IsUMKM
from core.responses import success_response, error_response, created_response

from .models import ChatSession
from .serializers import (
    ChatSessionSerializer,
    ChatSessionListSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)
from .services import get_chatbot_service


class ChatSendView(APIView):
    """
    Send a message to the chatbot and get AI response.
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    @extend_schema(
        summary="Send chat message",
        description="""
        Send a message to the AI chatbot and receive a response.
        Optionally include session_id to continue a conversation.
        If no session_id, a new session will be created.
        """,
        request=SendMessageSerializer,
        responses={200: {"description": "AI response"}},
        tags=["Chatbot"],
    )
    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        message = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id")

        try:
            chatbot = get_chatbot_service()

            # Get or create session
            session = chatbot.get_or_create_session(request.user, session_id)

            # Process message
            result = chatbot.chat(
                user=request.user,
                message=message,
                session=session,
            )

            if result["success"]:
                return success_response(
                    data=result["data"],
                    message="Message processed successfully",
                )
            else:
                return error_response(
                    message="Failed to process message",
                    errors={"detail": result.get("error", "Unknown error")},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return error_response(
                message="Chatbot service error",
                errors={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatSessionListCreateView(APIView):
    """
    List or create chat sessions.
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    @extend_schema(
        summary="List chat sessions",
        description="Get all chat sessions for the current user.",
        responses={200: ChatSessionListSerializer(many=True)},
        tags=["Chatbot"],
    )
    def get(self, request):
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True,
        ).order_by("-updated_at")

        serializer = ChatSessionListSerializer(sessions, many=True)
        return success_response(
            data=serializer.data,
            message="Chat sessions retrieved successfully",
        )

    @extend_schema(
        summary="Create new chat session",
        description="Create a new chat session.",
        request={"type": "object", "properties": {"title": {"type": "string"}}},
        responses={201: ChatSessionSerializer},
        tags=["Chatbot"],
    )
    def post(self, request):
        title = request.data.get("title", "")

        chatbot = get_chatbot_service()
        session = chatbot.create_session(request.user, title)

        serializer = ChatSessionSerializer(session)
        return created_response(
            data=serializer.data,
            message="Chat session created successfully",
        )


class ChatSessionDetailView(APIView):
    """
    Get or delete a specific chat session.
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    def get_object(self, session_id, user):
        """Get session and verify ownership."""
        try:
            return ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return None

    @extend_schema(
        summary="Get chat session details",
        description="Get a chat session with all messages.",
        responses={200: ChatSessionSerializer},
        tags=["Chatbot"],
    )
    def get(self, request, session_id):
        session = self.get_object(session_id, request.user)
        if not session:
            return error_response(
                message="Chat session not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = ChatSessionSerializer(session)
        return success_response(
            data=serializer.data,
            message="Chat session retrieved successfully",
        )

    @extend_schema(
        summary="Delete chat session",
        description="Soft delete a chat session (marks as inactive).",
        responses={200: {"description": "Session deleted"}},
        tags=["Chatbot"],
    )
    def delete(self, request, session_id):
        session = self.get_object(session_id, request.user)
        if not session:
            return error_response(
                message="Chat session not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Soft delete
        session.is_active = False
        session.save(update_fields=["is_active"])

        return success_response(
            data={"id": session_id},
            message="Chat session deleted successfully",
        )


class ChatSuggestionsView(APIView):
    """
    Get suggested questions based on user's data.
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    @extend_schema(
        summary="Get suggested questions",
        description="Get AI-suggested questions based on user's products and profile.",
        responses={200: {"description": "List of suggested questions"}},
        tags=["Chatbot"],
    )
    def get(self, request):
        chatbot = get_chatbot_service()
        suggestions = chatbot.get_suggested_questions(request.user)

        return success_response(
            data={"suggestions": suggestions},
            message="Suggestions retrieved successfully",
        )
