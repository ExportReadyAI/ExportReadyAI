"""
Tests for Business Profile Views
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.business_profiles.models import BusinessProfile
from apps.users.tests.factories import AdminUserFactory, UMKMUserFactory

from .factories import BusinessProfileFactory


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def umkm_user():
    """Create and return a UMKM test user."""
    return UMKMUserFactory(password="testpass123")


@pytest.fixture
def admin_user():
    """Create and return an Admin test user."""
    return AdminUserFactory(password="testpass123")


@pytest.mark.django_db
class TestCreateBusinessProfile:
    """Test cases for creating business profile."""

    def test_create_profile_success(self, api_client, umkm_user):
        """Test successful profile creation."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("business_profiles:business-profile-list-create")
        data = {
            "company_name": "Test Company",
            "address": "123 Test Street",
            "production_capacity_per_month": 1000,
            "year_established": 2020,
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["company_name"] == "Test Company"
        assert response.data["data"]["certifications"] == []
        assert BusinessProfile.objects.filter(user=umkm_user).exists()

    def test_create_profile_already_exists(self, api_client, umkm_user):
        """Test creating profile when one already exists returns 409."""
        BusinessProfileFactory(user=umkm_user)
        api_client.force_authenticate(user=umkm_user)
        url = reverse("business_profiles:business-profile-list-create")
        data = {
            "company_name": "Another Company",
            "address": "456 Test Street",
            "production_capacity_per_month": 2000,
            "year_established": 2021,
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["success"] is False

    def test_create_profile_future_year(self, api_client, umkm_user):
        """Test creating profile with future year_established."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("business_profiles:business-profile-list-create")
        data = {
            "company_name": "Future Company",
            "address": "123 Future Street",
            "production_capacity_per_month": 1000,
            "year_established": 2099,
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


@pytest.mark.django_db
class TestGetBusinessProfile:
    """Test cases for getting business profile."""

    def test_umkm_get_own_profile(self, api_client, umkm_user):
        """Test UMKM getting their own profile."""
        profile = BusinessProfileFactory(user=umkm_user)
        api_client.force_authenticate(user=umkm_user)
        url = reverse("business_profiles:business-profile-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["id"] == profile.id

    def test_umkm_no_profile(self, api_client, umkm_user):
        """Test UMKM with no profile returns 404."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("business_profiles:business-profile-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["success"] is False

    def test_admin_get_all_profiles(self, api_client, admin_user):
        """Test Admin getting all profiles."""
        BusinessProfileFactory.create_batch(3)
        api_client.force_authenticate(user=admin_user)
        url = reverse("business_profiles:business-profile-list-create")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert len(response.data["data"]) == 3


@pytest.mark.django_db
class TestUpdateCertifications:
    """Test cases for updating certifications."""

    def test_update_certifications_success(self, api_client, umkm_user):
        """Test successful certifications update."""
        profile = BusinessProfileFactory(user=umkm_user, certifications=[])
        api_client.force_authenticate(user=umkm_user)
        url = reverse(
            "business_profiles:business-profile-certifications",
            kwargs={"profile_id": profile.id},
        )
        data = {"certifications": ["Halal", "ISO"]}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert set(response.data["data"]["certifications"]) == {"Halal", "ISO"}

    def test_update_certifications_invalid(self, api_client, umkm_user):
        """Test updating with invalid certification."""
        profile = BusinessProfileFactory(user=umkm_user)
        api_client.force_authenticate(user=umkm_user)
        url = reverse(
            "business_profiles:business-profile-certifications",
            kwargs={"profile_id": profile.id},
        )
        data = {"certifications": ["InvalidCert"]}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_update_certifications_not_owner(self, api_client, umkm_user):
        """Test updating certifications for another user's profile."""
        other_user = UMKMUserFactory()
        profile = BusinessProfileFactory(user=other_user)
        api_client.force_authenticate(user=umkm_user)
        url = reverse(
            "business_profiles:business-profile-certifications",
            kwargs={"profile_id": profile.id},
        )
        data = {"certifications": ["Halal"]}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["success"] is False

