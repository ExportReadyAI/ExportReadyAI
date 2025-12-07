"""
Forwarder Views for ExportReady.AI

Implements:
- PBI-BE-M6-16: POST /forwarder-profile
- PBI-BE-M6-17: GET /forwarders
- PBI-BE-M6-18: GET /forwarders/:id
- PBI-BE-M6-19: PUT /forwarder-profile/:id
- PBI-BE-M6-20: POST /forwarders/:id/reviews
- PBI-BE-M6-21: PUT /forwarders/:forwarder_id/reviews/:review_id
- PBI-BE-M6-22: DELETE /forwarders/:forwarder_id/reviews/:review_id
- PBI-BE-M6-25: GET /forwarders/recommendations
- PBI-BE-M6-26: GET /forwarders/:id/statistics
"""

import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
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
    conflict_response,
)
from core.exceptions import NotFoundException, ForbiddenException, ConflictException

from .models import ForwarderProfile, ForwarderReview
from .serializers import (
    ForwarderProfileSerializer,
    CreateForwarderProfileSerializer,
    UpdateForwarderProfileSerializer,
    ForwarderReviewSerializer,
    CreateForwarderReviewSerializer,
    UpdateForwarderReviewSerializer,
    ForwarderRecommendationSerializer,
    ForwarderStatisticsSerializer,
)
from .services import ForwarderRatingService, ForwarderRecommendationService

logger = logging.getLogger(__name__)


class ForwarderPagination(PageNumberPagination):
    """Pagination for forwarders list."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class ForwarderProfileCreateView(APIView):
    """
    PBI-BE-M6-16: POST /forwarder-profile
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create forwarder profile",
        description="Create a forwarder profile. User must have Forwarder role.",
        request=CreateForwarderProfileSerializer,
        responses={201: ForwarderProfileSerializer},
        tags=["Forwarders"],
    )
    def post(self, request):
        """POST /forwarder-profile - Create forwarder profile."""
        # Validate user role
        if request.user.role != UserRole.FORWARDER:
            return forbidden_response("Only Forwarder users can create profiles")

        serializer = CreateForwarderProfileSerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            forwarder_profile = serializer.save()
        except ConflictException as e:
            return conflict_response(str(e))

        response_serializer = ForwarderProfileSerializer(forwarder_profile)
        return created_response(
            data=response_serializer.data,
            message="Forwarder profile created successfully"
        )


class ForwarderProfileUpdateView(APIView):
    """
    PBI-BE-M6-19: PUT /forwarder-profile/:id
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update forwarder profile",
        description="Update a forwarder profile. Only the owner can update.",
        request=UpdateForwarderProfileSerializer,
        responses={200: ForwarderProfileSerializer},
        tags=["Forwarders"],
    )
    def put(self, request, profile_id):
        """PUT /forwarder-profile/:id - Update forwarder profile."""
        try:
            forwarder_profile = ForwarderProfile.objects.get(id=profile_id)
        except ForwarderProfile.DoesNotExist:
            return not_found_response("Forwarder profile not found")

        # Validate ownership
        if request.user.role != UserRole.ADMIN and forwarder_profile.user_id != request.user.id:
            return forbidden_response("You can only update your own profile")

        serializer = UpdateForwarderProfileSerializer(forwarder_profile, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        updated_profile = serializer.save()
        response_serializer = ForwarderProfileSerializer(updated_profile)
        return success_response(data=response_serializer.data, message="Profile updated successfully")


class ForwarderListView(APIView):
    """
    PBI-BE-M6-17: GET /forwarders
    """

    permission_classes = [IsAuthenticated]
    pagination_class = ForwarderPagination

    @extend_schema(
        summary="List forwarders",
        description="Get list of forwarder profiles with filters and sorting. Available to Admin and UMKM.",
        responses={200: ForwarderProfileSerializer(many=True)},
        tags=["Forwarders"],
    )
    def get(self, request):
        """GET /forwarders - List forwarders with filters."""
        # Validate user role
        if request.user.role not in [UserRole.ADMIN, UserRole.UMKM]:
            return forbidden_response("Only Admin and UMKM users can view forwarders")

        queryset = ForwarderProfile.objects.all()

        # Query params filtering
        destination_country = request.query_params.get("destination_country")
        if destination_country:
            route_pattern = f"ID-{destination_country}"
            queryset = queryset.filter(specialization_routes__contains=[route_pattern])

        service_type = request.query_params.get("service_type")
        if service_type:
            queryset = queryset.filter(service_types__contains=[service_type])

        min_rating = request.query_params.get("min_rating")
        if min_rating:
            try:
                min_rating_float = float(min_rating)
                queryset = queryset.filter(average_rating__gte=min_rating_float)
            except ValueError:
                pass

        # Sorting
        sort_by = request.query_params.get("sort", "rating")
        if sort_by == "rating":
            queryset = queryset.order_by("-average_rating", "-total_reviews")
        elif sort_by == "reviews":
            queryset = queryset.order_by("-total_reviews", "-average_rating")
        elif sort_by == "name":
            queryset = queryset.order_by("company_name")

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ForwarderProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ForwarderProfileSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="Forwarders retrieved successfully")


class ForwarderMyProfileView(APIView):
    """
    Get current forwarder's own profile.
    Convenience endpoint for forwarders to get their profile without knowing the ID.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get my forwarder profile",
        description="Get the forwarder profile of the currently authenticated forwarder user.",
        responses={200: ForwarderProfileSerializer},
        tags=["Forwarders"],
    )
    def get(self, request):
        """GET /forwarders/profile/me - Get current forwarder's own profile."""
        # Validate user role
        if request.user.role != UserRole.FORWARDER:
            return forbidden_response("Only Forwarder users can access this endpoint")

        try:
            forwarder = ForwarderProfile.objects.get(user=request.user)
        except ForwarderProfile.DoesNotExist:
            return not_found_response("Forwarder profile not found. Please create your profile first.")

        serializer = ForwarderProfileSerializer(forwarder)
        return success_response(data=serializer.data, message="Forwarder profile retrieved successfully")


class ForwarderDetailView(APIView):
    """
    PBI-BE-M6-18: GET /forwarders/:id
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get forwarder detail",
        description="Get detailed information about a forwarder profile.",
        responses={200: ForwarderProfileSerializer},
        tags=["Forwarders"],
    )
    def get(self, request, forwarder_id):
        """GET /forwarders/:id - Get forwarder detail."""
        try:
            forwarder = ForwarderProfile.objects.get(id=forwarder_id)
        except ForwarderProfile.DoesNotExist:
            return not_found_response("Forwarder not found")

        serializer = ForwarderProfileSerializer(forwarder)
        return success_response(data=serializer.data, message="Forwarder retrieved successfully")


class ForwarderReviewCreateView(APIView):
    """
    PBI-BE-M6-20: POST /forwarders/:id/reviews
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create forwarder review",
        description="Create a review for a forwarder. Only UMKM users can create reviews.",
        request=CreateForwarderReviewSerializer,
        responses={201: ForwarderReviewSerializer},
        tags=["Forwarders"],
    )
    def post(self, request, forwarder_id):
        """POST /forwarders/:id/reviews - Create forwarder review."""
        # Validate user role
        if request.user.role != UserRole.UMKM:
            return forbidden_response("Only UMKM users can create reviews")

        try:
            forwarder = ForwarderProfile.objects.get(id=forwarder_id)
        except ForwarderProfile.DoesNotExist:
            return not_found_response("Forwarder not found")

        serializer = CreateForwarderReviewSerializer(
            data=request.data,
            context={"request": request, "forwarder": forwarder}
        )
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        try:
            review = serializer.save()
        except ConflictException as e:
            return conflict_response(str(e))

        # Auto-trigger rating recalculation
        ForwarderRatingService.recalculate_rating(forwarder_id)

        response_serializer = ForwarderReviewSerializer(review)
        return created_response(
            data=response_serializer.data,
            message="Review created successfully"
        )


class ForwarderReviewUpdateView(APIView):
    """
    PBI-BE-M6-21: PUT /forwarders/:forwarder_id/reviews/:review_id
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Update forwarder review",
        description="Update an existing review. Only the review owner can update.",
        request=UpdateForwarderReviewSerializer,
        responses={200: ForwarderReviewSerializer},
        tags=["Forwarders"],
    )
    def put(self, request, forwarder_id, review_id):
        """PUT /forwarders/:forwarder_id/reviews/:review_id - Update review."""
        try:
            review = ForwarderReview.objects.get(id=review_id, forwarder_id=forwarder_id)
        except ForwarderReview.DoesNotExist:
            return not_found_response("Review not found")

        # Validate ownership
        if review.umkm_id != request.user.id:
            return forbidden_response("You can only update your own reviews")

        serializer = UpdateForwarderReviewSerializer(review, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        updated_review = serializer.save()

        # Auto-trigger rating recalculation
        ForwarderRatingService.recalculate_rating(forwarder_id)

        response_serializer = ForwarderReviewSerializer(updated_review)
        return success_response(data=response_serializer.data, message="Review updated successfully")


class ForwarderReviewDeleteView(APIView):
    """
    PBI-BE-M6-22: DELETE /forwarders/:forwarder_id/reviews/:review_id
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete forwarder review",
        description="Delete a review. Only the review owner can delete.",
        responses={204: None},
        tags=["Forwarders"],
    )
    def delete(self, request, forwarder_id, review_id):
        """DELETE /forwarders/:forwarder_id/reviews/:review_id - Delete review."""
        try:
            review = ForwarderReview.objects.get(id=review_id, forwarder_id=forwarder_id)
        except ForwarderReview.DoesNotExist:
            return not_found_response("Review not found")

        # Validate ownership
        if review.umkm_id != request.user.id:
            return forbidden_response("You can only delete your own reviews")

        review_id = review.id
        review.delete()

        # Auto-trigger rating recalculation
        ForwarderRatingService.recalculate_rating(forwarder_id)

        return success_response(
            data={"id": review_id},
            message="Review deleted successfully"
        )


class ForwarderRecommendationView(APIView):
    """
    PBI-BE-M6-25: GET /forwarders/recommendations
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get forwarder recommendations",
        description="Get recommended forwarders for a destination country. Available to UMKM users.",
        responses={200: ForwarderRecommendationSerializer(many=True)},
        tags=["Forwarders"],
    )
    def get(self, request):
        """GET /forwarders/recommendations - Get forwarder recommendations."""
        # Validate user role
        if request.user.role != UserRole.UMKM:
            return forbidden_response("Only UMKM users can view recommendations")

        destination_country = request.query_params.get("destination_country")
        if not destination_country:
            return validation_error_response({"destination_country": "destination_country is required"})

        recommendations = ForwarderRecommendationService.get_recommendations(destination_country)
        serializer = ForwarderRecommendationSerializer(recommendations, many=True)
        return success_response(data=serializer.data, message="Recommendations retrieved successfully")


class ForwarderStatisticsView(APIView):
    """
    PBI-BE-M6-26: GET /forwarders/:id/statistics
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get forwarder statistics",
        description="Get statistics for a forwarder profile. Available to Forwarder (own) and Admin (all).",
        responses={200: ForwarderStatisticsSerializer},
        tags=["Forwarders"],
    )
    def get(self, request, forwarder_id):
        """GET /forwarders/:id/statistics - Get forwarder statistics."""
        try:
            forwarder = ForwarderProfile.objects.get(id=forwarder_id)
        except ForwarderProfile.DoesNotExist:
            return not_found_response("Forwarder not found")

        # Validate access
        if request.user.role not in [UserRole.ADMIN, UserRole.FORWARDER]:
            return forbidden_response("You do not have permission to view statistics")
        
        if request.user.role == UserRole.FORWARDER and forwarder.user_id != request.user.id:
            return forbidden_response("You can only view your own statistics")

        statistics = ForwarderRecommendationService.get_statistics(forwarder_id)
        if statistics is None:
            return error_response("Error retrieving statistics", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = ForwarderStatisticsSerializer(statistics)
        return success_response(data=serializer.data, message="Statistics retrieved successfully")

