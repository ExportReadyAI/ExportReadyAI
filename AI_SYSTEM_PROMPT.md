# AI System Prompt for ExportReady.AI Backend

> **Copy and paste this prompt when using AI assistants (Cursor, Claude, ChatGPT) to maintain code consistency.**

---

## System Prompt

```
You are working on ExportReady.AI, a Django REST Framework backend API for Indonesian UMKM export platform.

## Tech Stack
- Django 5.0 + DRF + PostgreSQL (Supabase)
- JWT auth (simplejwt) + bcrypt passwords
- drf-spectacular for OpenAPI docs

## Project Structure
- `apps/` - All Django apps (authentication, users, business_profiles, etc.)
- `core/` - Shared utilities (exceptions, pagination, permissions, responses)
- `config/settings/` - Split settings (base, development, production, test)

## CRITICAL RULES

### 1. API Responses - ALWAYS use core.responses helpers:
```python
from core.responses import success_response, created_response, error_response

# Success (200)
return success_response(data={...}, message="Success")

# Created (201)
return created_response(data={...}, message="Created successfully")

# Error (400/401/403/404)
return error_response(message="Error", errors={...}, status_code=status.HTTP_400_BAD_REQUEST)
```

Response format: {"success": true/false, "message": "...", "data": {...}, "errors": {...}}

### 2. Views - Use class-based APIView (NOT ViewSets):
```python
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from core.permissions import IsAdminOrUMKM

class MyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrUMKM]
    
    @extend_schema(summary="...", tags=["TagName"])
    def get(self, request):
        return success_response(data={...})
```

### 3. Permissions - Use core.permissions:
- `IsAdmin` - Admin only
- `IsUMKM` - UMKM only  
- `IsAdminOrUMKM` - Both roles
- `IsOwnerOrAdmin` - Object-level permission

### 4. Custom Exceptions - Use core.exceptions:
```python
from core.exceptions import NotFoundException, ForbiddenException, ConflictException
raise NotFoundException("Resource not found")
```

### 5. Serializers Pattern:
- ModelSerializer for READ (GET)
- Plain Serializer for WRITE (POST/PUT) with explicit validation
- Always include error_messages for required fields

### 6. Models - Always include:
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`
- `class Meta: ordering = ["-created_at"]`
- Verbose names for all fields

### 7. User Roles:
```python
from apps.users.models import UserRole
UserRole.ADMIN  # "Admin"
UserRole.UMKM   # "UMKM" (default for new users)
```

### 8. URL Naming:
- Apps go in `apps/` folder
- URL namespace: `app_name = "my_app"` in urls.py
- Register in `config/urls.py` under `api_v1_patterns`

## DO NOT:
- Use function-based views
- Use ViewSets
- Return raw Response() without helpers
- Create apps outside apps/ folder
- Use username field (we use email)
- Skip @extend_schema decorators

## REFERENCE FILES:
- `apps/authentication/` - Auth pattern example
- `apps/business_profiles/` - CRUD pattern example
- `core/responses.py` - Response helpers
- `core/permissions.py` - Permission classes
- `DEVELOPER_PROMPT.md` - Full guidelines
```

---

## Quick Copy-Paste Version (Shorter)

```
ExportReady.AI Django Backend Rules:

1. RESPONSES: Use core.responses (success_response, created_response, error_response)
   Format: {"success": bool, "message": str, "data": {}, "errors": {}}

2. VIEWS: Class-based APIView only, not ViewSets
   Always add @extend_schema for docs

3. PERMISSIONS: core.permissions (IsAdmin, IsUMKM, IsAdminOrUMKM)

4. EXCEPTIONS: core.exceptions (NotFoundException, ForbiddenException, ConflictException)

5. MODELS: Always include created_at, updated_at, verbose_name

6. ROLES: UserRole.ADMIN, UserRole.UMKM (default)

7. STRUCTURE: Apps in apps/, shared code in core/

Reference: apps/authentication/, apps/business_profiles/, DEVELOPER_PROMPT.md
```

