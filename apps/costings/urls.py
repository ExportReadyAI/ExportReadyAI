from django.urls import path
from .views import (
    CostingListCreateView,
    CostingDetailView,
    ExchangeRateView,
    CostingPDFExportView,
)

app_name = "costings"

urlpatterns = [
    # PBI-BE-M4-01, M4-03: List and create costings
    path("", CostingListCreateView.as_view(), name="costing-list-create"),
    
    # PBI-BE-M4-02, M4-04, M4-05: Detail, update, delete costing
    path("<int:costing_id>/", CostingDetailView.as_view(), name="costing-detail"),
    
    # PBI-BE-M4-13: Export costing as PDF
    path("<int:costing_id>/pdf/", CostingPDFExportView.as_view(), name="costing-pdf-export"),
    
    # PBI-BE-M4-11, M4-12: Get and update exchange rate
    path("exchange-rate/", ExchangeRateView.as_view(), name="exchange-rate"),
]
