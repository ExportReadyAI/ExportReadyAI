"""
Authentication Views for ExportReady.AI

Implements:
- PBI-BE-M1-01: POST /auth/register
- PBI-BE-M1-02: POST /auth/login
- PBI-BE-M1-03: GET /auth/me
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers import UserDetailSerializer
from core.exceptions import ConflictException
from core.responses import created_response, error_response, success_response

from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    MeResponseSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    UserResponseSerializer,
)


class RegisterView(APIView):
    """
    API endpoint for user registration.
    
    PBI-BE-M1-01:
    - Accepts: email, password, full_name
    - Validates server-side: email format, email uniqueness, password min 8 chars
    - Password hashed using bcrypt before saving
    - Role default = "UMKM"
    - Response success: 201 Created with user data (without password)
    - Response error: 400 Bad Request with error message
    - Response error: 409 Conflict if email exists
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Register a new user",
        description="Register a new UMKM user account. Email must be unique.",
        request=RegisterSerializer,
        responses={
            201: RegisterResponseSerializer,
            400: {"description": "Validation error"},
            409: {"description": "Email already exists"},
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            
            # Check for email uniqueness error -> return 409
            if "email" in errors:
                for error in errors["email"]:
                    if "already registered" in str(error).lower():
                        return error_response(
                            message="Email already exists",
                            errors=errors,
                            status_code=status.HTTP_409_CONFLICT,
                        )

            return error_response(
                message="Validation failed",
                errors=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        user_data = UserResponseSerializer(user).data

        return created_response(
            data={"user": user_data},
            message="User registered successfully",
        )


class LoginView(APIView):
    """
    API endpoint for user login.
    
    PBI-BE-M1-02:
    - Accepts: email, password
    - Validates credentials with database
    - Compares password with bcrypt
    - Generates JWT token if valid
    - Token contains: user_id, email, role, exp
    - Response success: 200 OK with token and user data
    - Response error: 401 Unauthorized if credentials invalid
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Login user",
        description="Authenticate user and return JWT tokens.",
        request=LoginSerializer,
        responses={
            200: LoginResponseSerializer,
            401: {"description": "Invalid credentials"},
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return error_response(
                message="Invalid email or password",
                errors=serializer.errors,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data["user"]
        tokens = serializer.get_tokens(user)
        user_data = UserResponseSerializer(user).data

        return success_response(
            data={
                "user": user_data,
                "tokens": tokens,
            },
            message="Login successful",
        )


class MeView(APIView):
    """
    API endpoint to get current authenticated user.
    
    PBI-BE-M1-03:
    - Requires Authorization header (Bearer token)
    - Validates and decodes JWT token
    - Response success: 200 OK with user data
    - Response error: 401 Unauthorized if token invalid/expired
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user",
        description="Get the currently authenticated user's information.",
        responses={
            200: MeResponseSerializer,
            401: {"description": "Unauthorized - invalid or expired token"},
        },
        tags=["Authentication"],
    )
    def get(self, request):
        user = request.user
        
        # Check if user has business profile
        has_business_profile = (
            hasattr(user, "business_profile") and user.business_profile is not None
        )

        response_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at,
            "has_business_profile": has_business_profile,
        }

        return success_response(
            data=response_data,
            message="User retrieved successfully",
        )

