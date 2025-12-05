"""
Views for Module 4: Costing & Pricing Calculations

Implements:
- PBI-BE-M4-01: GET /costings - List costings with pagination
- PBI-BE-M4-02: GET /costings/:id - Get costing detail
- PBI-BE-M4-03: POST /costings - Create new costing with AI calculations
- PBI-BE-M4-04: PUT /costings/:id - Update costing and recalculate
- PBI-BE-M4-05: DELETE /costings/:id - Delete costing
- PBI-BE-M4-11: GET /exchange-rate - Get current exchange rate
- PBI-BE-M4-12: PUT /exchange-rate - Update exchange rate (Admin only)
"""

import logging
from decimal import Decimal
from datetime import datetime
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from apps.users.models import UserRole
from apps.products.models import Product
from core.responses import created_response, success_response
from core.permissions import IsAdmin
from core.exceptions import ForbiddenException, NotFoundException

from .models import Costing, ExchangeRate
from .serializers import CostingSerializer, UpdateCostingSerializer, ExchangeRateSerializer
from .services import CostingService

logger = logging.getLogger(__name__)


# PBI-BE-M4-01: API GET /costings - List costings
# PBI-BE-M4-03: API POST /costings - Create new costing
# UMKM: return costings untuk products miliknya
# Admin: return semua costings
class CostingListCreateView(ListCreateAPIView):
    """
    PBI-BE-M4-01, PBI-BE-M4-03
    
    List and create costings with AI price calculations.
    UMKM sees only their product's costings.
    Admin sees all costings.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = CostingSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return Costing.objects.select_related("product").all()
        # UMKM: only costings for their products
        return Costing.objects.filter(product__business__user=user).select_related("product")
    
    def perform_create(self, serializer):
        """
        PBI-BE-M4-03: Create costing with AI calculations
        
        Flow:
        1. Validate product ownership
        2. Call CostingService.calculate_full_costing()
        3. Save with calculated prices
        """
        product_id = serializer.validated_data.get("product_id")
        user = self.request.user
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFoundException("Product not found")
        
        # Validate ownership for UMKM
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            raise ForbiddenException("Forbidden")
        
        # Calculate prices and container capacity
        cogs = serializer.validated_data["cogs_per_unit"]
        packing = serializer.validated_data["packing_cost"]
        margin = serializer.validated_data["target_margin_percent"]
        
        try:
            costing_result = CostingService.calculate_full_costing(
                product=product,
                cogs_per_unit_idr=cogs,
                packing_cost_idr=packing,
                target_margin_percent=margin,
                target_country_code=None  # Can be extended to use default country
            )
            
            # Separate AI recommendation from model fields (don't save to model)
            ai_recommendation = costing_result.pop("ai_pricing_recommendation", None)
            
            # Save with calculated values only
            serializer.save(product=product, **costing_result)
            
            # Store AI recommendation in context for response
            self.ai_pricing_recommendation = ai_recommendation
            
            logger.info(f"Costing created for product {product_id} with EXW=${costing_result['recommended_exw_price']}")
        except Exception as e:
            logger.error(f"Error calculating costing: {e}")
            raise
    
    def create(self, request, *args, **kwargs):
        """Wrap response with created_response format and include AI recommendation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_data = serializer.data
        # Include AI recommendation if available
        if hasattr(self, "ai_pricing_recommendation") and self.ai_pricing_recommendation:
            response_data["ai_pricing_recommendation"] = self.ai_pricing_recommendation
        
        return created_response(
            data=response_data,
            message="Costing created successfully with AI calculations"
        )
    
    def list(self, request, *args, **kwargs):
        """Return DRF paginated response with results key"""
        queryset = self.filter_queryset(self.get_queryset())
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# PBI-BE-M4-02: API GET /costings/:id - Get costing detail
# PBI-BE-M4-04: API PUT /costings/:id - Update costing
# PBI-BE-M4-05: API DELETE /costings/:id - Delete costing
class CostingDetailView(RetrieveUpdateDestroyAPIView):
    """
    PBI-BE-M4-02, PBI-BE-M4-04, PBI-BE-M4-05
    
    Retrieve, update, and delete costings.
    Validates UMKM ownership.
    On update, recalculates prices.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = CostingSerializer
    lookup_url_kwarg = "costing_id"
    
    def get_object(self):
        """Get costing and verify ownership"""
        costing_id = self.kwargs.get(self.lookup_url_kwarg)
        try:
            costing = Costing.objects.select_related("product").get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")
        
        # Verify ownership for UMKM
        user = self.request.user
        if user.role != UserRole.ADMIN and costing.product.business.user_id != user.id:
            raise ForbiddenException("Forbidden")
        
        return costing
    
    def update(self, request, *args, **kwargs):
        """
        PBI-BE-M4-04: Update costing and recalculate prices
        """
        costing = self.get_object()
        serializer = UpdateCostingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update input fields
        costing.cogs_per_unit = serializer.validated_data.get("cogs_per_unit", costing.cogs_per_unit)
        costing.packing_cost = serializer.validated_data.get("packing_cost", costing.packing_cost)
        costing.target_margin_percent = serializer.validated_data.get("target_margin_percent", costing.target_margin_percent)
        
        # Recalculate all prices
        try:
            costing_result = CostingService.calculate_full_costing(
                product=costing.product,
                cogs_per_unit_idr=costing.cogs_per_unit,
                packing_cost_idr=costing.packing_cost,
                target_margin_percent=costing.target_margin_percent,
                target_country_code=None
            )
            
            # Extract AI recommendation (don't save to model)
            ai_recommendation = costing_result.pop("ai_pricing_recommendation", None)
            
            # Update calculated fields only
            costing.recommended_exw_price = costing_result["recommended_exw_price"]
            costing.recommended_fob_price = costing_result["recommended_fob_price"]
            costing.recommended_cif_price = costing_result["recommended_cif_price"]
            costing.container_20ft_capacity = costing_result["container_20ft_capacity"]
            costing.optimization_notes = costing_result["optimization_notes"]
            costing.save()
            
            result_serializer = CostingSerializer(costing)
            response_data = result_serializer.data
            
            # Include AI recommendation in response
            if ai_recommendation:
                response_data["ai_pricing_recommendation"] = ai_recommendation
            
            return success_response(
                data=response_data,
                message="Costing updated and recalculated successfully"
            )
        except Exception as e:
            logger.error(f"Error updating costing: {e}")
            raise
    
    def destroy(self, request, *args, **kwargs):
        """PBI-BE-M4-05: Delete costing"""
        costing = self.get_object()
        product_name = costing.product.name_local
        self.perform_destroy(costing)
        return Response(
            {
                "success": True,
                "message": f"Costing for '{product_name}' deleted successfully"
            },
            status=status.HTTP_200_OK
        )


# PBI-BE-M4-11: API GET /exchange-rate - Get current exchange rate
# PBI-BE-M4-12: API PUT /exchange-rate - Update exchange rate (Admin only)
class ExchangeRateView(APIView):
    """
    PBI-BE-M4-11, PBI-BE-M4-12
    
    Manage IDR-USD exchange rate.
    GET: Anyone can view current rate.
    PUT: Only Admin can update.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """PBI-BE-M4-11: Get current exchange rate"""
        try:
            rate = ExchangeRate.objects.latest("updated_at")
            serializer = ExchangeRateSerializer(rate)
            return success_response(
                data=serializer.data,
                message="Current exchange rate retrieved"
            )
        except ExchangeRate.DoesNotExist:
            # Create default exchange rate if not exists
            default_rate, created = ExchangeRate.objects.get_or_create(
                id=1,
                defaults={"rate": Decimal("15800.00"), "source": "default_bootstrap"}
            )
            serializer = ExchangeRateSerializer(default_rate)
            message = "Default exchange rate initialized (update to customize)"
            return success_response(
                data=serializer.data,
                message=message,
                status_code=status.HTTP_200_OK
            )
    
    def put(self, request):
        """PBI-BE-M4-12: Update exchange rate (Admin only)"""
        # Check permission
        if request.user.role != UserRole.ADMIN:
            raise ForbiddenException("Only admins can update exchange rate")
        
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create exchange rate
        rate, created = ExchangeRate.objects.get_or_create(
            id=1,  # Single rate record
            defaults={"rate": serializer.validated_data["rate"], "source": serializer.validated_data.get("source", "manual")}
        )
        
        if not created:
            rate.rate = serializer.validated_data["rate"]
            rate.source = serializer.validated_data.get("source", "manual")
            rate.save()
        
        result_serializer = ExchangeRateSerializer(rate)
        return success_response(
            data=result_serializer.data,
            message="Exchange rate updated successfully"
        )


# PBI-BE-M4-13: API GET /costings/:id/pdf - Generate PDF costing report
class CostingPDFExportView(APIView):
    """
    PBI-BE-M4-13
    
    Generate professional PDF costing report for a specific costing.
    Includes: company profile, product details, price breakdown, container info.
    
    Permission: User must own the costing (UMKM) or be Admin
    Response: PDF file (application/pdf)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, costing_id):
        """Generate and return PDF costing report"""
        try:
            costing = Costing.objects.select_related("product", "product__business").get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # Verify ownership
        user = request.user
        if user.role != UserRole.ADMIN and costing.product.business.user_id != user.id:
            raise ForbiddenException("Forbidden")

        try:
            from .pdf_service import CostingPDFService

            # Generate PDF
            pdf_buffer = CostingPDFService.generate_costing_pdf(
                costing=costing,
                business_profile=costing.product.business,
                product=costing.product,
            )

            # Return PDF response using HttpResponse (not DRF Response) to avoid JSON serialization
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type="application/pdf",
                status=status.HTTP_200_OK,
            )
            response["Content-Disposition"] = f'attachment; filename="costing_{costing_id}_{datetime.now().strftime("%Y%m%d")}.pdf"'

            logger.info(f"PDF costing report exported for costing {costing_id}")
            return response

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return Response(
                {"success": False, "message": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

