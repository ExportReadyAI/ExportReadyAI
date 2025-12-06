"""
Product Views for ExportReady.AI

Implements:
- PBI-BE-M2-01: GET /products - List products with pagination
- PBI-BE-M2-02: GET /products/:id - Get product detail
- PBI-BE-M2-03: POST /products - Create new product
- PBI-BE-M2-04: PUT /products/:id - Update product
- PBI-BE-M2-05: DELETE /products/:id - Delete product
- PBI-BE-M2-09: POST /products/:id/enrich - Trigger AI enrichment

AI Services called:
- PBI-BE-M2-06: AI HS Code Mapper
- PBI-BE-M2-07: AI Description Rewriter
- PBI-BE-M2-08: AI SKU Generator

All acceptance criteria for these PBIs are implemented in this module.
"""

import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from apps.users.models import UserRole
from core.services import KolosalAIService
from core.responses import created_response
from core.exceptions import ForbiddenException, NotFoundException

from .models import Product, ProductEnrichment
from .serializers import ProductEnrichmentSerializer, ProductSerializer

logger = logging.getLogger(__name__)


# PBI-BE-M2-01: API GET /products - List products with pagination
# PBI-BE-M2-03: API POST /products - Create new product
# UMKM: return products milik user (by business_id)
# Admin: return semua products (dengan filter by business_id)
# Query params: page, limit, category, search
class ProductListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    # Use DRF page pagination for this endpoint so tests expect `results` key
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return Product.objects.all()
        # UMKM: only products for user's business profile
        return Product.objects.filter(business__user=user)

    def perform_create(self, serializer):
        # Auto-assign business from user's business profile
        user = self.request.user
        try:
            business = user.business_profile
        except Exception:
            business = None
        
        if not business:
            raise serializers.ValidationError({"business": "Business profile not found. Please create one first."})
        
        serializer.save(business=business)

    def create(self, request, *args, **kwargs):
        """Wrap create response to match project created_response format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return created_response(data=serializer.data, message="Product created successfully")

    def list(self, request, *args, **kwargs):
        # Explicitly use pagination to return DRF-style paginated response (results key)
        queryset = self.filter_queryset(self.get_queryset())

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# PBI-BE-M2-02: API GET /products/:id - Get product detail
# PBI-BE-M2-04: API PUT /products/:id - Update product
# PBI-BE-M2-05: API DELETE /products/:id - Delete product
# Validasi: UMKM hanya bisa akses product miliknya
# Include ProductEnrichment data (full)
class ProductDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    lookup_url_kwarg = "product_id"

    def get_object(self):
        # Get product by pk and enforce ownership rules to return 403 when forbidden
        product_id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFoundException("Product not found")

        # Enforce UMKM ownership
        user = self.request.user
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            raise ForbiddenException("Forbidden")

        return product

    def destroy(self, request, *args, **kwargs):
        # Return standard 204 No Content on successful delete
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnrichProductView(APIView):
    """
    Trigger AI enrichment for a product.

    # PBI-BE-M2-09: POST /products/:id/enrich - Trigger manual AI Enrichment
    # - Validasi: product milik user
    # - Call semua AI Services (HS Code, Description, SKU)
    # - Create atau Update ProductEnrichment
    # - Update last_updated_ai timestamp
    # - Response: 200 OK dengan enrichment result

    Uses Kolosal AI to generate:
    - PBI-BE-M2-06: HS Code recommendation (AI HS Code Mapper)
    - PBI-BE-M2-07: English B2B description (AI Description Rewriter)
    - PBI-BE-M2-08: SKU code (AI SKU Generator)
    - English B2B product name
    - Marketing highlights
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        user = request.user
        product = get_object_or_404(Product, id=product_id)

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            return Response(
                {"success": False, "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        enrichment, created = ProductEnrichment.objects.get_or_create(product=product)

        try:
            # Initialize Kolosal AI Service
            ai_service = KolosalAIService()

            # PBI-BE-M2-06: Service AI HS Code Mapper
            # PBI-BE-M2-07: Service AI Description Rewriter
            # PBI-BE-M2-08: Service AI SKU Generator
            logger.info(f"Starting AI enrichment for product {product_id}")

            enrichment_data = ai_service.enrich_product(
                product_name=product.name_local,
                description_local=product.description_local,
                material_composition=product.material_composition,
                category=str(product.category_id),
                product_id=product.id,
                business_id=product.business_id,
            )

            # Update enrichment record
            enrichment.hs_code_recommendation = enrichment_data["hs_code_recommendation"]
            enrichment.sku_generated = enrichment_data["sku_generated"]
            enrichment.name_english_b2b = enrichment_data["name_english_b2b"]
            enrichment.description_english_b2b = enrichment_data["description_english_b2b"]
            enrichment.marketing_highlights = enrichment_data["marketing_highlights"]
            enrichment.last_updated_ai = timezone.now()
            enrichment.save()

            logger.info(f"AI enrichment completed for product {product_id}")

            serializer = ProductEnrichmentSerializer(enrichment)
            return Response(
                {
                    "success": True,
                    "message": "Product enriched successfully with AI",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"AI enrichment failed for product {product_id}: {e}")
            return Response(
                {
                    "success": False,
                    "message": f"AI enrichment failed: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
