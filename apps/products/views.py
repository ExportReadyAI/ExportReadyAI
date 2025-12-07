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
from apps.catalogs.models import ProductMarketIntelligence, ProductPricingResult
from apps.catalogs.services import CatalogAIService
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
        product_id = instance.id
        self.perform_destroy(instance)
        from core.responses import success_response
        return success_response(
            data={"id": product_id},
            message="Product deleted successfully"
        )


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

            # Update enrichment record (hanya HS Code dan SKU)
            enrichment.hs_code_recommendation = enrichment_data["hs_code_recommendation"]
            enrichment.sku_generated = enrichment_data["sku_generated"]
            enrichment.last_updated_ai = timezone.now()
            enrichment.save()

            logger.info(f"AI enrichment completed for product {product_id}")
            logger.info(f"HS Code: {enrichment_data['hs_code_recommendation']} (from_ai: {enrichment_data['hs_code_from_ai']})")

            serializer = ProductEnrichmentSerializer(enrichment)
            response_data = serializer.data
            # Add status apakah HS code dari AI atau fallback
            response_data["hs_code_from_ai"] = enrichment_data["hs_code_from_ai"]
            
            return Response(
                {
                    "success": True,
                    "message": "Product enriched successfully with AI",
                    "data": response_data
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


class ProductMarketIntelligenceView(APIView):
    """
    AI Market Intelligence for a product.
    GET: Retrieve existing market intelligence
    POST: Generate new market intelligence (only once per product)
    """
    permission_classes = [IsAuthenticated]

    def get_product(self, product_id, user):
        """Get product with ownership validation"""
        product = get_object_or_404(Product, id=product_id)
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            return None
        return product

    def get(self, request, product_id):
        product = self.get_product(product_id, request.user)
        if not product:
            return Response(
                {"success": False, "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(product, 'market_intelligence'):
            mi = product.market_intelligence
            return Response({
                "success": True,
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
                    "generated_at": mi.generated_at
                }
            })

        return Response({
            "success": False,
            "message": "Market intelligence not yet generated for this product"
        }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, product_id):
        product = self.get_product(product_id, request.user)
        if not product:
            return Response(
                {"success": False, "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already exists
        if hasattr(product, 'market_intelligence'):
            return Response({
                "success": False,
                "message": "Market intelligence already exists for this product. Use GET to retrieve it."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get enrichment for HS code
        hs_code = None
        if hasattr(product, 'enrichment') and product.enrichment:
            hs_code = product.enrichment.hs_code_recommendation

        # Get optional parameters
        current_price_usd = request.data.get("current_price_usd")
        production_capacity = request.data.get("production_capacity")

        try:
            # Use the same KolosalAIService that works for product enrich
            ai_service = KolosalAIService()
            result = ai_service.get_market_intelligence(
                product_name=product.name_local,
                description=product.description_local,
                material_composition=product.material_composition,
                category=str(product.category_id) if product.category_id else "",
                current_price_usd=current_price_usd,
                production_capacity=production_capacity
            )

            if not result.get("success"):
                logger.error(f"Market intelligence generation failed: {result.get('error')}")
                logger.error(f"Raw response: {result.get('raw_response', 'N/A')}")
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to generate market intelligence")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = result.get("data")
            if not data:
                logger.error("Market intelligence result has no data")
                return Response({
                    "success": False,
                    "message": "AI returned empty data"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logger.info(f"Market intelligence data received, saving to database...")
            logger.debug(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

            # Save to database
            try:
                mi = ProductMarketIntelligence.objects.create(
                    product=product,
                    recommended_countries=data.get("recommended_countries", []),
                    countries_to_avoid=data.get("countries_to_avoid", []),
                    market_trends=data.get("market_trends", []),
                    competitive_landscape=data.get("competitive_landscape", ""),
                    growth_opportunities=data.get("growth_opportunities", []),
                    risks_and_challenges=data.get("risks_and_challenges", []),
                    overall_recommendation=data.get("overall_recommendation", "")
                )
                logger.info(f"Market intelligence saved to database with ID: {mi.id}")
            except Exception as db_error:
                logger.error(f"Error saving market intelligence to database: {db_error}", exc_info=True)
                return Response({
                    "success": False,
                    "message": f"Failed to save market intelligence: {str(db_error)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Build response - ensure datetime is serialized properly
            try:
                from django.utils import timezone
                response_data = {
                    "id": mi.id,
                    "product_id": product.id,
                    "recommended_countries": mi.recommended_countries,
                    "countries_to_avoid": mi.countries_to_avoid,
                    "market_trends": mi.market_trends,
                    "competitive_landscape": mi.competitive_landscape,
                    "growth_opportunities": mi.growth_opportunities,
                    "risks_and_challenges": mi.risks_and_challenges,
                    "overall_recommendation": mi.overall_recommendation,
                    "generated_at": mi.generated_at.isoformat() if mi.generated_at else None
                }
                logger.info(f"Returning success response for market intelligence ID: {mi.id}")
                logger.debug(f"Response data keys: {list(response_data.keys())}")
                return Response({
                    "success": True,
                    "message": "Market intelligence generated and saved",
                    "data": response_data
                }, status=status.HTTP_201_CREATED)
            except Exception as response_error:
                logger.error(f"Error building response: {response_error}", exc_info=True)
                # Even if response fails, data is saved, so return it
                return Response({
                    "success": True,
                    "message": "Market intelligence generated and saved (response formatting issue)",
                    "data": {
                        "id": mi.id,
                        "product_id": product.id
                    }
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductCatalogDescriptionView(APIView):
    """
    AI Catalog Description Generator for a product.

    POST: Generate catalog description recommendations BEFORE creating a catalog.

    This endpoint reads Product data and generates AI recommendations for:
    - export_description: Marketing description for international buyers (B2B)
    - technical_specs: Technical specification sheet
    - safety_info: Material/Food safety information

    The response is NOT saved - it's just recommendations for the user to review
    and optionally use when creating a catalog.

    Request body (optional):
    - is_food_product: bool (default: false) - affects safety_info content

    Response:
    - success: true
    - data:
      - export_description: string (marketing B2B description)
      - technical_specs: object (technical specification sheet)
      - safety_info: object (material/food safety information)
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

        # Get optional parameters - auto-detect food product from name/description
        is_food_product = request.data.get("is_food_product", None)
        if is_food_product is None:
            # Auto-detect food product from keywords
            food_keywords = ['makanan', 'minuman', 'food', 'snack', 'kopi', 'coffee', 'teh', 'tea',
                           'keripik', 'kue', 'sambal', 'bumbu', 'rempah', 'mie', 'noodle', 'rice',
                           'beras', 'gula', 'sugar', 'madu', 'honey', 'coklat', 'chocolate', 'kacang',
                           'singkong', 'cassava', 'pisang', 'banana', 'buah', 'fruit', 'sayur', 'vegetable']
            combined_text = f"{product.name_local} {product.description_local}".lower()
            is_food_product = any(kw in combined_text for kw in food_keywords)
            logger.info(f"Auto-detected is_food_product={is_food_product} for: {product.name_local}")

        try:
            # Use CatalogAIService to generate descriptions
            ai_service = CatalogAIService()

            # Prepare dimensions
            dimensions = product.dimensions_l_w_h if product.dimensions_l_w_h else None

            logger.info(f"Generating catalog description for product {product_id}: {product.name_local}")

            result = ai_service.generate_international_description(
                product_name=product.name_local,
                description_local=product.description_local,
                material_composition=product.material_composition,
                dimensions=dimensions,
                weight_net=float(product.weight_net) if product.weight_net else None,
                weight_gross=float(product.weight_gross) if product.weight_gross else None,
                category=str(product.category_id) if product.category_id else "",
                is_food_product=is_food_product,
            )

            logger.info(f"AI result: success={result.get('success')}, has_data={bool(result.get('data'))}")

            if not result.get("success"):
                logger.error(f"Catalog description generation failed: {result.get('error')}")
                raw_response = result.get("raw_response", "")
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to generate catalog description"),
                    "debug": raw_response[:500] if raw_response else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = result.get("data", {})

            # Log what we got
            logger.info(f"AI data keys: {list(data.keys()) if data else 'empty'}")

            # Map the AI response to catalog-friendly field names
            response_data = {
                "export_description": data.get("export_buyer_description", ""),
                "technical_specs": data.get("technical_spec_sheet", {}),
                "safety_info": data.get("safety_sheet", {}),
                "product_info": {
                    "id": product.id,
                    "name": product.name_local,
                    "description_local": product.description_local,
                    "material_composition": product.material_composition,
                },
                "is_food_product": is_food_product
            }

            logger.info(f"Catalog description generated for product {product_id}")

            return Response({
                "success": True,
                "message": "Catalog description recommendations generated. Review and use when creating your catalog.",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating catalog description for product {product_id}: {e}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductPricingView(APIView):
    """
    AI Pricing Calculator for a product.
    GET: Retrieve existing pricing result
    POST: Generate new pricing (only once per product)
    """
    permission_classes = [IsAuthenticated]

    def get_product(self, product_id, user):
        """Get product with ownership validation"""
        product = get_object_or_404(Product, id=product_id)
        if user.role != UserRole.ADMIN and product.business.user_id != user.id:
            return None
        return product

    def get(self, request, product_id):
        product = self.get_product(product_id, request.user)
        if not product:
            return Response(
                {"success": False, "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        if hasattr(product, 'pricing_result'):
            pr = product.pricing_result
            return Response({
                "success": True,
                "data": {
                    "id": pr.id,
                    "product_id": product.id,
                    "cogs_per_unit_idr": pr.cogs_per_unit_idr,
                    "target_margin_percent": pr.target_margin_percent,
                    "target_country_code": pr.target_country_code,
                    "exchange_rate_used": pr.exchange_rate_used,
                    "exw_price_usd": pr.exw_price_usd,
                    "fob_price_usd": pr.fob_price_usd,
                    "cif_price_usd": pr.cif_price_usd,
                    "pricing_insight": pr.pricing_insight,
                    "pricing_breakdown": pr.pricing_breakdown,
                    "generated_at": pr.generated_at
                }
            })

        return Response({
            "success": False,
            "message": "Pricing not yet generated for this product"
        }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, product_id):
        product = self.get_product(product_id, request.user)
        if not product:
            return Response(
                {"success": False, "message": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already exists
        if hasattr(product, 'pricing_result'):
            return Response({
                "success": False,
                "message": "Pricing already exists for this product. Use GET to retrieve it."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate required fields
        cogs_per_unit_idr = request.data.get("cogs_per_unit_idr")
        target_margin_percent = request.data.get("target_margin_percent")
        target_country_code = request.data.get("target_country_code", "US")

        if not cogs_per_unit_idr:
            return Response({
                "success": False,
                "message": "cogs_per_unit_idr is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not target_margin_percent:
            return Response({
                "success": False,
                "message": "target_margin_percent is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            ai_service = CatalogAIService()
            result = ai_service.generate_catalog_pricing(
                product_name=product.name_local,
                cogs_per_unit=float(cogs_per_unit_idr),
                target_margin_percent=float(target_margin_percent),
                material_composition=product.material_composition,
                target_country_code=target_country_code,
                weight_gross=float(product.weight_gross) if product.weight_gross else 1.0
            )

            if not result.get("success"):
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to generate pricing")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = result["data"]

            # Save to database
            pr = ProductPricingResult.objects.create(
                product=product,
                cogs_per_unit_idr=cogs_per_unit_idr,
                target_margin_percent=target_margin_percent,
                target_country_code=target_country_code,
                exchange_rate_used=data.get("exchange_rate_used"),
                exw_price_usd=data.get("exw_price_usd"),
                fob_price_usd=data.get("fob_price_usd"),
                cif_price_usd=data.get("cif_price_usd"),
                pricing_insight=data.get("pricing_insight", ""),
                pricing_breakdown=data.get("pricing_breakdown", {})
            )

            return Response({
                "success": True,
                "message": "Pricing generated and saved",
                "data": {
                    "id": pr.id,
                    "product_id": product.id,
                    "cogs_per_unit_idr": pr.cogs_per_unit_idr,
                    "target_margin_percent": pr.target_margin_percent,
                    "target_country_code": pr.target_country_code,
                    "exchange_rate_used": pr.exchange_rate_used,
                    "exw_price_usd": pr.exw_price_usd,
                    "fob_price_usd": pr.fob_price_usd,
                    "cif_price_usd": pr.cif_price_usd,
                    "pricing_insight": pr.pricing_insight,
                    "pricing_breakdown": pr.pricing_breakdown,
                    "generated_at": pr.generated_at
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error generating pricing: {e}")
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
