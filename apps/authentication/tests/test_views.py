"""
Tests for Authentication Views
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User, UserRole
from apps.users.tests.factories import UMKMUserFactory


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def user():
    """Create and return a test user."""
    return UMKMUserFactory(password="testpass123")


@pytest.mark.django_db
class TestRegisterView:
    """Test cases for user registration."""

    def test_register_success(self, api_client):
        """Test successful user registration."""
        url = reverse("authentication:register")
        data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["user"]["email"] == "newuser@example.com"
        assert response.data["data"]["user"]["role"] == UserRole.UMKM
        assert "password" not in response.data["data"]["user"]

    def test_register_duplicate_email(self, api_client, user):
        """Test registration with existing email returns 409."""
        url = reverse("authentication:register")
        data = {
            "email": user.email,
            "password": "securepass123",
            "full_name": "Another User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["success"] is False

    def test_register_invalid_email(self, api_client):
        """Test registration with invalid email."""
        url = reverse("authentication:register")
        data = {
            "email": "invalid-email",
            "password": "securepass123",
            "full_name": "Test User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_register_short_password(self, api_client):
        """Test registration with password less than 8 characters."""
        url = reverse("authentication:register")
        data = {
            "email": "test@example.com",
            "password": "short",
            "full_name": "Test User",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


@pytest.mark.django_db
class TestLoginView:
    """Test cases for user login."""

    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = reverse("authentication:login")
        data = {
            "email": user.email,
            "password": "testpass123",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "tokens" in response.data["data"]
        assert "access" in response.data["data"]["tokens"]
        assert "refresh" in response.data["data"]["tokens"]
        assert response.data["data"]["user"]["email"] == user.email

    def test_login_invalid_credentials(self, api_client, user):
        """Test login with wrong password."""
        url = reverse("authentication:login")
        data = {
            "email": user.email,
            "password": "wrongpassword",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent email."""
        url = reverse("authentication:login")
        data = {
            "email": "nonexistent@example.com",
            "password": "testpass123",
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["success"] is False


@pytest.mark.django_db
class TestMeView:
    """Test cases for getting current user."""

    def test_me_authenticated(self, api_client, user):
        """Test getting current user when authenticated."""
        api_client.force_authenticate(user=user)
        url = reverse("authentication:me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["email"] == user.email
        assert response.data["data"]["full_name"] == user.full_name
        assert response.data["data"]["role"] == user.role

    def test_me_unauthenticated(self, api_client):
        """Test getting current user without authentication."""
        url = reverse("authentication:me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

