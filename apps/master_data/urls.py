"""
URL Configuration for ExportReady.AI Module 5 - Master Data (Admin Only)

Implements URL routing for:
# PBI-BE-M5-01: GET /hs-codes
# PBI-BE-M5-02: POST /hs-codes
# PBI-BE-M5-03: PUT /hs-codes/:code
# PBI-BE-M5-04: DELETE /hs-codes/:code
# PBI-BE-M5-05: POST /hs-codes/import
# PBI-BE-M5-06: POST /admin/countries
# PBI-BE-M5-07: PUT /admin/countries/:code
# PBI-BE-M5-08: DELETE /admin/countries/:code
# PBI-BE-M5-09: GET /admin/countries/:code/regulations
# PBI-BE-M5-10: POST /admin/countries/:code/regulations
# PBI-BE-M5-11: PUT /admin/regulations/:id
# PBI-BE-M5-12: DELETE /admin/regulations/:id
# PBI-BE-M5-13: POST /admin/regulations/import
"""

from django.urls import path

from .views import (
    CountryCreateView,
    CountryDeleteView,
    CountryUpdateView,
    HSCodeCreateView,
    HSCodeDeleteView,
    HSCodeDetailView,
    HSCodeImportView,
    HSCodeListView,
    HSCodeUpdateView,
    RegulationCreateView,
    RegulationDeleteView,
    RegulationImportView,
    RegulationListView,
    RegulationUpdateView,
)

# HS Code URLs
hs_code_urlpatterns = [
    path("", HSCodeListView.as_view(), name="hs-code-list"),
    path("import/", HSCodeImportView.as_view(), name="hs-code-import"),
    path("create/", HSCodeCreateView.as_view(), name="hs-code-create"),
    path("<str:hs_code>/", HSCodeDetailView.as_view(), name="hs-code-detail"),
    path("<str:hs_code>/update/", HSCodeUpdateView.as_view(), name="hs-code-update"),
    path("<str:hs_code>/delete/", HSCodeDeleteView.as_view(), name="hs-code-delete"),
]

# Admin Country URLs (separate from public country endpoints in Module 3)
admin_country_urlpatterns = [
    path("", CountryCreateView.as_view(), name="admin-country-create"),
    path("<str:country_code>/", CountryUpdateView.as_view(), name="admin-country-update"),
    path("<str:country_code>/delete/", CountryDeleteView.as_view(), name="admin-country-delete"),
    path("<str:country_code>/regulations/", RegulationListView.as_view(), name="admin-regulation-list"),
    path("<str:country_code>/regulations/create/", RegulationCreateView.as_view(), name="admin-regulation-create"),
]

# Admin Regulation URLs
admin_regulation_urlpatterns = [
    path("import/", RegulationImportView.as_view(), name="admin-regulation-import"),
    path("<int:regulation_id>/", RegulationUpdateView.as_view(), name="admin-regulation-update"),
    path("<int:regulation_id>/delete/", RegulationDeleteView.as_view(), name="admin-regulation-delete"),
]
