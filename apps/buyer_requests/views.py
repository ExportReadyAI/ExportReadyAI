"""
Buyer Request Views for ExportReady.AI

Implements:
- PBI-BE-M6-03: POST /buyer-requests
- PBI-BE-M6-04: GET /buyer-requests
- PBI-BE-M6-05: GET /buyer-requests/:id
- PBI-BE-M6-06: PUT /buyer-requests/:id
- PBI-BE-M6-07: PATCH /buyer-requests/:id/status
- PBI-BE-M6-08: DELETE /buyer-requests/:id
- PBI-BE-M6-13: GET /buyer-requests/:id/matched-umkm
"""

import logging
from django.shortcuts import get_object_or_404
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema

from apps.users.models import UserRole
from core.responses import (
    created_response,
    success_response,
    error_response,
    not_found_response,
    forbidden_response,
    validation_error_response,
)
from core.exceptions import NotFoundException, ForbiddenException, ConflictException

from .models import BuyerRequest, BuyerProfile, RequestStatus
from .serializers import (
    BuyerRequestSerializer,
    CreateBuyerRequestSerializer,
    UpdateBuyerRequestSerializer,
    UpdateBuyerRequestStatusSerializer,
    SelectCatalogSerializer,
    MatchedUMSerializer,
    BuyerProfileSerializer,
    CreateBuyerProfileSerializer,
    UpdateBuyerProfileSerializer,
)
from .services import BuyerRequestMatchingService

logger = logging.getLogger(__name__)


class BuyerRequestPagination(PageNumberPagination):
    """Pagination for buyer requests list."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class BuyerRequestListCreateView(APIView):
    """
    PBI-BE-M6-03: POST /buyer-requests
    PBI-BE-M6-04: GET /buyer-requests
    """

    permission_classes = [IsAuthenticated]
    pagination_class = BuyerRequestPagination

    @extend_schema(
        summary="List buyer requests",
        description="Get list of buyer requests. Buyer sees own requests, UMKM sees matching open requests, Admin sees all.",
        responses={200: BuyerRequestSerializer(many=True)},
        tags=["Buyer Requests"],
    )
    def get(self, request):
        """GET /buyer-requests - List buyer requests with role-based filtering."""
        user = request.user
        queryset = BuyerRequest.objects.all()

        # Role-based filtering
        if user.role == UserRole.BUYER:
            # Buyer: return only own requests
            queryset = queryset.filter(buyer_user=user)
        elif user.role == UserRole.UMKM:
            # UMKM: return 'Open' requests matching capabilities
            queryset = queryset.filter(status="Open")
            # Filter by min_rank_required (for now, use certification_count as rank)
            try:
                from apps.business_profiles.models import BusinessProfile
                business_profile = BusinessProfile.objects.get(user=user)
                rank = business_profile.certification_count
                queryset = queryset.filter(min_rank_required__lte=rank)
            except:
                queryset = queryset.none()  # No business profile = no matches
        # Admin: return all (no filter)

        # Query params filtering
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        category_filter = request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(product_category__icontains=category_filter)

        destination_filter = request.query_params.get("destination_country")
        if destination_filter:
            queryset = queryset.filter(destination_country=destination_filter)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BuyerRequestSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BuyerRequestSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="Buyer requests retrieved successfully")

    @extend_schema(
        summary="Create buyer request",
        description="Create a new buyer request. Auto-triggers AI Smart Matching.",
        request=CreateBuyerRequestSerializer,
        responses={201: BuyerRequestSerializer},
        tags=["Buyer Requests"],
    )
    def post(self, request):
        """POST /buyer-requests - Create new buyer request."""
        # Validate user role
        if request.user.role != UserRole.BUYER:
            return forbidden_response("Only Buyer users can create requests")

        serializer = CreateBuyerRequestSerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        buyer_request = serializer.save()

        # Auto-trigger AI Smart Matching (async in background if needed)
        try:
            matching_service = BuyerRequestMatchingService()
            # Store matches (could be done async)
            # For now, matches are calculated on-demand when requested
            logger.info(f"Buyer request {buyer_request.id} created, AI matching will run on-demand")
        except Exception as e:
            logger.error(f"Error in AI matching for request {buyer_request.id}: {e}")

        response_serializer = BuyerRequestSerializer(buyer_request)
        return created_response(
            data=response_serializer.data,
            message="Buyer request created successfully"
        )


class BuyerRequestDetailView(APIView):
    """
    PBI-BE-M6-05: GET /buyer-requests/:id
    PBI-BE-M6-06: PUT /buyer-requests/:id
    PBI-BE-M6-08: DELETE /buyer-requests/:id
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, request_id, user):
        """Get buyer request and validate access."""
        try:
            buyer_request = BuyerRequest.objects.get(id=request_id)
        except BuyerRequest.DoesNotExist:
            raise NotFoundException("Buyer request not found")
        
        # Access control
        if user.role == UserRole.BUYER:
            # Buyer: unlimited access to own requests
            if buyer_request.buyer_user_id != user.id:
                raise ForbiddenException("You can only access your own requests")
        elif user.role == UserRole.UMKM:
            # UMKM: access only if meets min_rank_required
            try:
                from apps.business_profiles.models import BusinessProfile
                business_profile = BusinessProfile.objects.get(user=user)
                rank = business_profile.certification_count
                if buyer_request.min_rank_required > rank:
                    raise ForbiddenException("You do not meet the minimum rank requirement")
            except BusinessProfile.DoesNotExist:
                raise ForbiddenException("Business profile not found")
        # Admin: full access

        return buyer_request

    @extend_schema(
        summary="Get buyer request detail",
        description="Get detailed information about a buyer request.",
        responses={200: BuyerRequestSerializer},
        tags=["Buyer Requests"],
    )
    def get(self, request, request_id):
        """GET /buyer-requests/:id - Get buyer request detail."""
        buyer_request = self.get_object(request_id, request.user)
        serializer = BuyerRequestSerializer(buyer_request)
        return success_response(data=serializer.data, message="Buyer request retrieved successfully")

    @extend_schema(
        summary="Update buyer request",
        description="Update a buyer request. Re-triggers AI Smart Matching if criteria changed.",
        request=UpdateBuyerRequestSerializer,
        responses={200: BuyerRequestSerializer},
        tags=["Buyer Requests"],
    )
    def put(self, request, request_id):
        """PUT /buyer-requests/:id - Update buyer request."""
        buyer_request = self.get_object(request_id, request.user)
        
        # Validate ownership for Buyer
        if request.user.role == UserRole.BUYER and buyer_request.buyer_user_id != request.user.id:
            return forbidden_response("You can only update your own requests")

        serializer = UpdateBuyerRequestSerializer(buyer_request, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        updated_request = serializer.save()

        # Re-trigger AI Smart Matching if criteria changed
        try:
            matching_service = BuyerRequestMatchingService()
            logger.info(f"Buyer request {updated_request.id} updated, AI matching will recalculate on-demand")
        except Exception as e:
            logger.error(f"Error in AI matching for request {updated_request.id}: {e}")

        response_serializer = BuyerRequestSerializer(updated_request)
        return success_response(data=response_serializer.data, message="Buyer request updated successfully")

    @extend_schema(
        summary="Delete buyer request",
        description="Delete a buyer request.",
        responses={204: None},
        tags=["Buyer Requests"],
    )
    def delete(self, request, request_id):
        """DELETE /buyer-requests/:id - Delete buyer request."""
        buyer_request = self.get_object(request_id, request.user)
        
        # Validate ownership for Buyer
        if request.user.role == UserRole.BUYER and buyer_request.buyer_user_id != request.user.id:
            return forbidden_response("You can only delete your own requests")

        request_id = buyer_request.id
        buyer_request.delete()
        return success_response(
            data={"id": request_id},
            message="Buyer request deleted successfully"
        )


class BuyerRequestStatusView(APIView):
    """
    PBI-BE-M6-07: PATCH /buyer-requests/:id/status
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update buyer request status",
        description="Update only the status of a buyer request.",
        request=UpdateBuyerRequestStatusSerializer,
        responses={200: BuyerRequestSerializer},
        tags=["Buyer Requests"],
    )
    def patch(self, request, request_id):
        """PATCH /buyer-requests/:id/status - Update buyer request status."""
        try:
            buyer_request = BuyerRequest.objects.get(id=request_id)
        except BuyerRequest.DoesNotExist:
            return not_found_response("Buyer request not found")

        # Validate ownership
        if request.user.role == UserRole.BUYER and buyer_request.buyer_user_id != request.user.id:
            return forbidden_response("You can only update your own requests")

        serializer = UpdateBuyerRequestStatusSerializer(buyer_request, data=request.data)
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        updated_request = serializer.save()
        response_serializer = BuyerRequestSerializer(updated_request)
        return success_response(data=response_serializer.data, message="Status updated successfully")


class BuyerRequestMatchedUMKMView(APIView):
    """
    PBI-BE-M6-13: GET /buyer-requests/:id/matched-umkm
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get matched catalogs for buyer request",
        description="Get list of matched published catalogs for a buyer request, sorted by match score. Each result includes UMKM info and full catalog details. Multiple catalogs per UMKM are returned if they match.",
        responses={200: MatchedUMSerializer(many=True)},
        tags=["Buyer Requests"],
    )
    def get(self, request, request_id):
        """GET /buyer-requests/:id/matched-umkm - Get matched catalogs with UMKM info."""
        try:
            buyer_request = BuyerRequest.objects.get(id=request_id)
        except BuyerRequest.DoesNotExist:
            return not_found_response("Buyer request not found")

        # Validate ownership for Buyer
        if request.user.role == UserRole.BUYER and buyer_request.buyer_user_id != request.user.id:
            return forbidden_response("You can only view matches for your own requests")

        # Calculate matches (now returns catalogs with UMKM info)
        matching_service = BuyerRequestMatchingService()
        matches = matching_service.match_buyer_request(buyer_request)

        # Enrich with UMKM details
        from apps.users.models import User
        from apps.business_profiles.models import BusinessProfile

        enriched_matches = []
        for match in matches:
            try:
                umkm_user = User.objects.get(id=match["umkm_id"])
                business_profile = BusinessProfile.objects.get(user=umkm_user)
                
                # Build enriched match with catalog details
                enriched_match = {
                    "umkm_id": umkm_user.id,
                    "company_name": business_profile.company_name,
                    "email": umkm_user.email,
                    "full_name": umkm_user.full_name,
                    "match": "match",  # Category match (simplified)
                    "contact_info": {
                        "company_name": business_profile.company_name,
                        "address": business_profile.address,
                    },
                    "catalog": match["catalog"],  # Include full catalog details
                }
                enriched_matches.append(enriched_match)
            except (User.DoesNotExist, BusinessProfile.DoesNotExist):
                continue

        serializer = MatchedUMSerializer(enriched_matches, many=True)
        return success_response(data=serializer.data, message="Matched catalogs retrieved successfully")


class BuyerRequestSelectCatalogView(APIView):
    """
    POST /buyer-requests/:id/select-catalog
    
    Buyer selects a catalog from matched results and closes the request.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Select catalog and close buyer request",
        description="Buyer selects a catalog from matched results. This action updates the request status to 'Closed' and records the selected catalog.",
        request=SelectCatalogSerializer,
        responses={200: BuyerRequestSerializer},
        tags=["Buyer Requests"],
    )
    def post(self, request, request_id):
        """POST /buyer-requests/:id/select-catalog - Select catalog and close request."""
        try:
            buyer_request = BuyerRequest.objects.get(id=request_id)
        except BuyerRequest.DoesNotExist:
            return not_found_response("Buyer request not found")

        # Validate ownership
        if request.user.role == UserRole.BUYER and buyer_request.buyer_user_id != request.user.id:
            return forbidden_response("You can only select catalog for your own requests")

        # Validate catalog_id
        catalog_id = request.data.get("catalog_id")
        if not catalog_id:
            return error_response(message="catalog_id is required", status_code=status.HTTP_400_BAD_REQUEST)

        # Validate catalog exists and is published
        from apps.catalogs.models import ProductCatalog
        try:
            catalog = ProductCatalog.objects.get(id=catalog_id, is_published=True)
        except ProductCatalog.DoesNotExist:
            return not_found_response("Published catalog not found")

        # Update request: set selected catalog and close
        buyer_request.selected_catalog = catalog
        buyer_request.status = RequestStatus.CLOSED
        buyer_request.save()

        # Return updated request
        serializer = BuyerRequestSerializer(buyer_request)
        return success_response(
            data=serializer.data,
            message=f"Catalog selected successfully. Request is now closed."
        )


class BuyerProfilePagination(PageNumberPagination):
    """Pagination for buyer profiles list."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class BuyerProfileCreateView(APIView):
    """
    Create buyer profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create buyer profile",
        description="Create a buyer profile. User must have Buyer role.",
        request=CreateBuyerProfileSerializer,
        responses={201: BuyerProfileSerializer},
        tags=["Buyer Profiles"],
    )
    def post(self, request):
        """POST /buyers/profile - Create buyer profile."""
        # Validate user role
        if request.user.role != UserRole.BUYER:
            return forbidden_response("Only Buyer users can create profiles")

        serializer = CreateBuyerProfileSerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            buyer_profile = serializer.save()
        except ConflictException as e:
            return error_response(str(e), status_code=status.HTTP_409_CONFLICT)

        response_serializer = BuyerProfileSerializer(buyer_profile)
        return created_response(
            data=response_serializer.data,
            message="Buyer profile created successfully"
        )


class BuyerMyProfileView(APIView):
    """
    Get current buyer's own profile.
    Convenience endpoint for buyers to get their profile without knowing the ID.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get my buyer profile",
        description="Get the buyer profile of the currently authenticated buyer user.",
        responses={200: BuyerProfileSerializer},
        tags=["Buyer Profiles"],
    )
    def get(self, request):
        """GET /buyers/profile/me - Get current buyer's own profile."""
        # Validate user role
        if request.user.role != UserRole.BUYER:
            return forbidden_response("Only Buyer users can access this endpoint")

        try:
            buyer_profile = BuyerProfile.objects.get(user=request.user)
        except BuyerProfile.DoesNotExist:
            return not_found_response("Buyer profile not found. Please create your profile first.")

        serializer = BuyerProfileSerializer(buyer_profile)
        return success_response(data=serializer.data, message="Buyer profile retrieved successfully")


class BuyerProfileUpdateView(APIView):
    """
    Update buyer profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update buyer profile",
        description="Update a buyer profile. Only the owner can update.",
        request=UpdateBuyerProfileSerializer,
        responses={200: BuyerProfileSerializer},
        tags=["Buyer Profiles"],
    )
    def put(self, request, profile_id):
        """PUT /buyers/profile/:id - Update buyer profile."""
        try:
            buyer_profile = BuyerProfile.objects.get(id=profile_id)
        except BuyerProfile.DoesNotExist:
            return not_found_response("Buyer profile not found")

        # Validate ownership
        if request.user.role != UserRole.ADMIN and buyer_profile.user_id != request.user.id:
            return forbidden_response("You can only update your own profile")

        serializer = UpdateBuyerProfileSerializer(buyer_profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        updated_profile = serializer.save()
        response_serializer = BuyerProfileSerializer(updated_profile)
        return success_response(data=response_serializer.data, message="Profile updated successfully")


class BuyerListView(APIView):
    """
    List buyer profiles with filters.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = BuyerProfilePagination

    @extend_schema(
        summary="List buyer profiles",
        description="Get list of buyer profiles with filters and sorting. Available to all authenticated users.",
        responses={200: BuyerProfileSerializer(many=True)},
        tags=["Buyer Profiles"],
    )
    def get(self, request):
        """GET /buyers - List buyer profiles with filters."""
        # All authenticated users can view buyer profiles

        queryset = BuyerProfile.objects.all()

        # Query params filtering
        product_category = request.query_params.get("product_category")
        if product_category:
            queryset = queryset.filter(preferred_product_categories__contains=[product_category])

        source_country = request.query_params.get("source_country")
        if source_country:
            queryset = queryset.filter(source_countries__contains=[source_country])

        business_type = request.query_params.get("business_type")
        if business_type:
            queryset = queryset.filter(business_type__icontains=business_type)

        # Search by company name
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(company_name__icontains=search)

        # Sorting
        sort_by = request.query_params.get("sort", "company_name")
        if sort_by == "company_name":
            queryset = queryset.order_by("company_name")
        elif sort_by == "created_at":
            queryset = queryset.order_by("-created_at")

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BuyerProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BuyerProfileSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="Buyer profiles retrieved successfully")


class BuyerDetailView(APIView):
    """
    Get buyer profile detail.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get buyer profile detail",
        description="Get detailed information about a buyer profile.",
        responses={200: BuyerProfileSerializer},
        tags=["Buyer Profiles"],
    )
    def get(self, request, buyer_id):
        """GET /buyers/:id - Get buyer profile detail."""
        try:
            buyer_profile = BuyerProfile.objects.get(id=buyer_id)
        except BuyerProfile.DoesNotExist:
            return not_found_response("Buyer profile not found")

        serializer = BuyerProfileSerializer(buyer_profile)
        return success_response(data=serializer.data, message="Buyer profile retrieved successfully")

