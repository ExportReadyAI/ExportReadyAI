"""
Custom Permission Classes for ExportReady.AI API

Implements:
- PBI-BE-M1-11: Middleware: Role Guard
  - Cek role user dari JWT claims (user_id → lookup role)
  - Validasi apakah role diizinkan akses endpoint tertentu
  - Response 403 Forbidden jika role tidak sesuai

Note: PBI-BE-M1-10 (Auth Guard) is implemented via djangorestframework-simplejwt
in config/settings/base.py - validates JWT token on every request.

All acceptance criteria for these PBIs are implemented in this module.
"""

from rest_framework.permissions import BasePermission

from apps.users.models import UserRole


class IsAdmin(BasePermission):
    """
    # PBI-BE-M1-11: Role Guard - Admin Only
    # - Validates user role from JWT token
    # - Returns 403 Forbidden if not Admin

    Permission class that only allows Admin users.
    """

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsUMKM(BasePermission):
    """
    # PBI-BE-M1-11: Role Guard - UMKM Only
    # - Validates user role from JWT token
    # - Returns 403 Forbidden if not UMKM

    Permission class that only allows UMKM users.
    """

    message = "Only UMKM users can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.UMKM
        )


class IsAdminOrUMKM(BasePermission):
    """
    # PBI-BE-M1-11: Role Guard - Admin or UMKM
    # - Validates user role from JWT token
    # - Allows both Admin and UMKM roles
    # - Returns 403 Forbidden if neither

    Permission class that allows both Admin and UMKM users.
    """

    message = "You must be logged in to perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in [UserRole.ADMIN, UserRole.UMKM]
        )


class IsOwnerOrAdmin(BasePermission):
    """
    # PBI-BE-M1-11: Role Guard - Owner or Admin
    # - Admin: Full access to all resources
    # - UMKM: Only their own resources (validates ownership)
    # - Returns 403 Forbidden if not owner and not Admin

    Permission class that allows:
    - Admin users: full access
    - UMKM users: only their own resources

    Requires the view to have `get_object()` method and the object
    to have a `user` or `user_id` attribute.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == UserRole.ADMIN:
            return True

        # Check if the object belongs to the user
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id

        return False


def role_required(allowed_roles):
    """
    Decorator-style permission factory for role-based access.
    
    Usage:
        permission_classes = [role_required([UserRole.ADMIN, UserRole.UMKM])]
    """

    class RolePermission(BasePermission):
        message = f"Only users with roles {allowed_roles} can perform this action."

        def has_permission(self, request, view):
            return (
                request.user
                and request.user.is_authenticated
                and request.user.role in allowed_roles
            )

    return RolePermission

