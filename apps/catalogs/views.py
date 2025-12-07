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
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import models

from apps.products.models import Product
from .models import ProductCatalog, ProductCatalogImage, CatalogVariantType, CatalogVariantOption
from .serializers import (
    ProductCatalogSerializer,
    ProductCatalogListSerializer,
    ProductCatalogCreateSerializer,
    ProductCatalogUpdateSerializer,
    CatalogImageSerializer,
    CatalogImageCreateSerializer,
    CatalogVariantTypeSerializer,
    CatalogVariantTypeCreateSerializer,
    CatalogVariantOptionSerializer,
    CatalogVariantOptionCreateSerializer,
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
    POST: Create a new catalog entry with multiple image uploads
    
    Supports multipart/form-data for direct image uploads to Supabase.
    Multiple images can be uploaded using 'images[]' field (array of files).
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CatalogPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """List all catalogs for the user's products"""
        user = request.user

        # Get user's business profile products
        catalogs = ProductCatalog.objects.filter(
            product__business__user=user
        ).select_related("product").prefetch_related("images", "variant_types__options")

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
        """
        Create a new catalog entry with multiple image uploads.
        
        Supports:
        - multipart/form-data: Upload images directly (images[] field for multiple files)
        - application/json: Use image URLs instead
        
        Image files are uploaded to Supabase Storage bucket "catalogs".
        Max file size: 10MB per image.
        """
        from .services import get_catalog_storage_service
        
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

        # Handle image uploads before serializer validation
        data = request.data.copy()
        uploaded_images = []
        
        # Handle multiple image uploads (images[] or images)
        image_files = []
        if "images[]" in request.FILES:
            image_files = request.FILES.getlist("images[]")
        elif "images" in request.FILES:
            # Support both single and multiple
            images = request.FILES.getlist("images")
            image_files = images if isinstance(images, list) else [images]
        elif "image" in request.FILES:
            # Single image for backward compatibility
            image_files = [request.FILES.get("image")]
        
        # Upload images to Supabase if any files provided
        if image_files:
            storage_service = get_catalog_storage_service()
            # We'll create catalog first, then upload images
            # Store files temporarily to upload after catalog creation
            uploaded_images = image_files
        
        # Remove image files from data (they'll be handled separately)
        data.pop("images[]", None)
        data.pop("images", None)
        data.pop("image", None)
        
        # Create catalog first
        serializer = ProductCatalogCreateSerializer(data=data)
        if serializer.is_valid():
            catalog = serializer.save()
            
            # Now upload images to Supabase and create image records
            if uploaded_images:
                storage_service = get_catalog_storage_service()
                max_size = 10 * 1024 * 1024  # 10MB
                
                for idx, image_file in enumerate(uploaded_images):
                    # Validate file size
                    if image_file.size > max_size:
                        logger.error(f"Image {idx+1} size ({image_file.size} bytes) exceeds 10MB limit")
                        # Continue with other images, but log the error
                        continue
                    
                    try:
                        # Upload to Supabase
                        supabase_url = storage_service.upload_image(image_file, catalog.id)
                        
                        if supabase_url:
                            # Create image record with Supabase URL
                            ProductCatalogImage.objects.create(
                                catalog=catalog,
                                image_url=supabase_url,
                                alt_text=request.data.get(f"alt_text_{idx}", ""),
                                sort_order=idx,
                                is_primary=(idx == 0)  # First image is primary
                            )
                            logger.info(f"Image {idx+1} uploaded and saved for catalog {catalog.id}")
                        else:
                            logger.warning(f"Image {idx+1} upload returned None, skipping")
                    except ValueError as e:
                        # File size validation error (double-check)
                        logger.error(f"Image {idx+1} validation failed: {e}")
                        # Continue with other images
                    except Exception as e:
                        logger.error(f"Failed to upload image {idx+1}: {e}")
                        # Continue with other images
            
            # Refresh catalog to include new images
            catalog.refresh_from_db()
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
    PUT/PATCH: Update catalog (supports multiple image uploads via multipart/form-data)
    DELETE: Delete catalog
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_catalog(self, catalog_id, user):
        """Helper to get catalog with ownership check"""
        return get_object_or_404(
            ProductCatalog.objects.select_related("product").prefetch_related("images", "variant_types__options"),
            id=catalog_id,
            product__business__user=user,
        )

    def get(self, request, catalog_id):
        """Get catalog detail"""
        catalog = self.get_catalog(catalog_id, request.user)
        serializer = ProductCatalogSerializer(catalog)
        return Response(serializer.data)

    def put(self, request, catalog_id):
        """
        Update catalog (full or partial) with optional multiple image uploads.
        
        Supports:
        - multipart/form-data: Upload new images (images[] field for multiple files)
        - application/json: Update catalog fields only
        
        New images are uploaded to Supabase Storage and added to existing images.
        """
        from .services import get_catalog_storage_service
        
        catalog = self.get_catalog(catalog_id, request.user)

        # Handle new image uploads
        data = request.data.copy()
        uploaded_images = []
        
        # Handle multiple image uploads (images[] or images)
        image_files = []
        if "images[]" in request.FILES:
            image_files = request.FILES.getlist("images[]")
        elif "images" in request.FILES:
            images = request.FILES.getlist("images")
            image_files = images if isinstance(images, list) else [images]
        elif "image" in request.FILES:
            image_files = [request.FILES.get("image")]
        
        if image_files:
            uploaded_images = image_files
        
        # Remove image files from data
        data.pop("images[]", None)
        data.pop("images", None)
        data.pop("image", None)

        serializer = ProductCatalogUpdateSerializer(
            catalog,
            data=data,
            partial=True
        )

        if serializer.is_valid():
            catalog = serializer.save()
            
            # Upload new images to Supabase and create image records
            if uploaded_images:
                storage_service = get_catalog_storage_service()
                max_size = 10 * 1024 * 1024  # 10MB
                
                # Get current max sort_order to append new images
                max_sort_order = catalog.images.aggregate(
                    max_order=models.Max("sort_order")
                )["max_order"] or -1
                
                for idx, image_file in enumerate(uploaded_images):
                    # Validate file size
                    if image_file.size > max_size:
                        logger.error(f"Image {idx+1} size ({image_file.size} bytes) exceeds 10MB limit")
                        # Continue with other images
                        continue
                    
                    try:
                        # Upload to Supabase
                        supabase_url = storage_service.upload_image(image_file, catalog.id)
                        
                        if supabase_url:
                            # Create image record with Supabase URL
                            ProductCatalogImage.objects.create(
                                catalog=catalog,
                                image_url=supabase_url,
                                alt_text=request.data.get(f"alt_text_{idx}", ""),
                                sort_order=max_sort_order + idx + 1,
                                is_primary=False  # Don't change primary on update
                            )
                            logger.info(f"New image {idx+1} uploaded and saved for catalog {catalog.id}")
                        else:
                            logger.warning(f"Image {idx+1} upload returned None, skipping")
                    except ValueError as e:
                        # File size validation error (double-check)
                        logger.error(f"Image {idx+1} validation failed: {e}")
                    except Exception as e:
                        logger.error(f"Failed to upload image {idx+1}: {e}")
            
            # Refresh catalog to include new images
            catalog.refresh_from_db()
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
    POST: Add image to catalog (supports both file upload and URL)

    For file upload, use multipart/form-data with 'image' field.
    For URL, use application/json with 'image_url' field.

    File uploads are stored in Supabase Storage.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, catalog_id):
        """List all images for a catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )
        images = catalog.images.all()
        serializer = CatalogImageSerializer(images, many=True, context={"request": request})
        return Response({"success": True, "data": serializer.data})

    def post(self, request, catalog_id):
        """
        Add image to catalog.

        Supports two methods:
        1. File upload: POST with multipart/form-data, include 'image' file
           -> Uploaded to Supabase Storage, URL stored in image_url
        2. URL: POST with application/json, include 'image_url' string
        """
        from .services import get_catalog_storage_service

        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        data = request.data.copy()
        data["catalog_id"] = catalog_id

        # If file is uploaded, try to upload to Supabase
        uploaded_file = request.FILES.get("image")
        if uploaded_file:
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return Response(
                    {
                        "success": False,
                        "message": f"Image size ({uploaded_file.size} bytes) exceeds maximum allowed size (10MB)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            try:
                storage_service = get_catalog_storage_service()
                supabase_url = storage_service.upload_image(uploaded_file, catalog_id)

                if supabase_url:
                    # Successfully uploaded to Supabase, store URL
                    data["image_url"] = supabase_url
                    data.pop("image", None)
                # else: supabase_url is None, keep the file in data for local storage via ImageField
            except ValueError as e:
                # File size validation error (already checked above, but catch just in case)
                return Response(
                    {
                        "success": False,
                        "message": str(e)
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Failed to upload image to Supabase: {e}")
                return Response(
                    {
                        "success": False,
                        "message": f"Failed to upload image: {str(e)}"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        serializer = CatalogImageCreateSerializer(data=data)
        if serializer.is_valid():
            image = serializer.save()
            response_serializer = CatalogImageSerializer(image, context={"request": request})
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
    PUT: Update image (supports file upload to Supabase)
    DELETE: Delete image (also from Supabase)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_image(self, catalog_id, image_id, user):
        """Helper to get image with ownership check"""
        return get_object_or_404(
            ProductCatalogImage,
            id=image_id,
            catalog_id=catalog_id,
            catalog__product__business__user=user,
        )

    def put(self, request, catalog_id, image_id):
        """Update image (can update file or URL)"""
        from .services import get_catalog_storage_service

        image = self.get_image(catalog_id, image_id, request.user)

        data = request.data.copy()

        # If new file is uploaded, try to upload to Supabase
        uploaded_file = request.FILES.get("image")
        if uploaded_file:
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return Response(
                    {
                        "success": False,
                        "message": f"Image size ({uploaded_file.size} bytes) exceeds maximum allowed size (10MB)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            try:
                storage_service = get_catalog_storage_service()
                # Delete old image from Supabase if exists
                if image.image_url:
                    storage_service.delete_image(image.image_url)
                # Upload new image
                supabase_url = storage_service.upload_image(uploaded_file, catalog_id)

                if supabase_url:
                    data["image_url"] = supabase_url
                    data.pop("image", None)
                # else: keep file in data for local storage
            except ValueError as e:
                # File size validation error
                return Response(
                    {
                        "success": False,
                        "message": str(e)
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.error(f"Failed to upload image to Supabase: {e}")
                return Response(
                    {
                        "success": False,
                        "message": f"Failed to upload image: {str(e)}"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        serializer = CatalogImageSerializer(
            image, data=data, partial=True, context={"request": request}
        )
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
        """Delete image (also from Supabase storage)"""
        from .services import get_catalog_storage_service

        image = self.get_image(catalog_id, image_id, request.user)
        image_id_to_return = image.id

        # Delete from Supabase storage if it's a Supabase URL
        if image.image_url:
            try:
                storage_service = get_catalog_storage_service()
                storage_service.delete_image(image.image_url)
            except Exception as e:
                logger.warning(f"Failed to delete image from Supabase: {e}")

        image.delete()

        return Response(
            {
                "success": True,
                "message": "Image deleted successfully",
                "data": {"id": image_id_to_return},
            }
        )


# ============================================================
# CATALOG VARIANT TYPE VIEWS
# ============================================================


class CatalogVariantTypeListCreateView(APIView):
    """
    GET: List variant types for a catalog (with options)
    POST: Add variant type to catalog
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """List all variant types for a catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )
        variant_types = catalog.variant_types.prefetch_related("options").all()
        serializer = CatalogVariantTypeSerializer(variant_types, many=True)

        # Also return predefined types for dropdown
        predefined_types = CatalogVariantTypeSerializer.get_predefined_types()

        return Response({
            "success": True,
            "data": serializer.data,
            "predefined_types": predefined_types,
        })

    def post(self, request, catalog_id):
        """Add variant type to catalog"""
        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        data = request.data.copy()
        data["catalog_id"] = catalog_id

        serializer = CatalogVariantTypeCreateSerializer(data=data)
        if serializer.is_valid():
            variant_type = serializer.save()
            response_serializer = CatalogVariantTypeSerializer(variant_type)
            return Response(
                {
                    "success": True,
                    "message": "Variant type added successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CatalogVariantTypeDetailView(APIView):
    """
    PUT: Update variant type
    DELETE: Delete variant type (and all its options)
    """

    permission_classes = [IsAuthenticated]

    def get_variant_type(self, catalog_id, variant_type_id, user):
        """Helper to get variant type with ownership check"""
        return get_object_or_404(
            CatalogVariantType,
            id=variant_type_id,
            catalog_id=catalog_id,
            catalog__product__business__user=user,
        )

    def put(self, request, catalog_id, variant_type_id):
        """Update variant type"""
        variant_type = self.get_variant_type(catalog_id, variant_type_id, request.user)

        serializer = CatalogVariantTypeSerializer(variant_type, data=request.data, partial=True)
        if serializer.is_valid():
            variant_type = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Variant type updated successfully",
                    "data": serializer.data,
                }
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, catalog_id, variant_type_id):
        """Delete variant type and all its options"""
        variant_type = self.get_variant_type(catalog_id, variant_type_id, request.user)
        variant_type_id_to_return = variant_type.id
        variant_type.delete()

        return Response(
            {
                "success": True,
                "message": "Variant type deleted successfully",
                "data": {"id": variant_type_id_to_return},
            }
        )


# ============================================================
# CATALOG VARIANT OPTION VIEWS
# ============================================================


class CatalogVariantOptionListCreateView(APIView):
    """
    GET: List options for a variant type
    POST: Add option to variant type
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id, variant_type_id):
        """List all options for a variant type"""
        variant_type = get_object_or_404(
            CatalogVariantType,
            id=variant_type_id,
            catalog_id=catalog_id,
            catalog__product__business__user=request.user,
        )
        options = variant_type.options.all()
        serializer = CatalogVariantOptionSerializer(options, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request, catalog_id, variant_type_id):
        """Add option to variant type"""
        variant_type = get_object_or_404(
            CatalogVariantType,
            id=variant_type_id,
            catalog_id=catalog_id,
            catalog__product__business__user=request.user,
        )

        data = request.data.copy()
        data["variant_type_id"] = variant_type_id

        serializer = CatalogVariantOptionCreateSerializer(data=data)
        if serializer.is_valid():
            option = serializer.save()
            response_serializer = CatalogVariantOptionSerializer(option)
            return Response(
                {
                    "success": True,
                    "message": "Option added successfully",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CatalogVariantOptionDetailView(APIView):
    """
    PUT: Update option
    DELETE: Delete option
    """

    permission_classes = [IsAuthenticated]

    def get_option(self, catalog_id, variant_type_id, option_id, user):
        """Helper to get option with ownership check"""
        return get_object_or_404(
            CatalogVariantOption,
            id=option_id,
            variant_type_id=variant_type_id,
            variant_type__catalog_id=catalog_id,
            variant_type__catalog__product__business__user=user,
        )

    def put(self, request, catalog_id, variant_type_id, option_id):
        """Update option"""
        option = self.get_option(catalog_id, variant_type_id, option_id, request.user)

        serializer = CatalogVariantOptionSerializer(option, data=request.data, partial=True)
        if serializer.is_valid():
            option = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Option updated successfully",
                    "data": serializer.data,
                }
            )

        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, catalog_id, variant_type_id, option_id):
        """Delete option"""
        option = self.get_option(catalog_id, variant_type_id, option_id, request.user)
        option_id_to_return = option.id
        option.delete()

        return Response(
            {
                "success": True,
                "message": "Option deleted successfully",
                "data": {"id": option_id_to_return},
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
        ).select_related("product__business").prefetch_related("images", "variant_types__options")

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
            ProductCatalog.objects.select_related("product__business").prefetch_related("images", "variant_types__options"),
            id=catalog_id,
            is_published=True,
        )
        serializer = PublicCatalogSerializer(catalog)
        return Response({"success": True, "data": serializer.data})


# ============================================================
# AI FEATURE VIEWS
# ============================================================

from .models import ProductMarketIntelligence, ProductPricingResult
from .services import get_catalog_ai_service


class CatalogAIDescriptionView(APIView):
    """
    POST: Generate international product description using AI

    Returns 3 versions:
    - export_buyer_description: English B2B description
    - technical_spec_sheet: Technical specifications (flexible JSON)
    - safety_sheet: Material/Food safety info (flexible JSON)

    Optional: save_to_catalog=true to auto-save to catalog fields
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, catalog_id):
        """Generate international product description"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )

        product = catalog.product
        save_to_catalog = request.data.get("save_to_catalog", False)

        try:
            ai_service = get_catalog_ai_service()
            result = ai_service.generate_international_description(
                product_name=product.name_local,
                description_local=product.description_local,
                material_composition=product.material_composition,
                dimensions=product.dimensions_l_w_h,
                weight_net=float(product.weight_net) if product.weight_net else None,
                weight_gross=float(product.weight_gross) if product.weight_gross else None,
                category=str(product.category_id) if product.category_id else "",
                is_food_product=self._is_food_product(product),
            )

            if result.get("success"):
                data = result.get("data", {})

                # Format response for frontend auto-fill
                response_data = {
                    "export_description": data.get("export_buyer_description", ""),
                    "technical_specs": data.get("technical_spec_sheet", {}),
                    "safety_info": data.get("safety_sheet", {}),
                }

                # Optionally save to catalog
                if save_to_catalog:
                    catalog.export_description = response_data["export_description"]
                    catalog.technical_specs = response_data["technical_specs"]
                    catalog.safety_info = response_data["safety_info"]
                    catalog.save()

                    return Response({
                        "success": True,
                        "message": "Description generated and saved to catalog",
                        "data": response_data,
                        "saved_to_catalog": True,
                    })

                return Response({
                    "success": True,
                    "message": "Description generated successfully",
                    "data": response_data,
                    "saved_to_catalog": False,
                })

            return Response(
                {"success": False, "message": result.get("error", "Failed to generate description")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Error generating description: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _is_food_product(self, product):
        """Check if product is food/beverage based on category or material"""
        food_keywords = ["food", "makanan", "snack", "beverage", "minuman", "kopi", "coffee", "tea", "teh"]

        material = (product.material_composition or "").lower()
        description = (product.description_local or "").lower()

        for keyword in food_keywords:
            if keyword in material or keyword in description:
                return True
        return False


class CatalogMarketIntelligenceView(APIView):
    """
    GET: Get existing market intelligence for a product (via catalog)
    POST: Generate market intelligence using AI (one-time per PRODUCT, saved to DB)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """Get existing market intelligence"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )
        product = catalog.product

        # Check on PRODUCT level, not catalog
        if hasattr(product, 'market_intelligence'):
            mi = product.market_intelligence
            return Response({
                "success": True,
                "message": "Market intelligence retrieved",
                "data": {
                    "id": mi.id,
                    "product_id": product.id,
                    "recommended_countries": mi.recommended_countries,
                    "countries_to_avoid": mi.countries_to_avoid,
                    "market_trends": mi.market_trends,
                    "competitive_landscape": mi.competitive_landscape,
                    "growth_opportunities": mi.growth_opportunities,
                    "risks_and_challenges": mi.risks_and_challenges,
                    "overall_recommendation": mi.overall_recommendation,
                    "generated_at": mi.generated_at,
                }
            })

        return Response({
            "success": False,
            "message": "Market intelligence not yet generated for this product. Use POST to generate.",
        }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, catalog_id):
        """Generate market intelligence"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )
        product = catalog.product

        # Check if already exists on PRODUCT level
        if hasattr(product, 'market_intelligence'):
            return Response({
                "success": False,
                "message": "Market intelligence already exists for this product. Each product can only have one market intelligence result.",
                "existing_data": {
                    "id": product.market_intelligence.id,
                    "product_id": product.id,
                    "generated_at": product.market_intelligence.generated_at,
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_service = get_catalog_ai_service()
            result = ai_service.get_market_intelligence(
                product_name=product.name_local,
                description=product.description_local,
                material_composition=product.material_composition,
                category=str(product.category_id) if product.category_id else "",
                current_price_usd=float(catalog.base_price_exw) if catalog.base_price_exw else None,
                production_capacity=None,
            )

            if result.get("success"):
                data = result.get("data", {})

                # Save to database - linked to PRODUCT
                mi = ProductMarketIntelligence.objects.create(
                    product=product,
                    recommended_countries=data.get("recommended_countries", []),
                    countries_to_avoid=data.get("countries_to_avoid", []),
                    market_trends=data.get("market_trends", []),
                    competitive_landscape=data.get("competitive_landscape", ""),
                    growth_opportunities=data.get("growth_opportunities", []),
                    risks_and_challenges=data.get("risks_and_challenges", []),
                    overall_recommendation=data.get("overall_recommendation", ""),
                )

                return Response({
                    "success": True,
                    "message": "Market intelligence generated and saved",
                    "data": {
                        "id": mi.id,
                        "product_id": product.id,
                        "recommended_countries": mi.recommended_countries,
                        "countries_to_avoid": mi.countries_to_avoid,
                        "market_trends": mi.market_trends,
                        "competitive_landscape": mi.competitive_landscape,
                        "growth_opportunities": mi.growth_opportunities,
                        "risks_and_challenges": mi.risks_and_challenges,
                        "overall_recommendation": mi.overall_recommendation,
                        "generated_at": mi.generated_at,
                    }
                })

            return Response(
                {"success": False, "message": result.get("error", "Failed to generate market intelligence")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CatalogPricingView(APIView):
    """
    GET: Get existing pricing result for a product (via catalog)
    POST: Generate pricing using AI (one-time per PRODUCT, saved to DB)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """Get existing pricing result"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )
        product = catalog.product

        # Check on PRODUCT level, not catalog
        if hasattr(product, 'pricing_result'):
            pr = product.pricing_result
            return Response({
                "success": True,
                "message": "Pricing result retrieved",
                "data": {
                    "id": pr.id,
                    "product_id": product.id,
                    "cogs_per_unit_idr": float(pr.cogs_per_unit_idr),
                    "target_margin_percent": float(pr.target_margin_percent),
                    "target_country_code": pr.target_country_code,
                    "exchange_rate_used": float(pr.exchange_rate_used),
                    "exw_price_usd": float(pr.exw_price_usd),
                    "fob_price_usd": float(pr.fob_price_usd),
                    "cif_price_usd": float(pr.cif_price_usd) if pr.cif_price_usd else None,
                    "pricing_insight": pr.pricing_insight,
                    "pricing_breakdown": pr.pricing_breakdown,
                    "generated_at": pr.generated_at,
                }
            })

        return Response({
            "success": False,
            "message": "Pricing not yet generated for this product. Use POST to generate.",
        }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, catalog_id):
        """Generate pricing"""
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )
        product = catalog.product

        # Check if already exists on PRODUCT level
        if hasattr(product, 'pricing_result'):
            return Response({
                "success": False,
                "message": "Pricing result already exists for this product. Each product can only have one pricing result.",
                "existing_data": {
                    "id": product.pricing_result.id,
                    "product_id": product.id,
                    "exw_price_usd": float(product.pricing_result.exw_price_usd),
                    "generated_at": product.pricing_result.generated_at,
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get input parameters
        cogs_per_unit_idr = request.data.get("cogs_per_unit_idr")
        target_margin_percent = request.data.get("target_margin_percent", 25)
        target_country_code = request.data.get("target_country_code")

        if not cogs_per_unit_idr:
            return Response(
                {"success": False, "message": "cogs_per_unit_idr is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from decimal import Decimal
            ai_service = get_catalog_ai_service()
            result = ai_service.generate_catalog_pricing(
                product_name=product.name_local,
                cogs_per_unit=Decimal(str(cogs_per_unit_idr)),
                target_margin_percent=Decimal(str(target_margin_percent)),
                material_composition=product.material_composition,
                target_country_code=target_country_code,
                dimensions=product.dimensions_l_w_h,
                weight_gross=float(product.weight_gross) if product.weight_gross else None,
            )

            if result.get("success"):
                data = result.get("data", {})

                # Save to database - linked to PRODUCT
                pr = ProductPricingResult.objects.create(
                    product=product,
                    cogs_per_unit_idr=Decimal(str(data.get("cogs_per_unit_idr", cogs_per_unit_idr))),
                    target_margin_percent=Decimal(str(data.get("target_margin_percent", target_margin_percent))),
                    target_country_code=target_country_code,
                    exchange_rate_used=Decimal(str(data.get("exchange_rate_used", 16000))),
                    exw_price_usd=Decimal(str(data.get("exw_price_usd", 0))),
                    fob_price_usd=Decimal(str(data.get("fob_price_usd", 0))),
                    cif_price_usd=Decimal(str(data.get("cif_price_usd"))) if data.get("cif_price_usd") else None,
                    pricing_insight=data.get("pricing_insight", ""),
                    pricing_breakdown=data.get("pricing_breakdown", {}),
                )

                # Update catalog prices
                catalog.base_price_exw = pr.exw_price_usd
                catalog.base_price_fob = pr.fob_price_usd
                catalog.base_price_cif = pr.cif_price_usd
                catalog.save()

                return Response({
                    "success": True,
                    "message": "Pricing generated and saved",
                    "data": {
                        "id": pr.id,
                        "product_id": product.id,
                        "cogs_per_unit_idr": float(pr.cogs_per_unit_idr),
                        "target_margin_percent": float(pr.target_margin_percent),
                        "target_country_code": pr.target_country_code,
                        "exchange_rate_used": float(pr.exchange_rate_used),
                        "exw_price_usd": float(pr.exw_price_usd),
                        "fob_price_usd": float(pr.fob_price_usd),
                        "cif_price_usd": float(pr.cif_price_usd) if pr.cif_price_usd else None,
                        "pricing_insight": pr.pricing_insight,
                        "pricing_breakdown": pr.pricing_breakdown,
                        "generated_at": pr.generated_at,
                    }
                })

            return Response(
                {"success": False, "message": result.get("error", "Failed to generate pricing")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            logger.error(f"Error generating pricing: {e}", exc_info=True)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
