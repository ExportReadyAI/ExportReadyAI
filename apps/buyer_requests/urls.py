"""
URL configuration for buyer_requests app.
"""

from django.urls import path

from .views import (
    BuyerRequestListCreateView,
    BuyerRequestDetailView,
    BuyerRequestStatusView,
    BuyerRequestMatchedUMKMView,
    BuyerRequestSelectCatalogView,
    BuyerProfileCreateView,
    BuyerMyProfileView,
    BuyerProfileUpdateView,
    BuyerListView,
    BuyerDetailView,
)

app_name = "buyer_requests"

urlpatterns = [
    # Buyer Profiles (new endpoints)
    path("profile/", BuyerProfileCreateView.as_view(), name="profile-create"),
    path("profile/me/", BuyerMyProfileView.as_view(), name="profile-me"),
    path("my-profile/", BuyerMyProfileView.as_view(), name="profile-me-alias"),  # Alias for convenience
    path("profile/<int:profile_id>/", BuyerProfileUpdateView.as_view(), name="profile-update"),
    path("", BuyerListView.as_view(), name="list"),
    path("<int:buyer_id>/", BuyerDetailView.as_view(), name="detail"),
    # Buyer Requests (under /buyers/requests/)
    path("requests/", BuyerRequestListCreateView.as_view(), name="requests-list-create"),
    path("requests/<int:request_id>/", BuyerRequestDetailView.as_view(), name="requests-detail"),
    path("requests/<int:request_id>/status/", BuyerRequestStatusView.as_view(), name="requests-status"),
    path("requests/<int:request_id>/matched-umkm/", BuyerRequestMatchedUMKMView.as_view(), name="requests-matched-umkm"),
    path("requests/<int:request_id>/select-catalog/", BuyerRequestSelectCatalogView.as_view(), name="requests-select-catalog"),
]

