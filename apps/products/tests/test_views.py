import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from apps.products.models import Product, ProductEnrichment
from apps.users.models import UserRole
from .factories import UserFactory, BusinessProfileFactory, ProductFactory


@pytest.mark.django_db
class TestProductListCreateView:
    """Tests for Product list and create endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.business = BusinessProfileFactory(user=self.user)
        self.admin_user = UserFactory(role=UserRole.ADMIN)

    def test_create_product_success(self):
        """Test successful product creation."""
        self.client.force_authenticate(user=self.user)
        data = {
            "name_local": "Keripik Tempe",
            "category_id": 1,
            "description_local": "Keripik tempe renyah",
            "material_composition": "Tempe, Minyak",
            "production_technique": "Machine",
            "finishing_type": "Polish",
            "quality_specs": {"moisture": "5%"},
            "durability_claim": "12 Bulan",
            "packaging_type": "Karton",
            "dimensions_l_w_h": {"l": 20, "w": 15, "h": 5},
            "weight_net": "0.150",
            "weight_gross": "0.170",
        }
        response = self.client.post(
            "/api/v1/products/",
            data=data,
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["name_local"] == "Keripik Tempe"
        assert Product.objects.count() == 1

    def test_create_product_without_business_profile(self):
        """Test product creation fails without business profile."""
        user_no_biz = UserFactory(role=UserRole.UMKM)
        self.client.force_authenticate(user=user_no_biz)
        data = {
            "name_local": "Keripik",
            "category_id": 1,
            "description_local": "Desc",
            "material_composition": "Material",
            "production_technique": "Machine",
            "finishing_type": "Polish",
            "quality_specs": {},
            "durability_claim": "12 Bulan",
            "packaging_type": "Karton",
            "dimensions_l_w_h": {"l": 20, "w": 15, "h": 5},
            "weight_net": "0.150",
            "weight_gross": "0.170",
        }
        response = self.client.post("/api/v1/products/", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_products_umkm(self):
        """Test UMKM sees only their products."""
        product = ProductFactory(business=self.business)
        other_business = BusinessProfileFactory()
        other_product = ProductFactory(business=other_business)

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == product.id

    def test_list_products_admin(self):
        """Test Admin sees all products."""
        product1 = ProductFactory()
        product2 = ProductFactory()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/v1/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2


@pytest.mark.django_db
class TestProductDetailView:
    """Tests for Product retrieve, update, and delete endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.business = BusinessProfileFactory(user=self.user)
        self.product = ProductFactory(business=self.business)
        self.other_user = UserFactory(role=UserRole.UMKM)
        self.other_business = BusinessProfileFactory(user=self.other_user)
        self.other_product = ProductFactory(business=self.other_business)

    def test_retrieve_product_success(self):
        """Test successful product retrieval."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/products/{self.product.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name_local"] == self.product.name_local

    def test_retrieve_other_user_product_forbidden(self):
        """Test UMKM cannot retrieve other user's product."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/products/{self.other_product.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_product_success(self):
        """Test successful product update."""
        self.client.force_authenticate(user=self.user)
        updated_data = {
            "name_local": "Updated Product Name",
            "category_id": 2,
            "description_local": "Updated description",
            "material_composition": "Updated material",
            "production_technique": "Machine",
            "finishing_type": "Polish",
            "quality_specs": {"moisture": "6%"},
            "durability_claim": "18 Bulan",
            "packaging_type": "Box",
            "dimensions_l_w_h": {"l": 25, "w": 20, "h": 10},
            "weight_net": "0.200",
            "weight_gross": "0.220",
        }
        response = self.client.put(
            f"/api/v1/products/{self.product.id}/",
            data=updated_data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.product.refresh_from_db()
        assert self.product.name_local == "Updated Product Name"

    def test_delete_product_success(self):
        """Test successful product deletion."""
        self.client.force_authenticate(user=self.user)
        product_id = self.product.id
        response = self.client.delete(f"/api/v1/products/{product_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Product.objects.filter(id=product_id).exists()

    def test_delete_other_user_product_forbidden(self):
        """Test UMKM cannot delete other user's product."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/v1/products/{self.other_product.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEnrichProductView:
    """Tests for Product enrichment endpoint."""

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.business = BusinessProfileFactory(user=self.user)
        self.product = ProductFactory(business=self.business)

    def test_enrich_product_creates_enrichment(self):
        """Test enrichment endpoint creates ProductEnrichment."""
        self.client.force_authenticate(user=self.user)
        assert not ProductEnrichment.objects.filter(product=self.product).exists()

        response = self.client.post(f"/api/v1/products/{self.product.id}/enrich/")
        assert response.status_code == status.HTTP_200_OK
        assert ProductEnrichment.objects.filter(product=self.product).exists()

    def test_enrich_product_success(self):
        """Test successful enrichment with placeholder data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/v1/products/{self.product.id}/enrich/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["hs_code_recommendation"] is not None
        assert data["sku_generated"] is not None
        assert data["name_english_b2b"] is not None
        assert data["marketing_highlights"] is not None

    def test_enrich_other_user_product_forbidden(self):
        """Test UMKM cannot enrich other user's product."""
        other_user = UserFactory(role=UserRole.UMKM)
        self.client.force_authenticate(user=other_user)
        response = self.client.post(f"/api/v1/products/{self.product.id}/enrich/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
