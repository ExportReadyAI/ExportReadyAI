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

# API v1 URL patterns
api_v1_patterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("business-profile/", include("apps.business_profiles.urls")),
    path("products/", include("apps.products.urls")),
    # Module 4: Costings & Pricing
    path("costings/", include("apps.costings.urls")),
    # Module 3: Export Analysis
    path("export-analysis/", include("apps.export_analysis.urls")),
    path("countries/", include("apps.export_analysis.country_urls")),
    # Module 5: Master Data (Admin Only)
    path("hs-codes/", include(hs_code_urlpatterns)),
    path("admin/countries/", include(admin_country_urlpatterns)),
    path("admin/regulations/", include(admin_regulation_urlpatterns)),
    # Module 6: Market Connect & Logistics
    path("buyers/", include("apps.buyer_requests.urls")),
    path("buyer-requests/", include("apps.buyer_requests.legacy_urls")),  # Backward compatibility
    path("forwarders/", include("apps.forwarders.urls")),
    # Module 7: Educational Materials
    path("educational/", include("apps.educational_materials.urls")),
    # Product Catalogs
    path("catalogs/", include("apps.catalogs.urls")),
    # Chatbot
    path("chat/", include("apps.chatbot.urls")),
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

# Debug toolbar URLs and Media files (only in DEBUG mode)
if settings.DEBUG:
    from django.conf.urls.static import static

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

