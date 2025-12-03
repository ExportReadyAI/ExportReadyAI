"""
Custom Pagination Classes for ExportReady.AI API
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class with customizable page size.
    
    Query Parameters:
        - page: Page number (default: 1)
        - limit: Number of items per page (default: 10, max: 100)
    
    Response format:
    {
        "success": true,
        "message": "Data retrieved successfully",
        "data": [...],
        "pagination": {
            "count": 100,
            "page": 1,
            "limit": 10,
            "total_pages": 10,
            "next": "http://api.example.com/resource/?page=2",
            "previous": null
        }
    }
    """

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "message": "Data retrieved successfully",
                "data": data,
                "pagination": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "limit": self.get_page_size(self.request),
                    "total_pages": self.page.paginator.num_pages,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "page": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                    },
                },
            },
        }

