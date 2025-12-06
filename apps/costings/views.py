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
- PBI-BE-M4-13: GET /costings/:id/pdf - Generate PDF report
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
from .pdf_service import CostingPDFService

logger = logging.getLogger(__name__)


class CostingListCreateView(ListCreateAPIView):
    """
    PBI-BE-M4-01, PBI-BE-M4-03
    
    GET: List costings with pagination
    - UMKM: return costings untuk products miliknya
    - Admin: return semua costings
    - Query params: page, limit, search, sort_by
    - Include: product name
    
    POST: Create new costing with AI calculations
    - UMKM only (product must belong to user)
    - Trigger AI Price Calculation
    - Trigger AI Container Optimizer
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = CostingSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Filter costings based on user role"""
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return Costing.objects.select_related("product__business").all()
        # UMKM: only costings for their products
        return Costing.objects.filter(product__business__user=user).select_related("product__business")
    
    def perform_create(self, serializer):
        """
        PBI-BE-M4-03: Create costing with AI calculations
        
        Validasi:
        - Product milik user (UMKM)
        - Semua nilai positif
        
        Flow:
        1. Validate product ownership
        2. Call CostingService.calculate_full_costing()
        3. Save with calculated prices
        """
        product_id = serializer.validated_data.get("product_id")
        user = self.request.user
        
        # Get product
        try:
            product = Product.objects.select_related("business__user").get(id=product_id)
        except Product.DoesNotExist:
            raise NotFoundException("Product not found")
        
        # PBI-BE-M4-03: Validasi product milik user
        if user.role != UserRole.ADMIN and product.business.user.id != user.id:
            logger.warning(f"Forbidden: user {user.email} trying to create costing for product {product_id} owned by {product.business.user.email}")
            raise ForbiddenException("You can only create costings for your own products")
        
        # Get input values
        cogs = serializer.validated_data["cogs_per_unit"]
        packing = serializer.validated_data["packing_cost"]
        margin = serializer.validated_data["target_margin_percent"]
        target_country = serializer.validated_data.get("target_country_code")
        
        # Calculate with AI
        try:
            costing_result = CostingService.calculate_full_costing(
                product=product,
                cogs_per_unit_idr=cogs,
                packing_cost_idr=packing,
                target_margin_percent=margin,
                target_country_code=target_country
            )
            
            # Store AI recommendation separately (not in model)
            ai_recommendation = costing_result.pop("ai_pricing_recommendation", None)
            
            # Save costing with calculated values
            serializer.save(product=product, **costing_result)
            
            # Store for response
            self.ai_pricing_recommendation = ai_recommendation
            
            logger.info(f"Costing created: product={product_id}, EXW=${costing_result['recommended_exw_price']}")
        except Exception as e:
            logger.error(f"Error calculating costing: {e}", exc_info=True)
            raise
    
    def create(self, request, *args, **kwargs):
        """PBI-BE-M4-03: Response 201 Created dengan full costing result"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_data = serializer.data
        
        # Include AI recommendation in response
        if hasattr(self, "ai_pricing_recommendation") and self.ai_pricing_recommendation:
            response_data["ai_pricing_recommendation"] = self.ai_pricing_recommendation
        
        # Build informative message
        exw = response_data.get("recommended_exw_price")
        fob = response_data.get("recommended_fob_price")
        cif = response_data.get("recommended_cif_price")
        container = response_data.get("container_20ft_capacity")
        
        message_parts = [
            f"Costing calculated successfully!",
            f"EXW: ${exw}, FOB: ${fob}"
        ]
        
        if cif:
            message_parts.append(f"CIF: ${cif}")
        else:
            message_parts.append("(Add 'target_country_code' for CIF calculation)")
        
        if container:
            message_parts.append(f"Container 20ft: {container} units")
        
        message = " | ".join(message_parts)
        
        return created_response(
            data=response_data,
            message=message
        )
    
    def list(self, request, *args, **kwargs):
        """PBI-BE-M4-01: Response array dengan pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Return DRF paginated response (compatible with tests)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CostingDetailView(RetrieveUpdateDestroyAPIView):
    """
    PBI-BE-M4-02, PBI-BE-M4-04, PBI-BE-M4-05
    
    GET: Return detail lengkap costing
    - Include product details
    - Validasi access control
    
    PUT: Update costing inputs
    - Re-trigger calculations
    - Validasi costing untuk product milik user
    
    DELETE: Delete costing by id
    - Validasi access control
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = CostingSerializer
    lookup_url_kwarg = "costing_id"
    
    def get_object(self):
        """Get costing with ownership validation"""
        costing_id = self.kwargs.get(self.lookup_url_kwarg)
        
        try:
            costing = Costing.objects.select_related(
                "product__business__user"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")
        
        # PBI-BE-M4-02: Validasi access control
        user = self.request.user
        if user.role != UserRole.ADMIN and costing.product.business.user.id != user.id:
            raise ForbiddenException("You can only access your own costings")
        
        return costing
    
    def retrieve(self, request, *args, **kwargs):
        """PBI-BE-M4-02: Return detail lengkap costing dengan product details"""
        costing = self.get_object()
        serializer = self.get_serializer(costing)
        
        # Enrich with product details
        data = serializer.data
        data["product_details"] = {
            "id": costing.product.id,
            "name_local": costing.product.name_local,
            "category_id": costing.product.category_id,
            "material_composition": costing.product.material_composition,
            "dimensions_l_w_h": costing.product.dimensions_l_w_h,
            "weight_net": str(costing.product.weight_net),
            "weight_gross": str(costing.product.weight_gross),
            "business": {
                "company_name": costing.product.business.company_name,
                "address": costing.product.business.address,
            }
        }
        
        # Add 40ft container capacity (2.1x of 20ft)
        if costing.container_20ft_capacity:
            data["container_40ft_capacity"] = int(costing.container_20ft_capacity * 2.1)
        
        return Response(data)
    
    def update(self, request, *args, **kwargs):
        """PBI-BE-M4-04: Update costing inputs dan re-trigger calculations"""
        costing = self.get_object()
        serializer = UpdateCostingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update input fields
        costing.cogs_per_unit = serializer.validated_data.get("cogs_per_unit", costing.cogs_per_unit)
        costing.packing_cost = serializer.validated_data.get("packing_cost", costing.packing_cost)
        costing.target_margin_percent = serializer.validated_data.get("target_margin_percent", costing.target_margin_percent)
        
        # Re-trigger calculations
        try:
            costing_result = CostingService.calculate_full_costing(
                product=costing.product,
                cogs_per_unit_idr=costing.cogs_per_unit,
                packing_cost_idr=costing.packing_cost,
                target_margin_percent=costing.target_margin_percent,
                target_country_code=None
            )
            
            # Extract AI recommendation
            ai_recommendation = costing_result.pop("ai_pricing_recommendation", None)
            
            # Update calculated fields
            costing.recommended_exw_price = costing_result["recommended_exw_price"]
            costing.recommended_fob_price = costing_result["recommended_fob_price"]
            costing.recommended_cif_price = costing_result["recommended_cif_price"]
            costing.container_20ft_capacity = costing_result["container_20ft_capacity"]
            costing.optimization_notes = costing_result["optimization_notes"]
            costing.save()
            
            result_serializer = CostingSerializer(costing)
            response_data = result_serializer.data
            
            # Include AI recommendation
            if ai_recommendation:
                response_data["ai_pricing_recommendation"] = ai_recommendation
            
            return success_response(
                data=response_data,
                message="Costing updated successfully with AI recalculations"
            )
        except Exception as e:
            logger.error(f"Error updating costing: {e}", exc_info=True)
            raise
    
    def destroy(self, request, *args, **kwargs):
        """PBI-BE-M4-05: Delete costing by id"""
        costing = self.get_object()
        costing_id = costing.id
        costing.delete()
        
        return success_response(
            data={"id": costing_id},
            message="Costing deleted successfully"
        )


class ExchangeRateView(APIView):
    """
    PBI-BE-M4-11, PBI-BE-M4-12
    
    GET: Get current exchange rate
    - Response: {rate, source, updated_at}
    
    PUT: Update exchange rate (Admin only)
    - Body: rate (decimal)
    - Update stored rate
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """PBI-BE-M4-11: Return current exchange rate IDR-USD"""
        try:
            rate = ExchangeRate.objects.latest("updated_at")
            serializer = ExchangeRateSerializer(rate)
            return success_response(
                data=serializer.data,
                message="Current exchange rate retrieved successfully"
            )
        except ExchangeRate.DoesNotExist:
            # Create default if not exists
            default_rate = ExchangeRate.objects.create(
                rate=Decimal("15800.00"),
                source="default_bootstrap"
            )
            serializer = ExchangeRateSerializer(default_rate)
            return success_response(
                data=serializer.data,
                message="Default exchange rate initialized"
            )
    
    def put(self, request):
        """PBI-BE-M4-12: Manual update exchange rate (Admin only)"""
        if request.user.role != UserRole.ADMIN:
            raise ForbiddenException("Only admins can update exchange rate")
        
        serializer = ExchangeRateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create single exchange rate record
        rate, created = ExchangeRate.objects.get_or_create(
            id=1,
            defaults={
                "rate": serializer.validated_data["rate"],
                "source": serializer.validated_data.get("source", "manual")
            }
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


class CostingPDFExportView(APIView):
    """
    PBI-BE-M4-13: Generate PDF costing report
    
    Include:
    - Company profile
    - Product details
    - Price breakdown (EXW, FOB, CIF)
    - Container info (20ft & 40ft capacity)
    - Professional format untuk buyer
    
    Response: PDF file (application/pdf)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, costing_id):
        """Generate and return PDF costing report"""
        try:
            costing = Costing.objects.select_related(
                "product__business__user"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # PBI-BE-M4-13: Verify ownership
        user = request.user
        if user.role != UserRole.ADMIN and costing.product.business.user.id != user.id:
            raise ForbiddenException("You can only export your own costings")

        try:
            # Generate PDF
            pdf_buffer = CostingPDFService.generate_costing_pdf(
                costing=costing,
                business_profile=costing.product.business,
                product=costing.product,
            )

            # Return PDF file
            response = HttpResponse(
                pdf_buffer.getvalue(),
                content_type="application/pdf",
            )
            filename = f'costing_{costing_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(f"PDF exported: costing_id={costing_id}, user={user.email}")
            return response

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return Response(
                {"success": False, "message": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


