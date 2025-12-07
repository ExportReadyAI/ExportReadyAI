"""
Chatbot Service for ExportReady.AI

Provides AI-powered chat assistance for UMKM users.
Combines static knowledge base with user's dynamic data.
"""

import logging
import time
from typing import Dict, List, Optional

from django.conf import settings
from openai import OpenAI

from .knowledge import EXPORT_KNOWLEDGE, EXPORT_QUICK_CONTEXT, get_user_context
from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    AI Chatbot service for UMKM export assistance.
    """

    def __init__(self):
        api_key = settings.KOLOSAL_API_KEY
        if not api_key or api_key.strip() == "":
            logger.error("KOLOSAL_API_KEY is not set!")
            raise ValueError("KOLOSAL_API_KEY is required")

        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url=settings.KOLOSAL_BASE_URL,
        )
        self.model = settings.KOLOSAL_MODEL
        logger.info(f"ChatbotService initialized - Model: {self.model}")

    def _build_system_prompt(self, user, include_full_knowledge: bool = True) -> str:
        """
        Build system prompt with knowledge base and user context.
        """
        parts = [EXPORT_QUICK_CONTEXT]

        # Add user's dynamic context
        user_context = get_user_context(user)
        if user_context:
            parts.append(user_context)

        # Add full knowledge for comprehensive answers
        if include_full_knowledge:
            parts.append("\n# Knowledge Base:")
            parts.append(EXPORT_KNOWLEDGE)

        parts.append("""
# Instruksi Respons:
1. Jawab dengan jelas dan praktis
2. Jika user punya produk, berikan saran spesifik berdasarkan data mereka
3. Jika tidak yakin, minta klarifikasi
4. Gunakan contoh konkret jika membantu
5. Untuk perhitungan harga, jelaskan komponen-komponennya
6. Sebutkan sertifikasi yang relevan untuk produk user
""")

        return "\n".join(parts)

    def chat(
        self,
        user,
        message: str,
        session: Optional[ChatSession] = None,
        include_history: bool = True,
    ) -> Dict:
        """
        Process a chat message and return AI response.

        Args:
            user: The authenticated user
            message: User's message
            session: Optional chat session for conversation history
            include_history: Whether to include conversation history

        Returns:
            Dict with response data
        """
        start_time = time.time()

        try:
            # Build messages array
            messages = []

            # System prompt with knowledge + user context
            system_prompt = self._build_system_prompt(user)
            messages.append({"role": "system", "content": system_prompt})

            # Add conversation history if available
            if session and include_history:
                history = session.get_messages_for_context(limit=10)
                messages.extend(history)

            # Add current user message
            messages.append({"role": "user", "content": message})

            # Call AI API
            logger.info(f"Calling chatbot AI for user {user.id}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Slightly higher for more natural conversation
                max_tokens=1500,
            )

            assistant_message = response.choices[0].message.content.strip()
            elapsed_time = time.time() - start_time

            # Save messages to session if provided
            if session:
                # Save user message
                ChatMessage.objects.create(
                    session=session,
                    role="user",
                    content=message,
                )
                # Save assistant response
                ChatMessage.objects.create(
                    session=session,
                    role="assistant",
                    content=assistant_message,
                    metadata={
                        "response_time": elapsed_time,
                        "model": self.model,
                        "tokens_used": getattr(response.usage, 'total_tokens', None),
                    }
                )
                # Update session title if it's the first message
                if not session.title and session.messages.count() <= 2:
                    # Auto-generate title from first message
                    title = message[:50] + "..." if len(message) > 50 else message
                    session.title = title
                    session.save(update_fields=["title"])

            return {
                "success": True,
                "data": {
                    "message": assistant_message,
                    "session_id": session.id if session else None,
                    "response_time": round(elapsed_time, 2),
                }
            }

        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def create_session(self, user, title: str = "") -> ChatSession:
        """
        Create a new chat session for user.
        """
        return ChatSession.objects.create(
            user=user,
            title=title,
        )

    def get_or_create_session(self, user, session_id: Optional[int] = None) -> ChatSession:
        """
        Get existing session or create new one.
        """
        if session_id:
            try:
                return ChatSession.objects.get(id=session_id, user=user, is_active=True)
            except ChatSession.DoesNotExist:
                pass

        # Return most recent active session or create new
        recent = ChatSession.objects.filter(user=user, is_active=True).first()
        if recent:
            return recent

        return self.create_session(user)

    def get_suggested_questions(self, user) -> List[str]:
        """
        Get suggested questions based on user's data.
        """
        from apps.business_profiles.models import BusinessProfile
        from apps.products.models import Product

        suggestions = [
            "Apa saja dokumen yang diperlukan untuk ekspor?",
            "Bagaimana cara menghitung harga ekspor FOB?",
            "Negara mana yang cocok untuk produk saya?",
        ]

        try:
            profile = BusinessProfile.objects.get(user=user)
            products = Product.objects.filter(business=profile)

            if products.exists():
                first_product = products.first()
                suggestions.insert(0, f"Sertifikasi apa yang diperlukan untuk ekspor {first_product.name_local}?")
                suggestions.insert(1, f"Berapa estimasi biaya kirim {first_product.name_local} ke Singapura?")

            if not profile.certifications:
                suggestions.insert(0, "Bagaimana cara mendapatkan sertifikat Halal?")

        except BusinessProfile.DoesNotExist:
            suggestions.insert(0, "Bagaimana cara memulai ekspor untuk UMKM?")

        return suggestions[:5]


# Singleton instance
_chatbot_service = None


def get_chatbot_service() -> ChatbotService:
    """Get or create ChatbotService singleton."""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
