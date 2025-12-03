"""
User URL Configuration
"""

from django.urls import path

from .views import UserDeleteView, UserListView

app_name = "users"

urlpatterns = [
    # PBI-BE-M1-08: GET /users (Admin)
    path("", UserListView.as_view(), name="user-list"),
    # PBI-BE-M1-09: DELETE /users/:id
    path("<int:user_id>/", UserDeleteView.as_view(), name="user-delete"),
]

