"""
Simplified Views for Module 7: Educational Materials

Only Modules and Articles CRUD (no progress tracking)
"""

import logging
from django.db.models import Max
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.permissions import IsAdmin
from core.responses import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    validation_error_response,
)
from core.pagination import StandardResultsSetPagination

from .models import Module, Article
from .serializers import (
    ModuleSerializer,
    CreateModuleSerializer,
    UpdateModuleSerializer,
    ArticleSerializer,
    CreateArticleSerializer,
    UpdateArticleSerializer,
)

logger = logging.getLogger(__name__)


# ============================================================================
# MODULE VIEWS
# ============================================================================

class ModuleListView(APIView):
    """List and create modules."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List modules",
        description="Get list of modules with articles. Available to all authenticated users.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number"),
            OpenApiParameter(name="limit", type=int, description="Items per page"),
        ],
        responses={200: ModuleSerializer(many=True)},
        tags=["Modules"],
    )
    def get(self, request):
        """GET /modules/ - List modules."""
        queryset = Module.objects.all().order_by("order_index")

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ModuleSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ModuleSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="Modules retrieved successfully")

    @extend_schema(
        summary="Create module",
        description="Create a new module. Admin only.",
        request=CreateModuleSerializer,
        responses={201: ModuleSerializer, 400: None},
        tags=["Modules"],
    )
    def post(self, request):
        """POST /modules/ - Create module."""
        serializer = CreateModuleSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        module = serializer.save()
        response_serializer = ModuleSerializer(module)
        return created_response(data=response_serializer.data, message="Module created successfully")


class ModuleDetailView(APIView):
    """Get, update, and delete module."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get module detail",
        description="Get module details with articles.",
        responses={200: ModuleSerializer, 404: None},
        tags=["Modules"],
    )
    def get(self, request, module_id):
        """GET /modules/:id/ - Get module detail."""
        try:
            module = Module.objects.prefetch_related("articles").get(id=module_id)
        except Module.DoesNotExist:
            return not_found_response("Module not found")

        serializer = ModuleSerializer(module)
        return success_response(data=serializer.data, message="Module retrieved successfully")

    @extend_schema(
        summary="Update module",
        description="Update a module. Admin only.",
        request=UpdateModuleSerializer,
        responses={200: ModuleSerializer, 404: None},
        tags=["Modules"],
    )
    def put(self, request, module_id):
        """PUT /modules/:id/ - Update module."""
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return not_found_response("Module not found")

        serializer = UpdateModuleSerializer(module, data=request.data, partial=True)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        module = serializer.save()
        response_serializer = ModuleSerializer(module)
        return success_response(data=response_serializer.data, message="Module updated successfully")

    @extend_schema(
        summary="Delete module",
        description="Delete a module. Admin only. Cascade deletes articles.",
        responses={200: None, 404: None},
        tags=["Modules"],
    )
    def delete(self, request, module_id):
        """DELETE /modules/:id/ - Delete module."""
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return not_found_response("Module not found")

        module.delete()
        return success_response(message="Module deleted successfully")


# ============================================================================
# ARTICLE VIEWS
# ============================================================================

class ArticleListView(APIView):
    """List and create articles."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List articles",
        description="Get list of articles. Can filter by module_id. Available to all authenticated users.",
        parameters=[
            OpenApiParameter(name="module_id", type=int, description="Filter by module ID"),
            OpenApiParameter(name="page", type=int, description="Page number"),
            OpenApiParameter(name="limit", type=int, description="Items per page"),
        ],
        responses={200: ArticleSerializer(many=True)},
        tags=["Articles"],
    )
    def get(self, request):
        """GET /articles/ - List articles."""
        queryset = Article.objects.all()

        # Filter by module_id if provided
        module_id = request.query_params.get("module_id")
        if module_id:
            queryset = queryset.filter(module_id=module_id)

        queryset = queryset.order_by("order_index")

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = ArticleSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ArticleSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="Articles retrieved successfully")

    @extend_schema(
        summary="Create article",
        description="Create a new article. Admin only.",
        request=CreateArticleSerializer,
        responses={201: ArticleSerializer, 400: None},
        tags=["Articles"],
    )
    def post(self, request):
        """POST /articles/ - Create article."""
        serializer = CreateArticleSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        article = serializer.save()
        response_serializer = ArticleSerializer(article)
        return created_response(data=response_serializer.data, message="Article created successfully")


class ArticleDetailView(APIView):
    """Get, update, and delete article."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get article detail",
        description="Get article details.",
        responses={200: ArticleSerializer, 404: None},
        tags=["Articles"],
    )
    def get(self, request, article_id):
        """GET /articles/:id/ - Get article detail."""
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return not_found_response("Article not found")

        serializer = ArticleSerializer(article)
        return success_response(data=serializer.data, message="Article retrieved successfully")

    @extend_schema(
        summary="Update article",
        description="Update an article. Admin only.",
        request=UpdateArticleSerializer,
        responses={200: ArticleSerializer, 404: None},
        tags=["Articles"],
    )
    def put(self, request, article_id):
        """PUT /articles/:id/ - Update article."""
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return not_found_response("Article not found")

        serializer = UpdateArticleSerializer(article, data=request.data, partial=True)
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        article = serializer.save()
        response_serializer = ArticleSerializer(article)
        return success_response(data=response_serializer.data, message="Article updated successfully")

    @extend_schema(
        summary="Delete article",
        description="Delete an article. Admin only.",
        responses={200: None, 404: None},
        tags=["Articles"],
    )
    def delete(self, request, article_id):
        """DELETE /articles/:id/ - Delete article."""
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return not_found_response("Article not found")

        article.delete()
        return success_response(message="Article deleted successfully")


class ArticleFileUploadView(APIView):
    """Upload file for article."""

    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload file for article",
        description="Upload a file (PDF, image, etc.) for an article. Uses Supabase Storage. Admin only.",
        request={
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary"}
            },
            "required": ["file"]
        },
        responses={200: ArticleSerializer, 400: None, 404: None},
        tags=["Articles"],
    )
    def post(self, request, article_id):
        """POST /articles/:id/upload-file - Upload file."""
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return not_found_response("Article not found")

        # Validate: file must be provided
        if "file" not in request.FILES:
            return validation_error_response({"file": "File is required"})

        file = request.FILES["file"]
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return validation_error_response(
                {"file": "File size must be less than 10MB"}
            )

        # Upload to Supabase Storage (with local fallback)
        from .services import SupabaseStorageService
        
        storage_service = SupabaseStorageService()
        try:
            file_url = storage_service.upload_file(file, article_id)
            
            # Update article file_url
            article.file_url = file_url
            article.save()
            
            response_serializer = ArticleSerializer(article)
            return success_response(data=response_serializer.data, message="File uploaded successfully")
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return error_response(
                f"File upload failed: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
