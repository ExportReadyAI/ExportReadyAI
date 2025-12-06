"""
Simplified URL patterns for Module 7: Educational Materials

Only Modules and Articles CRUD
"""

from django.urls import path

from .views import (
    ModuleListView,
    ModuleDetailView,
    ArticleListView,
    ArticleDetailView,
    ArticleFileUploadView,
)

app_name = "educational_materials"

urlpatterns = [
    # Modules
    path("modules/", ModuleListView.as_view(), name="modules-list-create"),
    path("modules/<int:module_id>/", ModuleDetailView.as_view(), name="modules-detail"),
    
    # Articles
    path("articles/", ArticleListView.as_view(), name="articles-list-create"),
    path("articles/<int:article_id>/", ArticleDetailView.as_view(), name="articles-detail"),
    path("articles/<int:article_id>/upload-file/", ArticleFileUploadView.as_view(), name="articles-upload"),
]
