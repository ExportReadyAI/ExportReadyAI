"""
URL configuration for ExportReady.AI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Import master_data URL patterns
from apps.master_data.urls import (
    admin_country_urlpatterns,
    admin_regulation_urlpatterns,
    hs_code_urlpatterns,
)

# Import costing URL patterns (Module 4)
from apps.costing.urls import (
    costing_urlpatterns,
    exchange_rate_urlpatterns,
)

# API v1 URL patterns
api_v1_patterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("business-profile/", include("apps.business_profiles.urls")),
    path("products/", include("apps.products.urls")),
    # Module 3: Export Analysis
    path("export-analysis/", include("apps.export_analysis.urls")),
    path("countries/", include("apps.export_analysis.country_urls")),
    # Module 4: Costing & Financial Calculator
    path("costings/", include(costing_urlpatterns)),
    path("exchange-rate/", include(exchange_rate_urlpatterns)),
    # Module 5: Master Data (Admin Only)
    path("hs-codes/", include(hs_code_urlpatterns)),
    path("admin/countries/", include(admin_country_urlpatterns)),
    path("admin/regulations/", include(admin_regulation_urlpatterns)),
]

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/", include(api_v1_patterns)),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# Debug toolbar URLs (only in DEBUG mode)
if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

