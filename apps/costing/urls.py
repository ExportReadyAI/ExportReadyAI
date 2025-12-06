"""
URL Configuration for ExportReady.AI Module 4 - Costing & Financial Calculator

Implements URL routing for:
# PBI-BE-M4-01: GET /costings
# PBI-BE-M4-02: GET /costings/:id
# PBI-BE-M4-03: POST /costings
# PBI-BE-M4-04: PUT /costings/:id
# PBI-BE-M4-05: DELETE /costings/:id
# PBI-BE-M4-11: GET /exchange-rate
# PBI-BE-M4-12: PUT /exchange-rate
# PBI-BE-M4-13: GET /costings/:id/pdf
"""

from django.urls import path

from .views import (
    CostingListView,
    CostingDetailView,
    CostingCreateView,
    CostingUpdateView,
    CostingDeleteView,
    CostingPDFView,
    ExchangeRateView,
    ExchangeRateUpdateView,
)

# Costing URLs
costing_urlpatterns = [
    # List costings - PBI-BE-M4-01
    path("", CostingListView.as_view(), name="costing-list"),
    # Create costing - PBI-BE-M4-03
    path("create/", CostingCreateView.as_view(), name="costing-create"),
    # Get costing detail - PBI-BE-M4-02
    path("<int:costing_id>/", CostingDetailView.as_view(), name="costing-detail"),
    # Update costing - PBI-BE-M4-04
    path("<int:costing_id>/update/", CostingUpdateView.as_view(), name="costing-update"),
    # Delete costing - PBI-BE-M4-05
    path("<int:costing_id>/delete/", CostingDeleteView.as_view(), name="costing-delete"),
    # Generate PDF - PBI-BE-M4-13
    path("<int:costing_id>/pdf/", CostingPDFView.as_view(), name="costing-pdf"),
]

# Exchange Rate URLs
exchange_rate_urlpatterns = [
    # Get exchange rate - PBI-BE-M4-11
    path("", ExchangeRateView.as_view(), name="exchange-rate"),
    # Update exchange rate (Admin) - PBI-BE-M4-12
    path("update/", ExchangeRateUpdateView.as_view(), name="exchange-rate-update"),
]
