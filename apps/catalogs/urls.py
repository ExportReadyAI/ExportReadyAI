"""
URL Configuration for Product Catalog Module

Endpoints:
- GET/POST   /catalogs/                          - List/Create catalogs
- GET/PUT/DELETE /catalogs/:id/                  - Catalog detail
- GET/POST   /catalogs/:id/images/               - List/Add images
- PUT/DELETE /catalogs/:id/images/:image_id/     - Update/Delete image
- GET/POST   /catalogs/:id/variants/             - List/Add variants
- PUT/DELETE /catalogs/:id/variants/:variant_id/ - Update/Delete variant

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
    CatalogVariantListCreateView,
    CatalogVariantDetailView,
    PublicCatalogListView,
    PublicCatalogDetailView,
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

    # Catalog Variants
    path(
        "<int:catalog_id>/variants/",
        CatalogVariantListCreateView.as_view(),
        name="catalog-variant-list-create",
    ),
    path(
        "<int:catalog_id>/variants/<int:variant_id>/",
        CatalogVariantDetailView.as_view(),
        name="catalog-variant-detail",
    ),

    # Public catalog views (no auth required)
    path("public/", PublicCatalogListView.as_view(), name="public-catalog-list"),
    path("public/<int:catalog_id>/", PublicCatalogDetailView.as_view(), name="public-catalog-detail"),
]
