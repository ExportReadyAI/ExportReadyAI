"""
URL Configuration for ExportReady.AI Module 3 - Countries

Implements URL routing for:
# PBI-BE-M3-11: GET /countries
# PBI-BE-M3-12: GET /countries/:code
"""

from django.urls import path

from .views import CountryDetailView, CountryListView

urlpatterns = [
    path("", CountryListView.as_view(), name="country-list"),
    path("<str:country_code>/", CountryDetailView.as_view(), name="country-detail"),
]
