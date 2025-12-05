"""
BusinessProfile Views for ExportReady.AI

Implements:
- PBI-BE-M1-04: POST /business-profile - Create business profile (UMKM only)
- PBI-BE-M1-05: GET /business-profile - Get profile(s) with role-based access
- PBI-BE-M1-06: PUT /business-profile/:id - Update business profile
- PBI-BE-M1-07: PATCH /business-profile/:id/certifications - Update certifications
- PBI-BE-M1-12: GET /dashboard/summary - Dashboard statistics

All acceptance criteria for these PBIs are implemented in this module.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.users.models import User, UserRole
from core.exceptions import ConflictException, ForbiddenException, NotFoundException
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdminOrUMKM, IsUMKM
from core.responses import created_response, error_response, success_response

from .models import BusinessProfile
from .serializers import (
    BusinessProfileSerializer,
    CreateBusinessProfileSerializer,
    UpdateBusinessProfileSerializer,
    UpdateCertificationsSerializer,
)


class BusinessProfileListCreateView(APIView):
    """
    API endpoint for listing and creating business profiles.

    # PBI-BE-M1-04 (POST): Create a new business profile
    # - Accepts: company_name, address, production_capacity_per_month, year_established
    # - Validates: user belum memiliki profile (1-to-1), semua field wajib
    # - Auto-assign user_id dari token, default certifications = []
    # - Response: 201 Created / 400 Bad Request / 409 Conflict

    # PBI-BE-M1-05 (GET): List/Get business profiles
    # - UMKM: return own profile only
    # - Admin: return all profiles with pagination, can filter by user_id
    # - Response: 200 OK / 404 Not Found
    """

    permission_classes = [IsAuthenticated, IsAdminOrUMKM]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="Get business profile(s)",
        description="""
        - UMKM: Returns their own business profile
        - Admin: Returns all profiles with pagination, can filter by user_id
        """,
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number (Admin only)"),
            OpenApiParameter(name="limit", type=int, description="Items per page (Admin only)"),
            OpenApiParameter(name="user_id", type=int, description="Filter by user_id (Admin only)"),
        ],
        responses={
            200: BusinessProfileSerializer,
            404: {"description": "Profile not found (UMKM)"},
        },
        tags=["Business Profile"],
    )
    def get(self, request):
        user = request.user

        # UMKM: Return only their own profile
        if user.role == UserRole.UMKM:
            try:
                profile = BusinessProfile.objects.select_related("user").get(user=user)
            except BusinessProfile.DoesNotExist:
                raise NotFoundException("Business profile not found. Please create one first.")

            serializer = BusinessProfileSerializer(profile)
            return success_response(
                data=serializer.data,
                message="Business profile retrieved successfully",
            )

        # Admin: Return all profiles with pagination
        queryset = BusinessProfile.objects.select_related("user").all()

        # Filter by user_id if provided
        user_id = request.query_params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = BusinessProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BusinessProfileSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    @extend_schema(
        summary="Create business profile",
        description="""
        Create a new business profile for the authenticated UMKM user.
        Each user can only have one business profile.
        """,
        request=CreateBusinessProfileSerializer,
        responses={
            201: BusinessProfileSerializer,
            400: {"description": "Validation error"},
            409: {"description": "Profile already exists"},
        },
        tags=["Business Profile"],
    )
    def post(self, request):
        user = request.user

        # Check if user is UMKM
        if user.role != UserRole.UMKM:
            raise ForbiddenException("Only UMKM users can create business profiles")

        # Check if user already has a profile
        if BusinessProfile.objects.filter(user=user).exists():
            return error_response(
                message="You already have a business profile",
                status_code=status.HTTP_409_CONFLICT,
            )

        serializer = CreateBusinessProfileSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        profile = serializer.save()
        response_serializer = BusinessProfileSerializer(profile)

        return created_response(
            data=response_serializer.data,
            message="Business profile created successfully",
        )


class BusinessProfileDetailView(APIView):
    """
    API endpoint for updating a specific business profile.

    # PBI-BE-M1-06: PUT /business-profile/:id
    # - Accepts: company_name, address, production_capacity_per_month, year_established
    # - Validates: profile_id milik user yang login, semua field valid
    # - Update hanya field yang dikirim
    # - Response: 200 OK / 400 Bad Request / 403 Forbidden / 404 Not Found
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    def get_object(self, profile_id, user):
        """Get business profile and verify ownership."""
        try:
            profile = BusinessProfile.objects.select_related("user").get(id=profile_id)
        except BusinessProfile.DoesNotExist:
            raise NotFoundException("Business profile not found")

        # Verify ownership (UMKM can only update their own profile)
        if profile.user_id != user.id:
            raise ForbiddenException("You can only update your own business profile")

        return profile

    @extend_schema(
        summary="Update business profile",
        description="Update a business profile. UMKM can only update their own profile.",
        request=UpdateBusinessProfileSerializer,
        responses={
            200: BusinessProfileSerializer,
            400: {"description": "Validation error"},
            403: {"description": "Forbidden - not your profile"},
            404: {"description": "Profile not found"},
        },
        tags=["Business Profile"],
    )
    def put(self, request, profile_id):
        profile = self.get_object(profile_id, request.user)

        serializer = UpdateBusinessProfileSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_profile = serializer.update(profile, serializer.validated_data)
        response_serializer = BusinessProfileSerializer(updated_profile)

        return success_response(
            data=response_serializer.data,
            message="Business profile updated successfully",
        )


class BusinessProfileCertificationsView(APIView):
    """
    API endpoint for updating certifications.

    # PBI-BE-M1-07: PATCH /business-profile/:id/certifications
    # - Accepts: certifications (array of strings)
    # - Validates: nilai hanya boleh ["Halal", "ISO", "HACCP", "SVLK"]
    # - Validates: profile_id milik user yang login
    # - Update field certifications (replace entire array)
    # - Response: 200 OK dengan updated certifications
    """

    permission_classes = [IsAuthenticated, IsUMKM]

    def get_object(self, profile_id, user):
        """Get business profile and verify ownership."""
        try:
            profile = BusinessProfile.objects.get(id=profile_id)
        except BusinessProfile.DoesNotExist:
            raise NotFoundException("Business profile not found")

        # Verify ownership
        if profile.user_id != user.id:
            raise ForbiddenException("You can only update your own business profile")

        return profile

    @extend_schema(
        summary="Update certifications",
        description="""
        Update business profile certifications.
        Valid values: ["Halal", "ISO", "HACCP", "SVLK"]
        """,
        request=UpdateCertificationsSerializer,
        responses={
            200: BusinessProfileSerializer,
            400: {"description": "Validation error"},
            403: {"description": "Forbidden - not your profile"},
            404: {"description": "Profile not found"},
        },
        tags=["Business Profile"],
    )
    def patch(self, request, profile_id):
        profile = self.get_object(profile_id, request.user)

        serializer = UpdateCertificationsSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_profile = serializer.update(profile, serializer.validated_data)
        response_serializer = BusinessProfileSerializer(updated_profile)

        return success_response(
            data={"certifications": response_serializer.data["certifications"]},
            message="Certifications updated successfully",
        )


class DashboardSummaryView(APIView):
    """
    API endpoint for dashboard summary.

    # PBI-BE-M1-12: GET /dashboard/summary
    # - Return summary counts untuk dashboard
    # - UMKM: product_count, analysis_count, costing_count (milik sendiri)
    # - Admin: total_users, total_products, total_analysis
    # - Include: has_business_profile (boolean)
    # - Response: 200 OK dengan summary object
    """

    permission_classes = [IsAuthenticated, IsAdminOrUMKM]

    @extend_schema(
        summary="Get dashboard summary",
        description="""
        Get summary counts for the dashboard.
        - UMKM: Returns counts for their own resources
        - Admin: Returns system-wide counts
        """,
        responses={200: {"description": "Summary object"}},
        tags=["Dashboard"],
    )
    def get(self, request):
        user = request.user

        if user.role == UserRole.UMKM:
            # UMKM summary
            has_business_profile = BusinessProfile.objects.filter(user=user).exists()

            summary = {
                "product_count": 0,  # Will be updated when Product model is added
                "analysis_count": 0,  # Will be updated when ExportAnalysis model is added
                "costing_count": 0,  # Will be updated when Costing model is added
                "has_business_profile": has_business_profile,
            }
        else:
            # Admin summary
            total_users = User.objects.count()
            total_umkm = User.objects.filter(role=UserRole.UMKM).count()
            total_business_profiles = BusinessProfile.objects.count()

            summary = {
                "total_users": total_users,
                "total_umkm": total_umkm,
                "total_business_profiles": total_business_profiles,
                "total_products": 0,  # Will be updated when Product model is added
                "total_analysis": 0,  # Will be updated when ExportAnalysis model is added
            }

        return success_response(
            data=summary,
            message="Dashboard summary retrieved successfully",
        )

