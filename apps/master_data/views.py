"""
Views for ExportReady.AI Module 5 - Master Data (Admin Only)

Implements all admin endpoints for master data management:
# PBI-BE-M5-01 to M5-05: HSCode management
# PBI-BE-M5-06 to M5-08: Country management
# PBI-BE-M5-09 to M5-13: Regulation management
"""

import csv
import io

from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.export_analysis.models import Country, CountryRegulation
from core.permissions import IsAdmin

from .models import HSCode, HSSection
from .serializers import (
    CountryCreateSerializer,
    CountryUpdateSerializer,
    HSCodeCreateSerializer,
    HSCodeDetailSerializer,
    HSCodeListSerializer,
    HSCodeUpdateSerializer,
    RegulationCreateSerializer,
    RegulationListSerializer,
    RegulationUpdateSerializer,
)


# ============================================================================
# HSCode Views (PBI-BE-M5-01 to M5-05)
# ============================================================================

# PBI-BE-M5-01: [DONE] API: GET /hs-codes
class HSCodeListView(APIView):
    """
    GET /hs-codes - List all HS Codes (Admin only)

    Acceptance Criteria:
    - Return list HS Codes dengan pagination
    - Query params: page, limit, chapter, search
    - Search by hs_code atau description
    - Response: array dengan pagination info
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = HSCode.objects.all()

        # Filter by chapter
        chapter = request.query_params.get("chapter")
        if chapter:
            queryset = queryset.filter(hs_chapter=chapter)

        # Filter by level
        level = request.query_params.get("level")
        if level:
            queryset = queryset.filter(level=level)

        # Filter by section
        section = request.query_params.get("section")
        if section:
            queryset = queryset.filter(section=section)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(hs_code__icontains=search) |
                Q(description__icontains=search) |
                Q(description_id__icontains=search) |
                Q(keywords__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 20))
        offset = (page - 1) * limit

        total = queryset.count()
        hs_codes = queryset[offset:offset + limit]

        serializer = HSCodeListSerializer(hs_codes, many=True)

        return Response({
            "success": True,
            "message": "HS Codes retrieved successfully",
            "data": serializer.data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })


# PBI-BE-M5-01: [DONE] API: GET /hs-codes/:code
class HSCodeDetailView(APIView):
    """
    GET /hs-codes/:code - Get HS Code detail (Admin only)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, hs_code):
        try:
            code = HSCode.objects.get(hs_code=hs_code)
        except HSCode.DoesNotExist:
            return Response({
                "success": False,
                "message": "HS Code not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = HSCodeDetailSerializer(code)
        return Response({
            "success": True,
            "message": "HS Code retrieved successfully",
            "data": serializer.data
        })


# PBI-BE-M5-02: [DONE] API: POST /hs-codes
class HSCodeCreateView(APIView):
    """
    POST /hs-codes - Create new HS Code (Admin only)

    Acceptance Criteria:
    - Body: hs_code, description_id, description_en, keywords
    - Auto-extract: hs_chapter, hs_heading, hs_subheading
    - Validasi: hs_code format (2-8 digit)
    - Validasi: hs_code unique
    - Response: 201 Created
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = HSCodeCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        hs_code = serializer.save()

        return Response({
            "success": True,
            "message": "HS Code created successfully",
            "data": HSCodeDetailSerializer(hs_code).data
        }, status=status.HTTP_201_CREATED)


# PBI-BE-M5-03: [DONE] API: PUT /hs-codes/:code
class HSCodeUpdateView(APIView):
    """
    PUT /hs-codes/:code - Update HS Code (Admin only)

    Note: hs_code cannot be changed
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, hs_code):
        try:
            code = HSCode.objects.get(hs_code=hs_code)
        except HSCode.DoesNotExist:
            return Response({
                "success": False,
                "message": "HS Code not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = HSCodeUpdateSerializer(code, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            "success": True,
            "message": "HS Code updated successfully",
            "data": HSCodeDetailSerializer(code).data
        })


# PBI-BE-M5-04: [DONE] API: DELETE /hs-codes/:code
class HSCodeDeleteView(APIView):
    """
    DELETE /hs-codes/:code - Delete HS Code (Admin only)

    Acceptance Criteria:
    - Validasi: tidak ada ProductEnrichment yang reference
    - Response: 200 OK atau 409 Conflict
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, hs_code):
        try:
            code = HSCode.objects.get(hs_code=hs_code)
        except HSCode.DoesNotExist:
            return Response({
                "success": False,
                "message": "HS Code not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if any children exist
        if code.children.exists():
            return Response({
                "success": False,
                "message": "Cannot delete HS Code with child codes. Delete children first."
            }, status=status.HTTP_409_CONFLICT)

        code.delete()

        return Response({
            "success": True,
            "message": "HS Code deleted successfully"
        })


# PBI-BE-M5-05: [DONE] API: POST /hs-codes/import
class HSCodeImportView(APIView):
    """
    POST /hs-codes/import - Bulk import from CSV (Admin only)

    Acceptance Criteria:
    - Accept: multipart/form-data dengan CSV file
    - Parse CSV dan validate each row
    - Skip duplicates atau update existing
    - Response: {success_count, failed_count, errors}
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        if "file" not in request.FILES:
            return Response({
                "success": False,
                "message": "No file provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES["file"]

        if not csv_file.name.endswith('.csv'):
            return Response({
                "success": False,
                "message": "File must be a CSV"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))

            success_count = 0
            failed_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    hs_code = row.get("hs_code", "").strip()
                    if not hs_code:
                        continue

                    # Get or create section
                    section = None
                    section_code = row.get("section", "").strip()
                    if section_code:
                        section, _ = HSSection.objects.get_or_create(
                            section=section_code,
                            defaults={"name": row.get("section_name", section_code)}
                        )

                    # Determine level
                    level = int(row.get("level", len(hs_code)))
                    if level not in [2, 4, 6]:
                        level = 6

                    HSCode.objects.update_or_create(
                        hs_code=hs_code,
                        defaults={
                            "description": row.get("description", row.get("description_en", "")),
                            "description_id": row.get("description_id", ""),
                            "section": section,
                            "level": level,
                            "keywords": row.get("keywords", "").split(",") if row.get("keywords") else [],
                        }
                    )
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            return Response({
                "success": True,
                "message": f"Import completed: {success_count} success, {failed_count} failed",
                "data": {
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "errors": errors[:10]  # Limit errors shown
                }
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Import failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Country Admin Views (PBI-BE-M5-06 to M5-08)
# ============================================================================

# PBI-BE-M5-06: [DONE] API: POST /countries
class CountryCreateView(APIView):
    """
    POST /countries - Create new country (Admin only)

    Acceptance Criteria:
    - Body: country_code, country_name, region
    - Validasi: country_code format (2 char ISO)
    - Validasi: country_code unique
    - Response: 201 Created
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = CountryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        country = serializer.save()

        return Response({
            "success": True,
            "message": "Country created successfully",
            "data": {
                "country_code": country.country_code,
                "country_name": country.country_name,
                "region": country.region,
            }
        }, status=status.HTTP_201_CREATED)


# PBI-BE-M5-07: [DONE] API: PUT /countries/:code
class CountryUpdateView(APIView):
    """
    PUT /countries/:code - Update country (Admin only)

    Note: country_code cannot be changed
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, country_code):
        try:
            country = Country.objects.get(country_code=country_code.upper())
        except Country.DoesNotExist:
            return Response({
                "success": False,
                "message": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CountryUpdateSerializer(country, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            "success": True,
            "message": "Country updated successfully",
            "data": {
                "country_code": country.country_code,
                "country_name": country.country_name,
                "region": country.region,
            }
        })


# PBI-BE-M5-08: [DONE] API: DELETE /countries/:code
class CountryDeleteView(APIView):
    """
    DELETE /countries/:code - Delete country (Admin only)

    Acceptance Criteria:
    - Cascade delete: CountryRegulation
    - Validasi: tidak ada ExportAnalysis yang reference
    - Response: 200 OK atau 409 Conflict
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, country_code):
        try:
            country = Country.objects.get(country_code=country_code.upper())
        except Country.DoesNotExist:
            return Response({
                "success": False,
                "message": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if any ExportAnalysis references this country
        from apps.export_analysis.models import ExportAnalysis
        if ExportAnalysis.objects.filter(target_country=country).exists():
            return Response({
                "success": False,
                "message": "Cannot delete country with existing export analyses. Delete analyses first."
            }, status=status.HTTP_409_CONFLICT)

        # Cascade delete regulations
        country.regulations.all().delete()
        country.delete()

        return Response({
            "success": True,
            "message": "Country deleted successfully"
        })


# ============================================================================
# Regulation Admin Views (PBI-BE-M5-09 to M5-13)
# ============================================================================

# PBI-BE-M5-09: [DONE] API: GET /countries/:code/regulations
class RegulationListView(APIView):
    """
    GET /countries/:code/regulations - List regulations for country (Admin only)

    Query params: rule_category
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, country_code):
        try:
            country = Country.objects.get(country_code=country_code.upper())
        except Country.DoesNotExist:
            return Response({
                "success": False,
                "message": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)

        regulations = country.regulations.all()

        # Filter by rule_category
        rule_category = request.query_params.get("rule_category")
        if rule_category:
            regulations = regulations.filter(rule_category=rule_category)

        serializer = RegulationListSerializer(regulations, many=True)

        return Response({
            "success": True,
            "message": "Regulations retrieved successfully",
            "data": {
                "country_code": country.country_code,
                "country_name": country.country_name,
                "regulations": serializer.data
            }
        })


# PBI-BE-M5-10: [DONE] API: POST /countries/:code/regulations
class RegulationCreateView(APIView):
    """
    POST /countries/:code/regulations - Create regulation for country (Admin only)

    Acceptance Criteria:
    - Body: rule_category, forbidden_keywords, required_specs, description_rule
    - Validasi: rule_category enum valid
    - Response: 201 Created
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, country_code):
        try:
            country = Country.objects.get(country_code=country_code.upper())
        except Country.DoesNotExist:
            return Response({
                "success": False,
                "message": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = RegulationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        regulation = serializer.save(country=country)

        return Response({
            "success": True,
            "message": "Regulation created successfully",
            "data": RegulationListSerializer(regulation).data
        }, status=status.HTTP_201_CREATED)


# PBI-BE-M5-11: [DONE] API: PUT /regulations/:id
class RegulationUpdateView(APIView):
    """
    PUT /regulations/:id - Update regulation (Admin only)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, regulation_id):
        try:
            regulation = CountryRegulation.objects.get(id=regulation_id)
        except CountryRegulation.DoesNotExist:
            return Response({
                "success": False,
                "message": "Regulation not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = RegulationUpdateSerializer(regulation, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            "success": True,
            "message": "Regulation updated successfully",
            "data": RegulationListSerializer(regulation).data
        })


# PBI-BE-M5-12: [DONE] API: DELETE /regulations/:id
class RegulationDeleteView(APIView):
    """
    DELETE /regulations/:id - Delete regulation (Admin only)
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, regulation_id):
        try:
            regulation = CountryRegulation.objects.get(id=regulation_id)
        except CountryRegulation.DoesNotExist:
            return Response({
                "success": False,
                "message": "Regulation not found"
            }, status=status.HTTP_404_NOT_FOUND)

        regulation.delete()

        return Response({
            "success": True,
            "message": "Regulation deleted successfully"
        })


# PBI-BE-M5-13: [DONE] API: POST /regulations/import
class RegulationImportView(APIView):
    """
    POST /regulations/import - Bulk import regulations from CSV (Admin only)

    CSV format: country_code, rule_category, forbidden_keywords, required_specs, description_rule
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        if "file" not in request.FILES:
            return Response({
                "success": False,
                "message": "No file provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES["file"]

        if not csv_file.name.endswith('.csv'):
            return Response({
                "success": False,
                "message": "File must be a CSV"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))

            success_count = 0
            failed_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    country_code = row.get("country_code", "").strip().upper()
                    if not country_code:
                        continue

                    try:
                        country = Country.objects.get(country_code=country_code)
                    except Country.DoesNotExist:
                        errors.append(f"Row {row_num}: Country {country_code} not found")
                        failed_count += 1
                        continue

                    CountryRegulation.objects.create(
                        country=country,
                        rule_category=row.get("rule_category", "").strip(),
                        forbidden_keywords=row.get("forbidden_keywords", "").strip(),
                        required_specs=row.get("required_specs", "").strip(),
                        description_rule=row.get("description_rule", "").strip(),
                    )
                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            return Response({
                "success": True,
                "message": f"Import completed: {success_count} success, {failed_count} failed",
                "data": {
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "errors": errors[:10]
                }
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Import failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
