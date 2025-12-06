"""
Views for ExportReady.AI Module 4 - Costing & Financial Calculator

Implements:
# PBI-BE-M4-01: GET /costings - List costings
# PBI-BE-M4-02: GET /costings/:id - Get costing detail
# PBI-BE-M4-03: POST /costings - Create costing
# PBI-BE-M4-04: PUT /costings/:id - Update costing
# PBI-BE-M4-05: DELETE /costings/:id - Delete costing
# PBI-BE-M4-11: GET /exchange-rate - Get current exchange rate
# PBI-BE-M4-12: PUT /exchange-rate - Update exchange rate (Admin)
# PBI-BE-M4-13: GET /costings/:id/pdf - Generate PDF report
"""

import io
import logging
from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import UserRole
from core.exceptions import ForbiddenException, NotFoundException
from core.permissions import IsAdmin
from core.responses import success_response, created_response

from .models import Costing, ExchangeRate
from .serializers import (
    CostingListSerializer,
    CostingDetailSerializer,
    CostingCreateSerializer,
    CostingUpdateSerializer,
    ExchangeRateSerializer,
    ExchangeRateUpdateSerializer,
)
from .services import CostingService

logger = logging.getLogger(__name__)


# ============================================================================
# Exchange Rate Views
# ============================================================================

class ExchangeRateView(APIView):
    """
    # PBI-BE-M4-11: GET /exchange-rate
    Return current exchange rate IDR-USD.
    Response: {rate, source, updated_at}
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        exchange_rate = ExchangeRate.objects.filter(
            currency_from="IDR",
            currency_to="USD"
        ).first()

        if not exchange_rate:
            # Return default rate if none exists
            return success_response(
                data={
                    "rate": "0.000063",
                    "source": "default",
                    "updated_at": None,
                    "currency_from": "IDR",
                    "currency_to": "USD",
                },
                message="Exchange rate retrieved (default)"
            )

        serializer = ExchangeRateSerializer(exchange_rate)
        return success_response(
            data=serializer.data,
            message="Exchange rate retrieved successfully"
        )


class ExchangeRateUpdateView(APIView):
    """
    # PBI-BE-M4-12: PUT /exchange-rate (Admin)
    Manual update exchange rate.
    Body: rate (decimal)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request):
        serializer = ExchangeRateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rate = serializer.validated_data["rate"]

        # Update or create the exchange rate
        exchange_rate, created = ExchangeRate.objects.update_or_create(
            currency_from="IDR",
            currency_to="USD",
            defaults={
                "rate": rate,
                "source": "manual",
            }
        )

        result_serializer = ExchangeRateSerializer(exchange_rate)
        return success_response(
            data=result_serializer.data,
            message="Exchange rate updated successfully"
        )


# ============================================================================
# Costing Views
# ============================================================================

class CostingListView(APIView):
    """
    # PBI-BE-M4-01: GET /costings
    List costings for user or all (admin).

    UMKM: return costings for products owned by user
    Admin: return all costings
    Query params: page, limit, search, sort_by
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == UserRole.ADMIN:
            queryset = Costing.objects.all()
        else:
            # UMKM: only costings for user's products
            queryset = Costing.objects.filter(product__business__user=user)

        # Apply search filter
        search = request.query_params.get("search", "")
        if search:
            queryset = queryset.filter(product__name_local__icontains=search)

        # Apply sorting
        sort_by = request.query_params.get("sort_by", "-created_at")
        if sort_by in ["created_at", "-created_at", "recommended_exw_price", "-recommended_exw_price"]:
            queryset = queryset.order_by(sort_by)

        # Pagination
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        offset = (page - 1) * limit

        total = queryset.count()
        costings = queryset[offset:offset + limit]

        serializer = CostingListSerializer(costings, many=True)

        return success_response(
            data=serializer.data,
            message="Costings retrieved successfully",
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            }
        )


class CostingDetailView(APIView):
    """
    # PBI-BE-M4-02: GET /costings/:id
    Get costing detail.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, costing_id, user):
        try:
            costing = Costing.objects.select_related(
                "product", "product__business"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN:
            if costing.product.business.user_id != user.id:
                raise ForbiddenException("You don't have access to this costing")

        return costing

    def get(self, request, costing_id):
        costing = self.get_object(costing_id, request.user)
        serializer = CostingDetailSerializer(costing)
        return success_response(
            data=serializer.data,
            message="Costing retrieved successfully"
        )


class CostingCreateView(APIView):
    """
    # PBI-BE-M4-03: POST /costings
    Create new costing with AI calculations.

    Body: product_id, cogs_per_unit, packing_cost, target_margin_percent
    Triggers: AI Price Calculation, AI Container Optimizer
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CostingCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]

        # Get business address for trucking estimate
        business_address = ""
        if product.business:
            business_address = product.business.address or ""

        # Get product dimensions and weight
        product_dimensions = product.dimensions_l_w_h or {}
        product_weight = product.weight_gross or Decimal("1.0")

        # Calculate costing using AI services
        costing_service = CostingService()
        calculated_data = costing_service.calculate_full_costing(
            cogs_per_unit=serializer.validated_data["cogs_per_unit"],
            packing_cost=serializer.validated_data["packing_cost"],
            target_margin_percent=serializer.validated_data["target_margin_percent"],
            business_address=business_address,
            target_country_code=serializer.validated_data.get("target_country_code"),
            product_dimensions=product_dimensions,
            product_weight=product_weight,
        )

        # Create costing with calculated values
        costing = Costing.objects.create(
            product=product,
            cogs_per_unit=serializer.validated_data["cogs_per_unit"],
            packing_cost=serializer.validated_data["packing_cost"],
            target_margin_percent=serializer.validated_data["target_margin_percent"],
            **calculated_data
        )

        result_serializer = CostingDetailSerializer(costing)
        return created_response(
            data=result_serializer.data,
            message="Costing created successfully with AI calculations"
        )


class CostingUpdateView(APIView):
    """
    # PBI-BE-M4-04: PUT /costings/:id
    Update costing and recalculate.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, costing_id, user):
        try:
            costing = Costing.objects.select_related(
                "product", "product__business"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN:
            if costing.product.business.user_id != user.id:
                raise ForbiddenException("You don't have access to this costing")

        return costing

    def put(self, request, costing_id):
        costing = self.get_object(costing_id, request.user)

        serializer = CostingUpdateSerializer(
            costing,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Get updated values or existing
        cogs = serializer.validated_data.get("cogs_per_unit", costing.cogs_per_unit)
        packing = serializer.validated_data.get("packing_cost", costing.packing_cost)
        margin = serializer.validated_data.get("target_margin_percent", costing.target_margin_percent)
        target_country = serializer.validated_data.get("target_country_code", costing.target_country_code)

        product = costing.product
        business_address = product.business.address if product.business else ""
        product_dimensions = product.dimensions_l_w_h or {}
        product_weight = product.weight_gross or Decimal("1.0")

        # Recalculate
        costing_service = CostingService()
        calculated_data = costing_service.calculate_full_costing(
            cogs_per_unit=cogs,
            packing_cost=packing,
            target_margin_percent=margin,
            business_address=business_address,
            target_country_code=target_country,
            product_dimensions=product_dimensions,
            product_weight=product_weight,
        )

        # Update costing
        costing.cogs_per_unit = cogs
        costing.packing_cost = packing
        costing.target_margin_percent = margin
        for key, value in calculated_data.items():
            setattr(costing, key, value)
        costing.save()

        result_serializer = CostingDetailSerializer(costing)
        return success_response(
            data=result_serializer.data,
            message="Costing updated successfully"
        )


class CostingDeleteView(APIView):
    """
    # PBI-BE-M4-05: DELETE /costings/:id
    Delete costing.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, costing_id):
        try:
            costing = Costing.objects.select_related(
                "product__business"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # Check ownership for UMKM
        if request.user.role != UserRole.ADMIN:
            if costing.product.business.user_id != request.user.id:
                raise ForbiddenException("You don't have access to this costing")

        costing.delete()
        return success_response(message="Costing deleted successfully")


class CostingPDFView(APIView):
    """
    # PBI-BE-M4-13: GET /costings/:id/pdf
    Generate PDF costing report.

    Include: company profile, product details, price breakdown, container info
    Professional format for buyer
    Response: PDF file (application/pdf)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, costing_id):
        try:
            costing = Costing.objects.select_related(
                "product", "product__business", "product__business__user"
            ).get(id=costing_id)
        except Costing.DoesNotExist:
            raise NotFoundException("Costing not found")

        # Check ownership for UMKM
        if request.user.role != UserRole.ADMIN:
            if costing.product.business.user_id != request.user.id:
                raise ForbiddenException("You don't have access to this costing")

        # Generate PDF
        try:
            pdf_buffer = self._generate_pdf(costing)

            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            filename = f"costing_report_{costing.product.name_local}_{costing.id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return Response(
                {"success": False, "message": f"PDF generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_pdf(self, costing) -> io.BytesIO:
        """Generate PDF report for costing."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            # Fallback to simple text-based PDF if reportlab not available
            return self._generate_simple_pdf(costing)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=1  # Center
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=6,
            spaceBefore=12,
        )
        normal_style = styles['Normal']

        elements = []

        # Title
        elements.append(Paragraph("EXPORT COSTING REPORT", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Company Info
        business = costing.product.business
        elements.append(Paragraph("Company Information", heading_style))
        company_data = [
            ["Company Name:", business.company_name if business else "N/A"],
            ["Address:", business.address if business else "N/A"],
        ]
        company_table = Table(company_data, colWidths=[3*cm, 12*cm])
        company_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(company_table)
        elements.append(Spacer(1, 0.3*cm))

        # Product Info
        product = costing.product
        elements.append(Paragraph("Product Information", heading_style))
        product_data = [
            ["Product Name:", product.name_local],
            ["Category:", str(product.category_id)],
            ["Material:", product.material_composition or "N/A"],
            ["Dimensions:", str(product.dimensions_l_w_h or "N/A")],
            ["Weight (Gross):", f"{product.weight_gross} kg"],
        ]
        product_table = Table(product_data, colWidths=[3*cm, 12*cm])
        product_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(product_table)
        elements.append(Spacer(1, 0.3*cm))

        # Cost Breakdown
        elements.append(Paragraph("Cost Breakdown", heading_style))
        cost_data = [
            ["Description", "Amount (USD)"],
            ["COGS per unit (IDR)", f"IDR {costing.cogs_per_unit:,.2f}"],
            ["Packing cost (IDR)", f"IDR {costing.packing_cost:,.2f}"],
            ["Target Margin", f"{costing.target_margin_percent}%"],
            ["", ""],
            ["EXW Price", f"${costing.recommended_exw_price:,.2f}" if costing.recommended_exw_price else "N/A"],
            ["Trucking Cost", f"${costing.trucking_cost_usd:,.2f}" if costing.trucking_cost_usd else "N/A"],
            ["Document Cost", f"${costing.document_cost_usd:,.2f}" if costing.document_cost_usd else "N/A"],
            ["FOB Price", f"${costing.recommended_fob_price:,.2f}" if costing.recommended_fob_price else "N/A"],
        ]

        if costing.recommended_cif_price:
            cost_data.extend([
                ["Freight Cost", f"${costing.freight_cost_usd:,.2f}" if costing.freight_cost_usd else "N/A"],
                ["Insurance Cost", f"${costing.insurance_cost_usd:,.2f}" if costing.insurance_cost_usd else "N/A"],
                ["CIF Price", f"${costing.recommended_cif_price:,.2f}"],
            ])

        cost_table = Table(cost_data, colWidths=[8*cm, 7*cm])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),  # EXW row
            ('FONTNAME', (0, 8), (0, 8), 'Helvetica-Bold'),  # FOB row
        ]))
        elements.append(cost_table)
        elements.append(Spacer(1, 0.3*cm))

        # Container Information
        elements.append(Paragraph("Container Capacity", heading_style))
        container_data = [
            ["Container Type", "Capacity (units)"],
            ["20ft Container", str(costing.container_20ft_capacity or "N/A")],
            ["40ft Container", str(costing.container_40ft_capacity or "N/A")],
        ]
        container_table = Table(container_data, colWidths=[8*cm, 7*cm])
        container_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(container_table)

        if costing.optimization_notes:
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"<b>Optimization Notes:</b> {costing.optimization_notes}", normal_style))

        # Footer
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph(
            f"Exchange Rate Used: 1 USD = {1/float(costing.exchange_rate_used):,.2f} IDR" if costing.exchange_rate_used else "",
            normal_style
        ))
        elements.append(Paragraph(
            f"Generated by ExportReady.AI | Report ID: {costing.id}",
            ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _generate_simple_pdf(self, costing) -> io.BytesIO:
        """Generate simple text-based PDF if reportlab not available."""
        buffer = io.BytesIO()

        # Simple text content
        content = f"""
EXPORT COSTING REPORT
=====================

Company: {costing.product.business.company_name if costing.product.business else 'N/A'}
Product: {costing.product.name_local}

COST BREAKDOWN
--------------
COGS per unit: IDR {costing.cogs_per_unit:,.2f}
Packing cost: IDR {costing.packing_cost:,.2f}
Target Margin: {costing.target_margin_percent}%

EXW Price: ${costing.recommended_exw_price:,.2f if costing.recommended_exw_price else 'N/A'}
FOB Price: ${costing.recommended_fob_price:,.2f if costing.recommended_fob_price else 'N/A'}
CIF Price: ${costing.recommended_cif_price:,.2f if costing.recommended_cif_price else 'N/A'}

CONTAINER CAPACITY
------------------
20ft: {costing.container_20ft_capacity or 'N/A'} units
40ft: {costing.container_40ft_capacity or 'N/A'} units

Notes: {costing.optimization_notes or 'None'}

Generated by ExportReady.AI
        """

        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer
