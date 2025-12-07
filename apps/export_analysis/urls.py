"""
URL Configuration for ExportReady.AI Module 3 - Export Analysis

Implements URL routing for:
# PBI-BE-M3-01: GET /export-analysis
# PBI-BE-M3-02: GET /export-analysis/:id
# PBI-BE-M3-03: POST /export-analysis
# PBI-BE-M3-09: POST /export-analysis/:id/reanalyze
# PBI-BE-M3-10: DELETE /export-analysis/:id
# PBI-BE-M3-11: GET /countries
# PBI-BE-M3-12: GET /countries/:code
# PBI-BE-M3-13: POST /export-analysis/compare
"""

from django.urls import path

from .views import (
    CountryDetailView,
    CountryListView,
    ExportAnalysisCompareView,
    ExportAnalysisCreateView,
    ExportAnalysisDetailView,
    ExportAnalysisListView,
    ExportAnalysisReanalyzeView,
    RegulationRecommendationView,
)

urlpatterns = [
    # Export Analysis endpoints
    path("", ExportAnalysisListView.as_view(), name="export-analysis-list"),
    path("create/", ExportAnalysisCreateView.as_view(), name="export-analysis-create"),
    path("compare/", ExportAnalysisCompareView.as_view(), name="export-analysis-compare"),
    path("<int:analysis_id>/", ExportAnalysisDetailView.as_view(), name="export-analysis-detail"),
    path("<int:analysis_id>/reanalyze/", ExportAnalysisReanalyzeView.as_view(), name="export-analysis-reanalyze"),
    path(
        "<int:analysis_id>/regulation-recommendations/",
        RegulationRecommendationView.as_view(),
        name="regulation-recommendations",
    ),
]

# Country endpoints in separate URL file
country_urlpatterns = [
    path("", CountryListView.as_view(), name="country-list"),
    path("<str:country_code>/", CountryDetailView.as_view(), name="country-detail"),
]
