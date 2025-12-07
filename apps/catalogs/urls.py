"""
URL Configuration for Product Catalog Module

Endpoints:
- GET/POST   /catalogs/                                     - List/Create catalogs
- GET/PUT/DELETE /catalogs/:id/                             - Catalog detail
- GET/POST   /catalogs/:id/images/                          - List/Add images
- PUT/DELETE /catalogs/:id/images/:image_id/                - Update/Delete image
- GET/POST   /catalogs/:id/variant-types/                   - List/Add variant types
- PUT/DELETE /catalogs/:id/variant-types/:type_id/          - Update/Delete variant type
- GET/POST   /catalogs/:id/variant-types/:type_id/options/  - List/Add options
- PUT/DELETE /catalogs/:id/variant-types/:type_id/options/:option_id/ - Update/Delete option

AI Features:
- POST /catalogs/:id/ai/description/             - Generate international descriptions
- GET/POST /catalogs/:id/ai/market-intelligence/ - Get/Generate market intelligence
- GET/POST /catalogs/:id/ai/pricing/             - Get/Generate pricing

Public (no auth):
- GET /catalogs/public/                          - List published catalogs
- GET /catalogs/public/:id/                      - Published catalog detail
"""

from django.urls import path

from .views import (
    CatalogListCreateView,
    CatalogDetailView,
    CatalogImageListCreateView,
    CatalogImageDetailView,
    CatalogVariantTypeListCreateView,
    CatalogVariantTypeDetailView,
    CatalogVariantOptionListCreateView,
    CatalogVariantOptionDetailView,
    PublicCatalogListView,
    PublicCatalogDetailView,
    ForwarderCatalogListView,
    # AI Views
    CatalogAIDescriptionView,
    CatalogMarketIntelligenceView,
    CatalogPricingView,
)

app_name = "catalogs"

urlpatterns = [
    # Catalog CRUD (authenticated)
    path("", CatalogListCreateView.as_view(), name="catalog-list-create"),
    path("<int:catalog_id>/", CatalogDetailView.as_view(), name="catalog-detail"),

    # Catalog Images
    path(
        "<int:catalog_id>/images/",
        CatalogImageListCreateView.as_view(),
        name="catalog-image-list-create",
    ),
    path(
        "<int:catalog_id>/images/<int:image_id>/",
        CatalogImageDetailView.as_view(),
        name="catalog-image-detail",
    ),

    # Catalog Variant Types
    path(
        "<int:catalog_id>/variant-types/",
        CatalogVariantTypeListCreateView.as_view(),
        name="catalog-variant-type-list-create",
    ),
    path(
        "<int:catalog_id>/variant-types/<int:variant_type_id>/",
        CatalogVariantTypeDetailView.as_view(),
        name="catalog-variant-type-detail",
    ),

    # Catalog Variant Options (nested under variant types)
    path(
        "<int:catalog_id>/variant-types/<int:variant_type_id>/options/",
        CatalogVariantOptionListCreateView.as_view(),
        name="catalog-variant-option-list-create",
    ),
    path(
        "<int:catalog_id>/variant-types/<int:variant_type_id>/options/<int:option_id>/",
        CatalogVariantOptionDetailView.as_view(),
        name="catalog-variant-option-detail",
    ),

    # AI Features
    path(
        "<int:catalog_id>/ai/description/",
        CatalogAIDescriptionView.as_view(),
        name="catalog-ai-description",
    ),
    path(
        "<int:catalog_id>/ai/market-intelligence/",
        CatalogMarketIntelligenceView.as_view(),
        name="catalog-market-intelligence",
    ),
    path(
        "<int:catalog_id>/ai/pricing/",
        CatalogPricingView.as_view(),
        name="catalog-ai-pricing",
    ),

    # Public catalog views (no auth required)
    path("public/", PublicCatalogListView.as_view(), name="public-catalog-list"),
    path("public/<int:catalog_id>/", PublicCatalogDetailView.as_view(), name="public-catalog-detail"),

    # Forwarder catalog views (forwarder-only)
    path("forwarder/", ForwarderCatalogListView.as_view(), name="forwarder-catalog-list"),
]
