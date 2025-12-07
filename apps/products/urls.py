from django.urls import path

from .views import (
    ProductListCreateView,
    ProductDetailView,
    EnrichProductView,
    ProductMarketIntelligenceView,
    ProductPricingView,
)

app_name = "products"

urlpatterns = [
    # PBI-BE-M2-01, M2-03: GET/POST /api/v1/products/
    path("", ProductListCreateView.as_view(), name="product-list-create"),
    # PBI-BE-M2-02, M2-04, M2-05: GET/PUT/DELETE /api/v1/products/<product_id>/
    path("<int:product_id>/", ProductDetailView.as_view(), name="product-detail"),
    # PBI-BE-M2-09: POST /api/v1/products/<product_id>/enrich/
    path("<int:product_id>/enrich/", EnrichProductView.as_view(), name="product-enrich"),
    # AI Features - langsung dari product (tanpa perlu catalog)
    path("<int:product_id>/ai/market-intelligence/", ProductMarketIntelligenceView.as_view(), name="product-market-intelligence"),
    path("<int:product_id>/ai/pricing/", ProductPricingView.as_view(), name="product-pricing"),
]
