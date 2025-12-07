"""
Legacy URL configuration for buyer-requests endpoints (backward compatibility).
"""

from django.urls import path

from .views import (
    BuyerRequestListCreateView,
    BuyerRequestDetailView,
    BuyerRequestStatusView,
    BuyerRequestMatchedUMKMView,
    BuyerRequestSelectCatalogView,
    UMKMMatchedCatalogsView,
)

app_name = "buyer_requests_legacy"

urlpatterns = [
    path("", BuyerRequestListCreateView.as_view(), name="list-create"),
    path("<int:request_id>/", BuyerRequestDetailView.as_view(), name="detail"),
    path("<int:request_id>/status/", BuyerRequestStatusView.as_view(), name="status"),
    path("<int:request_id>/matched-umkm/", BuyerRequestMatchedUMKMView.as_view(), name="matched-umkm"),
    path("<int:request_id>/matched-catalogs/", UMKMMatchedCatalogsView.as_view(), name="matched-catalogs"),
    path("<int:request_id>/select-catalog/", BuyerRequestSelectCatalogView.as_view(), name="select-catalog"),
]

