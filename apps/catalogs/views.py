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


# ============================================================
# AI FEATURE VIEWS
# ============================================================


class CatalogAIDescriptionView(APIView):
    """
    POST: Generate international product descriptions using AI

    AI 1: International Product Description Generator
    - Export Buyer Description (English B2B)
    - Technical Specification Sheet
    - Material/Food Safety Sheet
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, catalog_id):
        """Generate AI descriptions for a catalog"""
        # Get catalog with ownership check
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )

        product = catalog.product

        # Check if product is food
        is_food = request.data.get("is_food_product", False)

        try:
            from .services import get_catalog_ai_service
            ai_service = get_catalog_ai_service()

            result = ai_service.generate_international_description(
                product_name=product.name_local,
                description_local=product.description_local or "",
                material_composition=product.material_composition or "",
                dimensions=product.dimensions_l_w_h,
                weight_net=float(product.weight_net) if product.weight_net else None,
                weight_gross=float(product.weight_gross) if product.weight_gross else None,
                category=str(product.category_id) if product.category_id else "",
                is_food_product=is_food,
            )

            if result.get("success"):
                return Response({
                    "success": True,
                    "message": "International descriptions generated successfully",
                    "data": result["data"]
                })
            else:
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to generate descriptions")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error generating AI descriptions: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CatalogMarketIntelligenceView(APIView):
    """
    GET: Get existing market intelligence
    POST: Generate market intelligence for a catalog product (only if not exists)

    AI 2: Market Intelligence
    - Recommended target countries
    - Countries to avoid
    - Market trends and insights

    Note: Each catalog can only have ONE market intelligence result.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """Get existing market intelligence for a catalog"""
        from .models import CatalogMarketIntelligence

        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        try:
            mi = catalog.market_intelligence
            return Response({
                "success": True,
                "message": "Market intelligence retrieved",
                "data": {
                    "id": mi.id,
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
        except CatalogMarketIntelligence.DoesNotExist:
            return Response({
                "success": False,
                "message": "Market intelligence not yet generated for this catalog. Use POST to generate."
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, catalog_id):
        """Generate market intelligence for a catalog (only if not exists)"""
        from .models import CatalogMarketIntelligence

        # Get catalog with ownership check
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product__business"),
            id=catalog_id,
            product__business__user=request.user,
        )

        # Check if market intelligence already exists
        if hasattr(catalog, 'market_intelligence'):
            return Response({
                "success": False,
                "message": "Market intelligence already exists for this catalog. Each catalog can only have one market intelligence result.",
                "existing_data": {
                    "id": catalog.market_intelligence.id,
                    "generated_at": catalog.market_intelligence.generated_at,
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        product = catalog.product
        business = product.business

        try:
            from .services import get_catalog_ai_service
            ai_service = get_catalog_ai_service()

            result = ai_service.get_market_intelligence(
                product_name=product.name_local,
                description=catalog.marketing_description or product.description_local or "",
                material_composition=product.material_composition or "",
                category=str(product.category_id) if product.category_id else "",
                current_price_usd=float(catalog.base_price_exw) if catalog.base_price_exw else None,
                production_capacity=business.production_capacity_per_month if business else None,
            )

            if result.get("success"):
                data = result["data"]

                # Save to database
                mi = CatalogMarketIntelligence.objects.create(
                    catalog=catalog,
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
                    "message": "Market intelligence generated and saved successfully",
                    "data": {
                        "id": mi.id,
                        **data,
                        "generated_at": mi.generated_at,
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to generate market intelligence")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error getting market intelligence: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CatalogPricingView(APIView):
    """
    GET: Get existing pricing result
    POST: Generate pricing recommendations for catalog (only if not exists)

    AI 3: Catalog Pricing (reuses costing module)
    - EXW/FOB/CIF pricing
    - AI pricing insights

    Note: Each catalog can only have ONE pricing result.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, catalog_id):
        """Get existing pricing result for a catalog"""
        from .models import CatalogPricingResult

        catalog = get_object_or_404(
            ProductCatalog,
            id=catalog_id,
            product__business__user=request.user,
        )

        try:
            pr = catalog.pricing_result
            return Response({
                "success": True,
                "message": "Pricing result retrieved",
                "data": {
                    "id": pr.id,
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
        except CatalogPricingResult.DoesNotExist:
            return Response({
                "success": False,
                "message": "Pricing not yet generated for this catalog. Use POST to generate."
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, catalog_id):
        """Generate pricing for a catalog (only if not exists)"""
        from decimal import Decimal
        from .models import CatalogPricingResult

        # Get catalog with ownership check
        catalog = get_object_or_404(
            ProductCatalog.objects.select_related("product"),
            id=catalog_id,
            product__business__user=request.user,
        )

        # Check if pricing already exists
        if hasattr(catalog, 'pricing_result'):
            return Response({
                "success": False,
                "message": "Pricing result already exists for this catalog. Each catalog can only have one pricing result.",
                "existing_data": {
                    "id": catalog.pricing_result.id,
                    "exw_price_usd": float(catalog.pricing_result.exw_price_usd),
                    "generated_at": catalog.pricing_result.generated_at,
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        product = catalog.product

        # Get pricing inputs from request
        cogs_per_unit = request.data.get("cogs_per_unit")
        target_margin = request.data.get("target_margin_percent", 30)
        target_country = request.data.get("target_country_code")

        if not cogs_per_unit:
            return Response({
                "success": False,
                "message": "cogs_per_unit is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .services import get_catalog_ai_service
            ai_service = get_catalog_ai_service()

            result = ai_service.generate_catalog_pricing(
                product_name=product.name_local,
                cogs_per_unit=Decimal(str(cogs_per_unit)),
                target_margin_percent=Decimal(str(target_margin)),
                material_composition=product.material_composition or "",
                target_country_code=target_country,
                dimensions=product.dimensions_l_w_h,
                weight_gross=float(product.weight_gross) if product.weight_gross else None,
            )

            if result.get("success"):
                data = result["data"]

                # Save to database
                pr = CatalogPricingResult.objects.create(
                    catalog=catalog,
                    cogs_per_unit_idr=Decimal(str(data["cogs_per_unit_idr"])),
                    target_margin_percent=Decimal(str(data["target_margin_percent"])),
                    target_country_code=target_country or "",
                    exchange_rate_used=Decimal(str(data["exchange_rate_used"])),
                    exw_price_usd=Decimal(str(data["exw_price_usd"])),
                    fob_price_usd=Decimal(str(data["fob_price_usd"])),
                    cif_price_usd=Decimal(str(data["cif_price_usd"])) if data.get("cif_price_usd") else None,
                    pricing_insight=data.get("pricing_insight", ""),
                    pricing_breakdown=data.get("pricing_breakdown", {}),
                )

                # Update catalog prices
                catalog.base_price_exw = pr.exw_price_usd
                catalog.base_price_fob = pr.fob_price_usd
                if pr.cif_price_usd:
                    catalog.base_price_cif = pr.cif_price_usd
                catalog.save()

                return Response({
                    "success": True,
                    "message": "Pricing calculated and saved successfully. Catalog prices updated.",
                    "data": {
                        "id": pr.id,
                        **data,
                        "generated_at": pr.generated_at,
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": result.get("error", "Failed to calculate pricing")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error generating pricing: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
