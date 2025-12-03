"""
Standardized API Response Helpers for ExportReady.AI
"""

from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    Create a standardized success response.
    
    Args:
        data: The response data (dict, list, or None)
        message: Success message
        status_code: HTTP status code
    
    Returns:
        Response object with format:
        {
            "success": true,
            "message": "Success message",
            "data": {...}
        }
    """
    response_data = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response_data["data"] = data
    return Response(response_data, status=status_code)


def created_response(data=None, message="Created successfully"):
    """
    Create a standardized 201 Created response.
    """
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: Optional dict of field-level errors
        status_code: HTTP status code
    
    Returns:
        Response object with format:
        {
            "success": false,
            "message": "Error message",
            "errors": {...}  # Optional
        }
    """
    response_data = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        response_data["errors"] = errors
    return Response(response_data, status=status_code)


def validation_error_response(errors, message="Validation failed"):
    """
    Create a standardized validation error response.
    """
    return error_response(message=message, errors=errors, status_code=status.HTTP_400_BAD_REQUEST)


def not_found_response(message="Resource not found"):
    """
    Create a standardized 404 Not Found response.
    """
    return error_response(message=message, status_code=status.HTTP_404_NOT_FOUND)


def unauthorized_response(message="Unauthorized"):
    """
    Create a standardized 401 Unauthorized response.
    """
    return error_response(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message="Forbidden"):
    """
    Create a standardized 403 Forbidden response.
    """
    return error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)


def conflict_response(message="Resource already exists"):
    """
    Create a standardized 409 Conflict response.
    """
    return error_response(message=message, status_code=status.HTTP_409_CONFLICT)

