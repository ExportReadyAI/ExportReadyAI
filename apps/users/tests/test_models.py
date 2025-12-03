"""
Tests for User Model
"""

import pytest
from django.contrib.auth import get_user_model

from apps.users.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.UMKM  # Default role
        assert user.is_active is True
        assert user.is_staff is False
        assert user.check_password("testpass123")

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            full_name="Admin User",
        )
        assert admin.email == "admin@example.com"
        assert admin.role == UserRole.ADMIN
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_email_normalized(self):
        """Test email is normalized to lowercase."""
        user = User.objects.create_user(
            email="TEST@EXAMPLE.COM",
            password="testpass123",
            full_name="Test User",
        )
        assert user.email == "test@example.com"

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            full_name="Test User",
        )
        assert str(user) == "test@example.com"

    def test_is_admin_property(self):
        """Test is_admin property."""
        admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        umkm = User.objects.create_user(
            email="umkm@example.com",
            password="testpass123",
            full_name="UMKM User",
            role=UserRole.UMKM,
        )
        assert admin.is_admin is True
        assert umkm.is_admin is False

    def test_is_umkm_property(self):
        """Test is_umkm property."""
        admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        umkm = User.objects.create_user(
            email="umkm@example.com",
            password="testpass123",
            full_name="UMKM User",
            role=UserRole.UMKM,
        )
        assert admin.is_umkm is False
        assert umkm.is_umkm is True

