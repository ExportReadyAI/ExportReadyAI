import pytest

from apps.products.models import Product, ProductEnrichment
from .factories import ProductFactory, ProductEnrichmentFactory


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model."""

    def test_product_creation(self):
        """Test product creation with required fields."""
        product = ProductFactory()
        assert product.name_local
        assert product.business
        assert product.created_at

    def test_product_str_representation(self):
        """Test product string representation."""
        product = ProductFactory(name_local="Test Product")
        assert "Test Product" in str(product)

    def test_product_ordering(self):
        """Test products are ordered by created_at descending."""
        product1 = ProductFactory()
        product2 = ProductFactory()
        products = Product.objects.all()
        assert products[0].id == product2.id


@pytest.mark.django_db
class TestProductEnrichmentModel:
    """Tests for ProductEnrichment model."""

    def test_enrichment_creation(self):
        """Test enrichment creation."""
        enrichment = ProductEnrichmentFactory()
        assert enrichment.product
        assert enrichment.hs_code_recommendation
        assert enrichment.last_updated_ai

    def test_enrichment_one_to_one_relationship(self):
        """Test one-to-one relationship between Product and ProductEnrichment."""
        product = ProductFactory()
        enrichment1 = ProductEnrichmentFactory(product=product)
        
        # Try to create another enrichment for same product (should fail with IntegrityError)
        with pytest.raises(Exception):
            ProductEnrichmentFactory(product=product)

    def test_enrichment_cascade_delete(self):
        """Test enrichment is deleted when product is deleted."""
        enrichment = ProductEnrichmentFactory()
        product_id = enrichment.product.id
        enrichment.product.delete()
        
        assert not ProductEnrichment.objects.filter(product_id=product_id).exists()

    def test_enrichment_str_representation(self):
        """Test enrichment string representation."""
        enrichment = ProductEnrichmentFactory()
        assert str(enrichment.product.id) in str(enrichment)
