"""
Tests for Module 4 Views (Costing CRUD, Exchange Rate)
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from apps.costings.models import Costing, ExchangeRate
from apps.users.models import UserRole
from apps.products.tests.factories import UserFactory, BusinessProfileFactory, ProductFactory
from .factories import CostingFactory, ExchangeRateFactory


@pytest.mark.django_db
class TestCostingListCreateView:
    """Tests for PBI-BE-M4-01 (list) and PBI-BE-M4-03 (create)"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.business = BusinessProfileFactory(user=self.user)
        self.product = ProductFactory(business=self.business)
        
        self.admin_user = UserFactory(role=UserRole.ADMIN)
        self.admin_business = BusinessProfileFactory()
        self.admin_product = ProductFactory(business=self.admin_business)
        
        ExchangeRateFactory(rate=Decimal("15800.00"))
    
    def test_list_costings_umkm(self):
        """PBI-BE-M4-01: UMKM sees only their product costings"""
        costing = CostingFactory(product=self.product)
        other_costing = CostingFactory(product=self.admin_product)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/costings/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == costing.id
    
    def test_list_costings_admin(self):
        """PBI-BE-M4-01: Admin sees all costings"""
        costing1 = CostingFactory(product=self.product)
        costing2 = CostingFactory(product=self.admin_product)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/v1/costings/")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2
    
    def test_create_costing_success(self):
        """PBI-BE-M4-03: Create costing with AI calculations"""
        self.client.force_authenticate(user=self.user)
        data = {
            "product_id": self.product.id,
            "cogs_per_unit": "50000.00",
            "packing_cost": "5000.00",
            "target_margin_percent": "30.00",
        }
        
        response = self.client.post("/api/v1/costings/", data=data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "recommended_exw_price" in response.data["data"]
        assert "recommended_fob_price" in response.data["data"]
        assert response.data["data"]["recommended_exw_price"] is not None
        assert Costing.objects.count() == 1
    
    def test_create_costing_invalid_values(self):
        """Test validation of cost inputs"""
        self.client.force_authenticate(user=self.user)
        data = {
            "product_id": self.product.id,
            "cogs_per_unit": "-1000",  # Invalid: negative
            "packing_cost": "5000",
            "target_margin_percent": "30",
        }
        
        response = self.client.post("/api/v1/costings/", data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_costing_invalid_product(self):
        """Test creating costing for non-existent product"""
        self.client.force_authenticate(user=self.user)
        data = {
            "product_id": 99999,
            "cogs_per_unit": "50000",
            "packing_cost": "5000",
            "target_margin_percent": "30",
        }
        
        response = self.client.post("/api/v1/costings/", data=data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCostingDetailView:
    """Tests for PBI-BE-M4-02 (get), M4-04 (update), M4-05 (delete)"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.business = BusinessProfileFactory(user=self.user)
        self.product = ProductFactory(business=self.business)
        self.costing = CostingFactory(product=self.product)
        
        self.other_user = UserFactory(role=UserRole.UMKM)
        self.other_business = BusinessProfileFactory(user=self.other_user)
        self.other_product = ProductFactory(business=self.other_business)
        self.other_costing = CostingFactory(product=self.other_product)
        
        ExchangeRateFactory(rate=Decimal("15800.00"))
    
    def test_retrieve_costing_success(self):
        """PBI-BE-M4-02: Retrieve own costing"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/costings/{self.costing.id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.costing.id
        assert response.data["recommended_exw_price"] is not None
    
    def test_retrieve_other_user_costing_forbidden(self):
        """Test cannot retrieve other user's costing"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/v1/costings/{self.other_costing.id}/")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_costing_success(self):
        """PBI-BE-M4-04: Update costing and recalculate"""
        self.client.force_authenticate(user=self.user)
        data = {
            "cogs_per_unit": "60000.00",
            "packing_cost": "7000.00",
            "target_margin_percent": "35.00",
        }
        
        response = self.client.put(f"/api/v1/costings/{self.costing.id}/", data=data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        self.costing.refresh_from_db()
        assert self.costing.cogs_per_unit == Decimal("60000.00")
        assert self.costing.recommended_exw_price is not None
    
    def test_delete_costing_success(self):
        """PBI-BE-M4-05: Delete costing"""
        self.client.force_authenticate(user=self.user)
        costing_id = self.costing.id
        
        response = self.client.delete(f"/api/v1/costings/{costing_id}/")
        
        assert response.status_code == status.HTTP_200_OK
        assert not Costing.objects.filter(id=costing_id).exists()


@pytest.mark.django_db
class TestExchangeRateView:
    """Tests for PBI-BE-M4-11 (get) and PBI-BE-M4-12 (update)"""
    
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory(role=UserRole.UMKM)
        self.admin_user = UserFactory(role=UserRole.ADMIN)
        ExchangeRateFactory(rate=Decimal("15800.00"))
    
    def test_get_exchange_rate(self):
        """PBI-BE-M4-11: Get current exchange rate"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/costings/exchange-rate/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["rate"] is not None
        assert response.data["data"]["source"] is not None
    
    def test_update_exchange_rate_admin_only(self):
        """PBI-BE-M4-12: Only admin can update exchange rate"""
        # UMKM tries to update - should fail
        self.client.force_authenticate(user=self.user)
        data = {"rate": "16000.00", "source": "manual"}
        
        response = self.client.put("/api/v1/costings/exchange-rate/", data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_exchange_rate_admin(self):
        """Test admin can update exchange rate"""
        self.client.force_authenticate(user=self.admin_user)
        data = {"rate": "16200.00", "source": "manual"}
        
        response = self.client.put("/api/v1/costings/exchange-rate/", data=data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        latest_rate = ExchangeRate.objects.latest("updated_at")
        assert latest_rate.rate == Decimal("16200.00")
