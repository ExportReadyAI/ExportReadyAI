"""
Custom Exception Handling for ExportReady.AI API
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors consistently.

    Response format:
    {
        "success": false,
        "message": "Error message",
        "errors": {...}  # Optional, for validation errors
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            "success": False,
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
        }

        # Only process detail if it exists (Http404 doesn't have detail attribute)
        if hasattr(exc, "detail"):
            # Handle validation errors (dict of field errors)
            if isinstance(exc.detail, dict):
                custom_response_data["message"] = "Validation failed"
                custom_response_data["errors"] = exc.detail
            # Handle list of errors
            elif isinstance(exc.detail, list):
                custom_response_data["message"] = exc.detail[0] if exc.detail else "An error occurred"
                custom_response_data["errors"] = exc.detail

        response.data = custom_response_data

    return response


class ConflictException(APIException):
    """
    Exception for 409 Conflict responses (e.g., duplicate email, existing profile)
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource already exists"
    default_code = "conflict"


class BadRequestException(APIException):
    """
    Exception for 400 Bad Request responses
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad request"
    default_code = "bad_request"


class ForbiddenException(APIException):
    """
    Exception for 403 Forbidden responses
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action"
    default_code = "forbidden"


class NotFoundException(APIException):
    """
    Exception for 404 Not Found responses
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Resource not found"
    default_code = "not_found"


class UnauthorizedException(APIException):
    """
    Exception for 401 Unauthorized responses
    """

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided or are invalid"
    default_code = "unauthorized"

