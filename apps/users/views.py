"""
User Views for ExportReady.AI

Implements:
- PBI-BE-M1-08: GET /users (Admin only)
- PBI-BE-M1-09: DELETE /users/:id
"""

from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.exceptions import ForbiddenException, NotFoundException
from core.pagination import StandardResultsSetPagination
from core.permissions import IsAdmin, IsAdminOrUMKM
from core.responses import success_response

from .models import User, UserRole
from .serializers import UserListSerializer


class UserListView(APIView):
    """
    API endpoint for listing users (Admin only).
    
    PBI-BE-M1-08:
    - Return list of all users with pagination
    - Query params: page, limit, role, search
    - Search by email or full_name (LIKE query)
    - Response: array of users with total count
    - Response does not include password_hash
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List all users",
        description="Admin only endpoint to list all users with pagination and filtering.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number"),
            OpenApiParameter(name="limit", type=int, description="Items per page"),
            OpenApiParameter(name="role", type=str, description="Filter by role (Admin, UMKM)"),
            OpenApiParameter(name="search", type=str, description="Search by email or full_name"),
        ],
        responses={200: UserListSerializer(many=True)},
        tags=["Users"],
    )
    def get(self, request):
        queryset = User.objects.all()

        # Filter by role
        role = request.query_params.get("role")
        if role and role in [UserRole.ADMIN, UserRole.UMKM]:
            queryset = queryset.filter(role=role)

        # Search by email or full_name
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserListSerializer(queryset, many=True)
        return success_response(data=serializer.data)


class UserDeleteView(APIView):
    """
    API endpoint for deleting a user account.
    
    PBI-BE-M1-09:
    - UMKM can only delete their own account
    - Cascade delete: BusinessProfile, Product, ProductEnrichment, ExportAnalysis, Costing
    - Response success: 200 OK with message
    - Response error: 403 Forbidden if not own account
    """

    permission_classes = [IsAuthenticated, IsAdminOrUMKM]

    @extend_schema(
        summary="Delete user account",
        description="UMKM can only delete their own account. Cascade deletes all related data.",
        responses={
            200: {"description": "Account deleted successfully"},
            403: {"description": "Forbidden - cannot delete other user's account"},
            404: {"description": "User not found"},
        },
        tags=["Users"],
    )
    def delete(self, request, user_id):
        try:
            user_to_delete = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundException("User not found")

        # UMKM can only delete their own account
        if request.user.role == UserRole.UMKM and request.user.id != user_to_delete.id:
            raise ForbiddenException("You can only delete your own account")

        # Cascade delete is handled by Django's on_delete=CASCADE
        with transaction.atomic():
            email = user_to_delete.email
            user_to_delete.delete()

        return success_response(
            message=f"User account ({email}) has been deleted successfully",
            status_code=status.HTTP_200_OK,
        )

