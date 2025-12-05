from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Product, ProductEnrichment
from .serializers import ProductSerializer, ProductEnrichmentSerializer
from apps.users.models import UserRole


# PBI-BE-M2-01: API GET /products - List products with pagination
# PBI-BE-M2-03: API POST /products - Create new product
# UMKM: return products milik user (by business_id)
# Admin: return semua products (dengan filter by business_id)
# Query params: page, limit, category, search
class ProductListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

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


# PBI-BE-M2-02: API GET /products/:id - Get product detail
# PBI-BE-M2-04: API PUT /products/:id - Update product
# PBI-BE-M2-05: API DELETE /products/:id - Delete product
# Validasi: UMKM hanya bisa akses product miliknya
# Include ProductEnrichment data (full)
class ProductDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    lookup_url_kwarg = "product_id"

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return Product.objects.all()
        return Product.objects.filter(business__user=user)


# PBI-BE-M2-09: API POST /products/:id/enrich - Trigger manual AI Enrichment
# Validasi: product milik user
# Call semua AI Services (HS Code, Description, SKU)
# Create atau Update ProductEnrichment
# Update last_updated_ai timestamp
class EnrichProductView(APIView):
    """Manual trigger for AI enrichment. For now it will create placeholder enrichment data."""

    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        user = request.user
        product = get_object_or_404(Product, id=product_id)
        # Check ownership for UMKM
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            return Response({"success": False, "message": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        enrichment, created = ProductEnrichment.objects.get_or_create(product=product)

        # PBI-BE-M2-06: Service AI HS Code Mapper
        # PBI-BE-M2-07: Service AI Description Rewriter
        # PBI-BE-M2-08: Service AI SKU Generator
        # Placeholder enrichment logic (replace with AI calls)
        enrichment.hs_code_recommendation = "00000000"
        enrichment.sku_generated = f"CAT-MAT-{product.id:03d}"
        enrichment.name_english_b2b = product.name_local + " (English)"
        enrichment.description_english_b2b = (product.description_local[:300])
        enrichment.marketing_highlights = ["Handmade", "High Quality"]
        enrichment.save()

        serializer = ProductEnrichmentSerializer(enrichment)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
