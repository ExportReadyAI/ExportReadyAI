"""
Authentication URL Configuration
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, MeView, RegisterView
from .views import RegisterAdminView

app_name = "authentication"

urlpatterns = [
    # PBI-BE-M1-01: POST /auth/register
    path("register/", RegisterView.as_view(), name="register"),
    # PBI-BE-M1-02: POST /auth/login
    path("login/", LoginView.as_view(), name="login"),
    # PBI-BE-M1-03: GET /auth/me
    path("me/", MeView.as_view(), name="me"),
    # Admin-only registration endpoint
    path("register-admin/", RegisterAdminView.as_view(), name="register-admin"),
    # Token refresh endpoint
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]

