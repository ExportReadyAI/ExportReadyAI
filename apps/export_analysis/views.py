"""
Export Analysis Views for ExportReady.AI Module 3

Implements:
# PBI-BE-M3-01: API: GET /export-analysis - List analyses
# PBI-BE-M3-02: API: GET /export-analysis/:id - Get analysis detail
# PBI-BE-M3-03: API: POST /export-analysis - Create new analysis
# PBI-BE-M3-09: API: POST /export-analysis/:id/reanalyze - Re-run analysis
# PBI-BE-M3-10: API: DELETE /export-analysis/:id - Delete analysis
# PBI-BE-M3-11: API: GET /countries - List countries
# PBI-BE-M3-12: API: GET /countries/:code - Get country detail
# PBI-BE-M3-13: API: POST /export-analysis/compare - Multi-country comparison

All acceptance criteria for these PBIs are implemented in this module.
"""

import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product
from apps.users.models import UserRole

from .models import Country, ExportAnalysis
from .serializers import (
    CountryDetailSerializer,
    CountryListSerializer,
    ExportAnalysisCompareSerializer,
    ExportAnalysisCreateSerializer,
    ExportAnalysisDetailSerializer,
    ExportAnalysisListSerializer,
)
from .services import ComplianceAIService

logger = logging.getLogger(__name__)


class ExportAnalysisListView(APIView):
    """
    # PBI-BE-M3-01: API: GET /export-analysis
    #
    # Acceptance Criteria:
    # [DONE] UMKM: return analysis untuk products miliknya
    # [DONE] Admin: return semua analysis
    # [DONE] Query params: page, limit, country_code, score_min, score_max, search
    # [DONE] Include: product name, country name
    # [DONE] Response: array dengan pagination
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Base queryset
        if user.role == UserRole.ADMIN:
            queryset = ExportAnalysis.objects.all()
        else:
            # UMKM: only analyses for their products
            if not hasattr(user, "business_profile"):
                return Response(
                    {"success": False, "message": "Business profile not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = ExportAnalysis.objects.filter(
                product__business=user.business_profile
            )

        # Filter by country_code
        country_code = request.query_params.get("country_code")
        if country_code:
            queryset = queryset.filter(target_country_id=country_code.upper())

        # Filter by score range
        score_min = request.query_params.get("score_min")
        score_max = request.query_params.get("score_max")
        if score_min:
            queryset = queryset.filter(readiness_score__gte=int(score_min))
        if score_max:
            queryset = queryset.filter(readiness_score__lte=int(score_max))

        # Search by product name
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(product__name_local__icontains=search)
                | Q(target_country__country_name__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        offset = (page - 1) * limit
        total = queryset.count()

        analyses = queryset.order_by("-analyzed_at")[offset : offset + limit]
        serializer = ExportAnalysisListSerializer(analyses, many=True)

        return Response(
            {
                "success": True,
                "message": "Export analyses retrieved successfully",
                "data": serializer.data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
            status=status.HTTP_200_OK,
        )


class ExportAnalysisDetailView(APIView):
    """
    # PBI-BE-M3-02: API: GET /export-analysis/:id
    # PBI-BE-M3-10: API: DELETE /export-analysis/:id
    #
    # Acceptance Criteria:
    # [DONE] Return detail lengkap analysis
    # [DONE] Include: product details, country details, compliance_issues, recommendations
    # [DONE] Validasi: UMKM hanya bisa akses analysis untuk product miliknya
    # [DONE] Response: 200 OK atau 403/404
    # [DONE] DELETE: Delete analysis by id
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, analysis_id):
        user = request.user
        analysis = get_object_or_404(ExportAnalysis, id=analysis_id)

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN:
            if not hasattr(user, "business_profile"):
                return Response(
                    {"success": False, "message": "Business profile not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if analysis.product.business_id != user.business_profile.id:
                return Response(
                    {"success": False, "message": "Forbidden"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = ExportAnalysisDetailSerializer(analysis)
        return Response(
            {
                "success": True,
                "message": "Export analysis retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, analysis_id):
        """
        # PBI-BE-M3-10: API: DELETE /export-analysis/:id
        # [DONE] Delete analysis by id
        # [DONE] Validasi: analysis untuk product milik user
        # [DONE] Response: 200 OK
        """
        user = request.user
        analysis = get_object_or_404(ExportAnalysis, id=analysis_id)

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN:
            if not hasattr(user, "business_profile"):
                return Response(
                    {"success": False, "message": "Business profile not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if analysis.product.business_id != user.business_profile.id:
                return Response(
                    {"success": False, "message": "Forbidden"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        analysis.delete()
        return Response(
            {
                "success": True,
                "message": "Export analysis deleted successfully",
            },
            status=status.HTTP_200_OK,
        )


class ExportAnalysisCreateView(APIView):
    """
    # PBI-BE-M3-03: API: POST /export-analysis
    #
    # Acceptance Criteria:
    # [DONE] Body: product_id, target_country_code
    # [DONE] Validasi: product milik user
    # [DONE] Validasi: product sudah punya ProductEnrichment
    # [DONE] Validasi: kombinasi product + country belum ada
    # [DONE] Trigger AI Compliance Checker
    # [DONE] Response: 201 Created dengan analysis result
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExportAnalysisCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        country_code = serializer.validated_data["target_country_code"]

        product = get_object_or_404(Product, id=product_id)
        country = get_object_or_404(Country, country_code=country_code)

        try:
            # Run AI compliance analysis
            logger.info(f"Starting compliance analysis for product {product_id} -> {country_code}")
            ai_service = ComplianceAIService()
            analysis_result = ai_service.analyze_product_compliance(product, country_code)

            # Create ExportAnalysis record
            analysis = ExportAnalysis.objects.create(
                product=product,
                target_country=country,
                readiness_score=analysis_result["readiness_score"],
                status_grade=analysis_result["status_grade"],
                compliance_issues=analysis_result["compliance_issues"],
                recommendations=analysis_result["recommendations"],
            )

            logger.info(f"Compliance analysis completed for product {product_id} -> {country_code}")

            result_serializer = ExportAnalysisDetailSerializer(analysis)
            return Response(
                {
                    "success": True,
                    "message": "Export analysis created successfully",
                    "data": result_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return Response(
                {
                    "success": False,
                    "message": f"Compliance analysis failed: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportAnalysisReanalyzeView(APIView):
    """
    # PBI-BE-M3-09: API: POST /export-analysis/:id/reanalyze
    #
    # Acceptance Criteria:
    # [DONE] Re-run analysis dengan data product terbaru
    # [DONE] Validasi: analysis milik user
    # [DONE] Fetch latest product data
    # [DONE] Re-run semua AI Compliance Checker
    # [DONE] Update: compliance_issues, readiness_score, recommendations, analyzed_at
    # [DONE] Response: 200 OK dengan updated result
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, analysis_id):
        user = request.user
        analysis = get_object_or_404(ExportAnalysis, id=analysis_id)

        # Check ownership for UMKM
        if user.role != UserRole.ADMIN:
            if not hasattr(user, "business_profile"):
                return Response(
                    {"success": False, "message": "Business profile not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if analysis.product.business_id != user.business_profile.id:
                return Response(
                    {"success": False, "message": "Forbidden"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            # Re-fetch latest product data
            product = analysis.product
            product.refresh_from_db()

            # Re-run AI compliance analysis
            logger.info(f"Re-analyzing product {product.id} -> {analysis.target_country_id}")
            ai_service = ComplianceAIService()
            analysis_result = ai_service.analyze_product_compliance(
                product, analysis.target_country_id
            )

            # Update ExportAnalysis record
            analysis.readiness_score = analysis_result["readiness_score"]
            analysis.status_grade = analysis_result["status_grade"]
            analysis.compliance_issues = analysis_result["compliance_issues"]
            analysis.recommendations = analysis_result["recommendations"]
            analysis.save()  # analyzed_at will be auto-updated

            logger.info(f"Re-analysis completed for analysis {analysis_id}")

            result_serializer = ExportAnalysisDetailSerializer(analysis)
            return Response(
                {
                    "success": True,
                    "message": "Export analysis re-analyzed successfully",
                    "data": result_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Re-analysis failed: {e}")
            return Response(
                {
                    "success": False,
                    "message": f"Re-analysis failed: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportAnalysisCompareView(APIView):
    """
    # PBI-BE-M3-13: API: POST /export-analysis/compare
    #
    # Acceptance Criteria:
    # [DONE] Body: product_id, country_codes (array, max 5)
    # [DONE] Run analysis untuk setiap country
    # [DONE] Return comparison data
    # [DONE] Response: array of analysis results
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExportAnalysisCompareSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        country_codes = serializer.validated_data["country_codes"]

        product = get_object_or_404(Product, id=product_id)
        ai_service = ComplianceAIService()

        results = []
        for country_code in country_codes:
            country = get_object_or_404(Country, country_code=country_code)

            try:
                # Check if analysis already exists
                existing = ExportAnalysis.objects.filter(
                    product_id=product_id,
                    target_country_id=country_code,
                ).first()

                if existing:
                    # Use existing analysis
                    analysis = existing
                else:
                    # Run new analysis
                    logger.info(f"Running comparison analysis: {product_id} -> {country_code}")
                    analysis_result = ai_service.analyze_product_compliance(product, country_code)

                    analysis = ExportAnalysis.objects.create(
                        product=product,
                        target_country=country,
                        readiness_score=analysis_result["readiness_score"],
                        status_grade=analysis_result["status_grade"],
                        compliance_issues=analysis_result["compliance_issues"],
                        recommendations=analysis_result["recommendations"],
                    )

                result_serializer = ExportAnalysisDetailSerializer(analysis)
                results.append(result_serializer.data)

            except Exception as e:
                logger.error(f"Comparison analysis failed for {country_code}: {e}")
                results.append(
                    {
                        "country_code": country_code,
                        "error": str(e),
                    }
                )

        return Response(
            {
                "success": True,
                "message": f"Comparison completed for {len(results)} countries",
                "data": results,
            },
            status=status.HTTP_200_OK,
        )


class CountryListView(APIView):
    """
    # PBI-BE-M3-11: API: GET /countries
    #
    # Acceptance Criteria:
    # [DONE] Return list semua countries
    # [DONE] Query params: region, search
    # [DONE] Include: regulations_count
    # [DONE] Response: array of countries
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Country.objects.all()

        # Filter by region
        region = request.query_params.get("region")
        if region:
            queryset = queryset.filter(region__icontains=region)

        # Search by country name or code
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(country_name__icontains=search) | Q(country_code__icontains=search)
            )

        serializer = CountryListSerializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Countries retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class CountryDetailView(APIView):
    """
    # PBI-BE-M3-12: API: GET /countries/:code
    #
    # Acceptance Criteria:
    # [DONE] Return country detail dengan regulations
    # [DONE] Include: semua CountryRegulation grouped by type
    # [DONE] Response: country object dengan nested regulations
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, country_code):
        country = get_object_or_404(Country, country_code=country_code.upper())
        serializer = CountryDetailSerializer(country)
        return Response(
            {
                "success": True,
                "message": "Country retrieved successfully",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
