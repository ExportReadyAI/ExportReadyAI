"""
Custom Permission Classes for ExportReady.AI API
"""

from rest_framework.permissions import BasePermission

from apps.users.models import UserRole


class IsAdmin(BasePermission):
    """
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

