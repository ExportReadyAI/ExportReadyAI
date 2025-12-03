"""
Authentication Serializers for ExportReady.AI
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, UserRole


class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    
    PBI-BE-M1-01:
    - Accepts: email, password, full_name
    - Validates: email format, email uniqueness, password min 8 chars
    - Password hashed using bcrypt before saving
    - Default role = "UMKM"
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Please enter a valid email address",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        error_messages={
            "required": "Password is required",
            "min_length": "Password must be at least 8 characters",
        },
    )
    full_name = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Full name is required",
            "max_length": "Full name must be less than 255 characters",
        },
    )

    def validate_email(self, value):
        """Check if email is already registered."""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("This email is already registered")
        return email

    def validate_password(self, value):
        """Validate password strength."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Create a new user with UMKM role."""
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            role=UserRole.UMKM,
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    PBI-BE-M1-02:
    - Accepts: email, password
    - Validates credentials with database
    - Compares password with bcrypt
    - Generates JWT token if valid
    - Token contains: user_id, email, role, exp
    """

    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Please enter a valid email address",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "Password is required",
        },
    )

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password", "")

        # Authenticate user
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                {"detail": "Invalid email or password"}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "User account is disabled"}
            )

        attrs["user"] = user
        return attrs

    def get_tokens(self, user):
        """Generate JWT tokens for user."""
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["user_id"] = user.id

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class UserResponseSerializer(serializers.Serializer):
    """
    Serializer for user data in responses (without password).
    """

    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()


class RegisterResponseSerializer(serializers.Serializer):
    """
    Serializer for registration response.
    """

    user = UserResponseSerializer()


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for login response.
    """

    user = UserResponseSerializer()
    tokens = serializers.DictField(
        child=serializers.CharField(),
        help_text="JWT access and refresh tokens",
    )


class MeResponseSerializer(serializers.Serializer):
    """
    Serializer for /auth/me response.
    """

    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
    has_business_profile = serializers.BooleanField()

