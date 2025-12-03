"""
BusinessProfile URL Configuration
"""

from django.urls import path

from .views import (
    BusinessProfileCertificationsView,
    BusinessProfileDetailView,
    BusinessProfileListCreateView,
    DashboardSummaryView,
)

app_name = "business_profiles"

urlpatterns = [
    # PBI-BE-M1-04: POST /business-profile
    # PBI-BE-M1-05: GET /business-profile
    path("", BusinessProfileListCreateView.as_view(), name="business-profile-list-create"),
    # PBI-BE-M1-06: PUT /business-profile/:id
    path("<int:profile_id>/", BusinessProfileDetailView.as_view(), name="business-profile-detail"),
    # PBI-BE-M1-07: PATCH /business-profile/:id/certifications
    path(
        "<int:profile_id>/certifications/",
        BusinessProfileCertificationsView.as_view(),
        name="business-profile-certifications",
    ),
    # PBI-BE-M1-12: GET /dashboard/summary
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
]

