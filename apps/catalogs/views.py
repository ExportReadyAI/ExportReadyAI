"""
Views for Product Catalog Module

Implements CRUD endpoints for:
- ProductCatalog: List, Create, Detail, Update, Delete
- ProductCatalogImage: Add, Update, Delete
- CatalogVariant: Add, Update, Delete
- Public catalog view for buyers
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from apps.products.models import Product
from .models import ProductCatalog, ProductCatalogImage, CatalogVariant
from .serializers import (
    ProductCatalogSerializer,
    ProductCatalogListSerializer,
    ProductCatalogCreateSerializer,
    ProductCatalogUpdateSerializer,
    CatalogImageSerializer,
    CatalogImageCreateSerializer,
    CatalogVariantSerializer,
    CatalogVariantCreateSerializer,
    PublicCatalogSerializer,
)

logger = logging.getLogger(__name__)


class CatalogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


# ============================================================
# CATALOG CRUD VIEWS (Authenticated - Owner only)
# ============================================================


class CatalogListCreateView(APIView):
    """
    GET: List all catalogs for the authenticated user
    POST: Create a new catalog entry
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CatalogPagination

    def get(self, request):
        """List all catalogs for the user's products"""
        user = request.user

        # Get user's business profile products
        catalogs = ProductCatalog.objects.filter(
            product__business__user=user
        ).select_related("product").prefetch_related("images", "variants")

        # Filter by published status if provided
        is_published = request.query_params.get("is_published")
        if is_published is not None:
            catalogs = catalogs.filter(is_published=is_published.lower() == "true")

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(catalogs, request)

        serializer = ProductCatalogListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Create a new catalog entry"""
        user = request.user

        # Validate product belongs to user
        product_id = request.data.get("product_id")
        if not product_id:
            return Response(
                {"success": False, "message": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(
                id=product_id,
                business__user=user
            )
        except Product.DoesNotExist:
            return Response(
                {"success": False, "message": "Product not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if catalog already exists for this product
        if hasattr(product, "catalog"):
            return Response(
                {"success": False, "message": "Catalog already exists for this product"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductCatalogCreateSerializer(data=request.data)
        if serializer.is_valid():
            catalog = serializer.save()
            response_serializer = ProductCatalogSerializer(catalog)
            return Response(
                {
                    "success": True,
                    "message": "Catalog created successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CatalogDetailView(APIView):
    """
    GET: Get catalog detail
    PUT/PATCH: Update catalog
    DELETE: Delete catalog
    """

    permission_classes = [IsAuthenticated]

    def get_catalog(self, catalog_id, user):
        """Helper to get catalog with ownership check"""
        return get_object_or_404(
            ProductCatalog.objects.select_related("product").prefetch_related("images", "variants"),
            id=catalog_id,
            product__business__user=user,
        )

    def get(self, request, catalog_id):
        """Get catalog detail"""
        catalog = self.get_catalog(catalog_id, request.user)
        serializer = ProductCatalogSerializer(catalog)
        return Response(serializer.data)

    def put(self, request, catalog_id):
        """Update catalog (full or partial)"""
        catalog = self.get_catalog(catalog_id, request.user)

        serializer = ProductCatalogUpdateSerializer(
            catalog,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            catalog = serializer.save()
            response_serializer = ProductCatalogSerializer(catalog)
            return Response(
                {
                    "success": True,
                    "message": "Catalog updated successfully",
                    "data": response_serializer.data,
                }
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, catalog_id):
        """Partial update - same as PUT"""
        return self.put(request, catalog_id)

    def delete(self, request, catalog_id):
        """Delete catalog"""
        catalog = self.get_catalog(catalog_id, request.user)
        catalog_id = catalog.id
        catalog.delete()

        return Response(
            {
                "success": True,
                "message": "Catalog deleted successfully",
                "data": {"id": catalog_id},
            }
        )


# ============================================================
# CATALOG IMAGE VIEWS
# ============================================================


class CatalogImageListCreateView(APIView):
    """
    GET: List images for a catalog
    POST: Add image to catalog
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """List all images for a catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )
        images = catalog.images.all()
        serializer = CatalogImageSerializer(images, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request, catalog_id):
        """Add image to catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        data = request.data.copy()
        data["catalog_id"] = catalog_id

        serializer = CatalogImageCreateSerializer(data=data)
        if serializer.is_valid():
            image = serializer.save()
            response_serializer = CatalogImageSerializer(image)
            return Response(
                {
                    "success": True,
                    "message": "Image added successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CatalogImageDetailView(APIView):
    """
    PUT: Update image
    DELETE: Delete image
    """

    permission_classes = [IsAuthenticated]

    def get_image(self, catalog_id, image_id, user):
        """Helper to get image with ownership check"""
        return get_object_or_404(
            ProductCatalogImage,
            id=image_id,
            catalog_id=catalog_id,
            catalog__product__business__user=user,
        )

    def put(self, request, catalog_id, image_id):
        """Update image"""
        image = self.get_image(catalog_id, image_id, request.user)

        serializer = CatalogImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            image = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Image updated successfully",
                    "data": serializer.data,
                }
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, catalog_id, image_id):
        """Delete image"""
        image = self.get_image(catalog_id, image_id, request.user)
        image_id = image.id
        image.delete()

        return Response(
            {
                "success": True,
                "message": "Image deleted successfully",
                "data": {"id": image_id},
            }
        )


# ============================================================
# CATALOG VARIANT VIEWS
# ============================================================


class CatalogVariantListCreateView(APIView):
    """
    GET: List variants for a catalog
    POST: Add variant to catalog
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """List all variants for a catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )
        variants = catalog.variants.all()
        serializer = CatalogVariantSerializer(variants, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request, catalog_id):
        """Add variant to catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        data = request.data.copy()
        data["catalog_id"] = catalog_id

        serializer = CatalogVariantCreateSerializer(data=data)
        if serializer.is_valid():
            variant = serializer.save()
            response_serializer = CatalogVariantSerializer(variant)
            return Response(
                {
                    "success": True,
                    "message": "Variant added successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CatalogVariantDetailView(APIView):
    """
    PUT: Update variant
    DELETE: Delete variant
    """

    permission_classes = [IsAuthenticated]

    def get_variant(self, catalog_id, variant_id, user):
        """Helper to get variant with ownership check"""
        return get_object_or_404(
            CatalogVariant,
            id=variant_id,
            catalog_id=catalog_id,
            catalog__product__business__user=user,
        )

    def put(self, request, catalog_id, variant_id):
        """Update variant"""
        variant = self.get_variant(catalog_id, variant_id, request.user)

        serializer = CatalogVariantSerializer(variant, data=request.data, partial=True)
        if serializer.is_valid():
            variant = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Variant updated successfully",
                    "data": serializer.data,
                }
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, catalog_id, variant_id):
        """Delete variant"""
        variant = self.get_variant(catalog_id, variant_id, request.user)
        variant_id = variant.id
        variant.delete()

        return Response(
            {
                "success": True,
                "message": "Variant deleted successfully",
                "data": {"id": variant_id},
            }
        )


# ============================================================
# PUBLIC CATALOG VIEWS (For Buyers)
# ============================================================


class PublicCatalogListView(APIView):
    """
    GET: List all published catalogs (public, no auth required)
    """

    permission_classes = [AllowAny]
    pagination_class = CatalogPagination

    def get(self, request):
        """List all published catalogs for buyers"""
        catalogs = ProductCatalog.objects.filter(
            is_published=True
        ).select_related("product__business").prefetch_related("images", "variants")

        # Search by display name
        search = request.query_params.get("search")
        if search:
            catalogs = catalogs.filter(display_name__icontains=search)

        # Filter by tags
        tag = request.query_params.get("tag")
        if tag:
            catalogs = catalogs.filter(tags__contains=[tag])

        # Filter by price range
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        if min_price:
            catalogs = catalogs.filter(base_price_exw__gte=min_price)
        if max_price:
            catalogs = catalogs.filter(base_price_exw__lte=max_price)

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(catalogs, request)

        serializer = PublicCatalogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicCatalogDetailView(APIView):
    """
    GET: Get published catalog detail (public, no auth required)
    """

    permission_classes = [AllowAny]

    def get(self, request, catalog_id):
        """Get catalog detail for buyers"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product__business").prefetch_related("images", "variants"),
            id=catalog_id,
            is_published=True,
        )
        serializer = PublicCatalogSerializer(catalog)
        return Response({"success": True, "data": serializer.data})
