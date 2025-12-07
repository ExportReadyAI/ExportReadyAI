"""
Tests for Product Snapshot functionality in Export Analysis

Tests cover:
- Snapshot creation on first analysis
- Snapshot preservation on reanalyze (new snapshot created)
- Snapshot usage in comparison (single snapshot for all countries)
- Change detection (is_product_changed)
- Regulation recommendations caching and retrieval
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.products.models import Product, ProductEnrichment
from apps.users.models import User, UserRole
from apps.business_profiles.models import BusinessProfile
from apps.export_analysis.models import ExportAnalysis, Country
from apps.export_analysis.services import ComplianceAIService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def umkm_user(db):
    """Create a UMKM user."""
    return User.objects.create_user(
        email="umkm@test.com",
        password="testpass123",
        full_name="Test UMKM",
        role=UserRole.UMKM.value,
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        full_name="Test Admin",
        role=UserRole.ADMIN.value,
    )


@pytest.fixture
def business_profile(db, umkm_user):
    """Create a business profile."""
    return BusinessProfile.objects.create(
        user=umkm_user,
        business_name="Test Business",
        business_type="manufacture",
        legal_entity_type="CV",
        business_address="Jl. Test No. 123",
        province="DKI Jakarta",
        regency_city="Jakarta Selatan",
        district="Kebayoran Baru",
        village="Senayan",
        postal_code="12190",
        business_phone="+628123456789",
        npwp_number="123456789012345",
        nib_number="1234567890123",
        business_email="business@test.com",
    )


@pytest.fixture
def product(db, business_profile):
    """Create a test product."""
    return Product.objects.create(
        business_profile=business_profile,
        name_local="Keripik Tempe",
        category_id=1,
        description_local="Keripik tempe renyah dan gurih",
        material_composition="Tempe, Minyak Kelapa Sawit, Garam",
        production_technique="Machine",
        finishing_type="Polish",
        quality_specs={"moisture": "5%", "texture": "crispy"},
        durability_claim="12 Bulan",
        packaging_type="Karton",
        dimensions_l_w_h={"l": 20, "w": 15, "h": 5},
        weight_net="0.150",
        weight_gross="0.170",
    )


@pytest.fixture
def product_enrichment(db, product):
    """Create product enrichment data."""
    return ProductEnrichment.objects.create(
        product=product,
        hs_code="2008.11.00",
        product_name_en="Tempe Chips",
        description_en="Crispy and savory tempe chips",
        intended_use="Food consumption",
        storage_conditions="Store in cool, dry place",
        shelf_life="12 months",
        target_market="Southeast Asia",
        certifications_needed=["Halal", "BPOM"],
        additional_features={"organic": True, "gluten_free": True},
    )


@pytest.fixture
def country_us(db):
    """Create US country."""
    return Country.objects.create(
        country_code="US",
        country_name="United States",
        market_info={"gdp": "21T", "population": "330M"},
    )


@pytest.fixture
def country_sg(db):
    """Create Singapore country."""
    return Country.objects.create(
        country_code="SG",
        country_name="Singapore",
        market_info={"gdp": "364B", "population": "5.7M"},
    )


@pytest.mark.django_db
class TestSnapshotCreation:
    """Test snapshot creation on initial analysis."""

    def test_snapshot_created_on_first_analysis(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that snapshot is created when first analysis is performed."""
        api_client.force_authenticate(user=umkm_user)

        # Create analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {
                "product_id": product.id,
                "country_code": "US",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        analysis_id = response.data["data"]["analysis_id"]

        # Verify snapshot was created
        analysis = ExportAnalysis.objects.get(analysis_id=analysis_id)
        assert analysis.product_snapshot is not None
        assert isinstance(analysis.product_snapshot, dict)

        # Verify snapshot contains product data
        snapshot = analysis.product_snapshot
        assert snapshot["name_local"] == "Keripik Tempe"
        assert snapshot["material_composition"] == "Tempe, Minyak Kelapa Sawit, Garam"

        # Verify snapshot contains enrichment data
        assert snapshot["enrichment"]["hs_code"] == "2008.11.00"
        assert snapshot["enrichment"]["product_name_en"] == "Tempe Chips"

    def test_snapshot_contains_timestamp(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that snapshot contains creation timestamp."""
        api_client.force_authenticate(user=umkm_user)

        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )

        analysis = ExportAnalysis.objects.get(analysis_id=response.data["data"]["analysis_id"])
        assert "snapshot_created_at" in analysis.product_snapshot
        assert analysis.product_snapshot["snapshot_created_at"] is not None


@pytest.mark.django_db
class TestSnapshotOnReanalyze:
    """Test snapshot behavior during reanalysis."""

    def test_reanalyze_creates_new_snapshot(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that reanalyze uses updated product data and creates new snapshot."""
        api_client.force_authenticate(user=umkm_user)

        # Initial analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]
        analysis = ExportAnalysis.objects.get(analysis_id=analysis_id)
        old_snapshot = analysis.product_snapshot.copy()

        # Modify product
        product.name_local = "Keripik Tempe Super"
        product.save()

        # Reanalyze
        response = api_client.post(
            f"/api/v1/export-analysis/{analysis_id}/reanalyze/",
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify new snapshot was created
        analysis.refresh_from_db()
        assert analysis.product_snapshot["name_local"] == "Keripik Tempe Super"
        assert analysis.product_snapshot["name_local"] != old_snapshot["name_local"]

    def test_reanalyze_clears_recommendation_cache(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that reanalyze clears the regulation recommendations cache."""
        api_client.force_authenticate(user=umkm_user)

        # Initial analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]

        # Add cache data (simulating that recommendations were generated)
        analysis = ExportAnalysis.objects.get(analysis_id=analysis_id)
        analysis.regulation_recommendations_cache = {"test": "cached_data"}
        analysis.save()

        # Reanalyze
        response = api_client.post(
            f"/api/v1/export-analysis/{analysis_id}/reanalyze/",
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify cache was cleared
        analysis.refresh_from_db()
        assert analysis.regulation_recommendations_cache == {}


@pytest.mark.django_db
class TestSnapshotInComparison:
    """Test snapshot usage in multi-country comparison."""

    def test_compare_uses_single_snapshot(
        self, api_client, umkm_user, product, product_enrichment, country_us, country_sg
    ):
        """Test that comparison creates one snapshot used for all countries."""
        api_client.force_authenticate(user=umkm_user)

        # Perform comparison
        response = api_client.post(
            "/api/v1/export-analysis/compare/",
            {
                "product_id": product.id,
                "country_codes": ["US", "SG"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        comparison_data = response.data["data"]

        # Get both analyses
        us_analysis = ExportAnalysis.objects.get(
            product=product,
            country_code="US",
        )
        sg_analysis = ExportAnalysis.objects.get(
            product=product,
            country_code="SG",
        )

        # Verify both have snapshots
        assert us_analysis.product_snapshot is not None
        assert sg_analysis.product_snapshot is not None

        # Verify snapshots are identical (same timestamp)
        assert (
            us_analysis.product_snapshot["snapshot_created_at"]
            == sg_analysis.product_snapshot["snapshot_created_at"]
        )


@pytest.mark.django_db
class TestChangeDetection:
    """Test product change detection functionality."""

    def test_product_unchanged_returns_false(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that is_product_changed returns False when product hasn't changed."""
        api_client.force_authenticate(user=umkm_user)

        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )

        analysis = ExportAnalysis.objects.get(analysis_id=response.data["data"]["analysis_id"])
        assert analysis.is_product_changed() is False

    def test_product_changed_returns_true(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that is_product_changed returns True when product has changed."""
        api_client.force_authenticate(user=umkm_user)

        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )

        analysis = ExportAnalysis.objects.get(analysis_id=response.data["data"]["analysis_id"])

        # Modify product after snapshot
        product.name_local = "Updated Name"
        product.save()

        assert analysis.is_product_changed() is True

    def test_change_detection_exposed_in_api(self, api_client, umkm_user, product, product_enrichment, country_us):
        """Test that product_changed flag is included in API response."""
        api_client.force_authenticate(user=umkm_user)

        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]

        # Get analysis detail
        response = api_client.get(f"/api/v1/export-analysis/{analysis_id}/")

        assert response.status_code == status.HTTP_200_OK
        assert "product_changed" in response.data["data"]
        assert response.data["data"]["product_changed"] is False


@pytest.mark.django_db
class TestRegulationRecommendations:
    """Test regulation recommendations caching and retrieval."""

    def test_recommendations_generated_on_first_request(
        self, api_client, umkm_user, product, product_enrichment, country_us, mocker
    ):
        """Test that recommendations are generated on first request."""
        api_client.force_authenticate(user=umkm_user)

        # Create analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]

        # Mock the AI service to avoid actual API calls
        mock_recommendations = {
            "overview": {"summary": "Test summary"},
            "prohibited_items": {"items": []},
        }
        mocker.patch.object(
            ComplianceAIService,
            "generate_regulation_recommendations",
            return_value=mock_recommendations,
        )

        # Request recommendations
        response = api_client.get(f"/api/v1/export-analysis/{analysis_id}/regulation-recommendations/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["from_cache"] is False
        assert "recommendations" in response.data["data"]

    def test_recommendations_cached_after_generation(
        self, api_client, umkm_user, product, product_enrichment, country_us, mocker
    ):
        """Test that recommendations are cached after first generation."""
        api_client.force_authenticate(user=umkm_user)

        # Create analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]

        # Mock the AI service
        mock_recommendations = {"overview": {"summary": "Test summary"}}
        mock_generate = mocker.patch.object(
            ComplianceAIService,
            "generate_regulation_recommendations",
            return_value=mock_recommendations,
        )

        # First request - generates
        response = api_client.get(f"/api/v1/export-analysis/{analysis_id}/regulation-recommendations/")
        assert response.data["data"]["from_cache"] is False
        assert mock_generate.call_count == 1

        # Second request - from cache
        response = api_client.get(f"/api/v1/export-analysis/{analysis_id}/regulation-recommendations/")
        assert response.data["data"]["from_cache"] is True
        assert mock_generate.call_count == 1  # Not called again

    def test_recommendations_use_snapshot(self, api_client, umkm_user, product, product_enrichment, country_us, mocker):
        """Test that recommendations are generated from snapshot, not live product."""
        api_client.force_authenticate(user=umkm_user)

        # Create analysis
        response = api_client.post(
            "/api/v1/export-analysis/create/",
            {"product_id": product.id, "country_code": "US"},
            format="json",
        )
        analysis_id = response.data["data"]["analysis_id"]

        # Modify product
        product.name_local = "Modified Name"
        product.save()

        # Mock and track calls
        mock_generate = mocker.patch.object(
            ComplianceAIService,
            "generate_regulation_recommendations",
            return_value={"overview": {"summary": "Test"}},
        )

        # Request recommendations
        api_client.get(f"/api/v1/export-analysis/{analysis_id}/regulation-recommendations/")

        # Verify it was called with snapshot, not live product
        call_args = mock_generate.call_args
        snapshot_used = call_args[1]["product_snapshot"]

        # Snapshot should have original name, not modified name
        assert snapshot_used["name_local"] == "Keripik Tempe"
        assert snapshot_used["name_local"] != "Modified Name"


@pytest.mark.django_db
class TestSnapshotHelperMethods:
    """Test model helper methods for snapshot handling."""

    def test_get_snapshot_product_name(self, product, product_enrichment, country_us):
        """Test get_snapshot_product_name returns correct name."""
        analysis = ExportAnalysis.objects.create(
            product=product,
            country_code="US",
            compliance_score=85.5,
        )

        # Create snapshot
        analysis.product_snapshot = analysis.create_product_snapshot(product)
        analysis.save()

        assert analysis.get_snapshot_product_name() == "Keripik Tempe"

    def test_get_snapshot_product_name_with_enrichment(self, product, product_enrichment, country_us):
        """Test that English name is included in snapshot."""
        analysis = ExportAnalysis.objects.create(
            product=product,
            country_code="US",
            compliance_score=85.5,
        )

        analysis.product_snapshot = analysis.create_product_snapshot(product)
        analysis.save()

        # Verify English name in snapshot
        assert analysis.product_snapshot["enrichment"]["product_name_en"] == "Tempe Chips"

    def test_create_product_snapshot_handles_missing_enrichment(self, product, country_us):
        """Test snapshot creation when enrichment doesn't exist."""
        # Don't create enrichment
        analysis = ExportAnalysis.objects.create(
            product=product,
            country_code="US",
            compliance_score=85.5,
        )

        snapshot = analysis.create_product_snapshot(product)

        # Should still create snapshot with null enrichment
        assert snapshot is not None
        assert snapshot["enrichment"] is None
        assert snapshot["name_local"] == "Keripik Tempe"
