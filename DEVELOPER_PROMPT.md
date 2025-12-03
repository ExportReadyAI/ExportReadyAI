# 🧠 ExportReady.AI - Developer Prompt & Guidelines

> **Use this prompt when working with AI assistants (Cursor, Claude, Copilot) or as a reference guide to maintain consistency across the codebase.**

---

## 📋 Project Context

You are working on **ExportReady.AI**, a Django REST Framework backend API for an AI-powered export platform for Indonesian UMKM (small businesses).

**Tech Stack:**
- Django 5.0 + Django REST Framework
- PostgreSQL (Supabase)
- JWT Authentication (djangorestframework-simplejwt)
- bcrypt for password hashing
- drf-spectacular for OpenAPI docs

---

## 🏗️ Project Structure Convention

```
exportready-backend/
├── config/                     # Project configuration (DO NOT put app code here)
│   └── settings/              # Split settings: base.py, development.py, production.py, test.py
├── apps/                       # All Django apps go here
│   └── {app_name}/            # Each feature is a separate app
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py          # Database models
│       ├── serializers.py     # DRF serializers
│       ├── views.py           # API views (use APIView, not ViewSets)
│       ├── urls.py            # URL routing for this app
│       ├── admin.py           # Django admin config
│       └── tests/             # Tests folder
│           ├── __init__.py
│           ├── factories.py   # Test factories (factory-boy)
│           └── test_*.py      # Test files
├── core/                       # Shared utilities (reusable across apps)
│   ├── exceptions.py          # Custom exceptions
│   ├── pagination.py          # Pagination classes
│   ├── permissions.py         # Permission classes
│   └── responses.py           # Response helpers
└── requirements/               # Split requirements
```

---

## ✅ Coding Standards & Patterns

### 1. API Response Format (ALWAYS follow this)

**Success Response:**
```python
from core.responses import success_response, created_response

# 200 OK
return success_response(
    data={"key": "value"},
    message="Operation successful"
)

# 201 Created
return created_response(
    data=serializer.data,
    message="Resource created successfully"
)
```

**Error Response:**
```python
from core.responses import error_response, not_found_response, forbidden_response

# 400 Bad Request
return error_response(
    message="Validation failed",
    errors=serializer.errors,
    status_code=status.HTTP_400_BAD_REQUEST
)

# 404 Not Found
return not_found_response(message="Resource not found")

# 403 Forbidden
return forbidden_response(message="You don't have permission")
```

**Response JSON Structure:**
```json
// Success
{
  "success": true,
  "message": "Description of what happened",
  "data": { ... }
}

// Error
{
  "success": false,
  "message": "Error description",
  "errors": { "field": ["error message"] }
}

// Paginated
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": [...],
  "pagination": {
    "count": 100,
    "page": 1,
    "limit": 10,
    "total_pages": 10,
    "next": "url",
    "previous": null
  }
}
```

### 2. Views Pattern (Use Class-Based APIView)

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.exceptions import NotFoundException, ForbiddenException
from core.permissions import IsAdminOrUMKM
from core.responses import success_response, created_response, error_response


class MyResourceListCreateView(APIView):
    """
    Brief description of what this view does.
    
    PBI-XX-XX: Reference to product backlog item
    """
    permission_classes = [IsAuthenticated, IsAdminOrUMKM]

    @extend_schema(
        summary="Short summary for docs",
        description="Detailed description",
        request=MySerializer,
        responses={200: MyResponseSerializer},
        tags=["Tag Name"],
    )
    def get(self, request):
        # Implementation
        pass

    @extend_schema(...)
    def post(self, request):
        serializer = MySerializer(data=request.data, context={"request": request})
        
        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        instance = serializer.save()
        return created_response(
            data=MyResponseSerializer(instance).data,
            message="Created successfully"
        )
```

### 3. Serializers Pattern

```python
from rest_framework import serializers

# For READ operations (GET)
class MyModelSerializer(serializers.ModelSerializer):
    """Serializer for reading MyModel."""
    
    # Add computed fields
    computed_field = serializers.SerializerMethodField()
    
    class Meta:
        model = MyModel
        fields = ["id", "field1", "field2", "computed_field", "created_at"]
        read_only_fields = ["id", "created_at"]
    
    def get_computed_field(self, obj):
        return obj.some_computation()


# For WRITE operations (POST/PUT/PATCH) - Use plain Serializer for more control
class CreateMyModelSerializer(serializers.Serializer):
    """Serializer for creating MyModel."""
    
    field1 = serializers.CharField(
        required=True,
        max_length=255,
        error_messages={
            "required": "Field1 is required",
            "max_length": "Field1 must be less than 255 characters",
        }
    )
    
    def validate_field1(self, value):
        """Custom validation for field1."""
        if some_condition:
            raise serializers.ValidationError("Error message")
        return value
    
    def create(self, validated_data):
        user = self.context["request"].user
        return MyModel.objects.create(user=user, **validated_data)
```

### 4. Models Pattern

```python
from django.conf import settings
from django.db import models


class MyModel(models.Model):
    """
    Description of what this model represents.
    """
    
    # Foreign keys
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_models",
        verbose_name="user",
    )
    
    # Fields with verbose names
    name = models.CharField("name", max_length=255)
    description = models.TextField("description", blank=True)
    is_active = models.BooleanField("active", default=True)
    
    # JSON fields for flexible data
    metadata = models.JSONField("metadata", default=dict, blank=True)
    
    # Timestamps (ALWAYS include these)
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True)

    class Meta:
        verbose_name = "my model"
        verbose_name_plural = "my models"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
```

### 5. Permissions Pattern

```python
# In your view
from core.permissions import IsAdmin, IsUMKM, IsAdminOrUMKM, IsOwnerOrAdmin

class MyView(APIView):
    # For Admin only
    permission_classes = [IsAuthenticated, IsAdmin]
    
    # For UMKM only
    permission_classes = [IsAuthenticated, IsUMKM]
    
    # For both Admin and UMKM
    permission_classes = [IsAuthenticated, IsAdminOrUMKM]


# For object-level permissions (checking ownership)
def get_object(self, pk, user):
    try:
        obj = MyModel.objects.get(pk=pk)
    except MyModel.DoesNotExist:
        raise NotFoundException("Resource not found")
    
    # Check ownership for UMKM
    if user.role == UserRole.UMKM and obj.user_id != user.id:
        raise ForbiddenException("You can only access your own resources")
    
    return obj
```

### 6. URL Pattern

```python
# apps/{app_name}/urls.py
from django.urls import path
from .views import MyListCreateView, MyDetailView

app_name = "app_name"  # ALWAYS set app_name for namespacing

urlpatterns = [
    path("", MyListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", MyDetailView.as_view(), name="detail"),
]

# config/urls.py - Register in api_v1_patterns
api_v1_patterns = [
    path("my-resource/", include("apps.my_app.urls")),
]
```

### 7. Testing Pattern

```python
# tests/factories.py
import factory
from faker import Faker
from apps.my_app.models import MyModel

fake = Faker()

class MyModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MyModel
    
    name = factory.LazyAttribute(lambda _: fake.company())
    user = factory.SubFactory("apps.users.tests.factories.UMKMUserFactory")


# tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestMyView:
    def test_create_success(self, api_client, umkm_user):
        api_client.force_authenticate(user=umkm_user)
        url = reverse("app_name:list-create")
        data = {"name": "Test"}
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
```

---

## 🎯 When Creating a New Feature/Module

### Step 1: Create the App Structure
```bash
# Create app folder manually in apps/
mkdir apps/new_feature
```

### Step 2: Create Files in This Order
1. `__init__.py` - App init
2. `apps.py` - App config
3. `models.py` - Database models
4. `serializers.py` - Request/Response serializers
5. `views.py` - API endpoints
6. `urls.py` - URL routing
7. `admin.py` - Admin configuration
8. `tests/` - Test folder with factories and tests

### Step 3: Register the App
1. Add to `config/settings/base.py` in `LOCAL_APPS`
2. Add URL pattern to `config/urls.py` in `api_v1_patterns`
3. Run migrations: `python manage.py makemigrations && python manage.py migrate`

---

## 🚫 DO NOT

- ❌ Use function-based views (use class-based APIView)
- ❌ Use ViewSets (we prefer explicit APIView for clarity)
- ❌ Return raw Response() - use `core.responses` helpers
- ❌ Hardcode error messages - define in serializers
- ❌ Skip `@extend_schema` decorators - we need good docs
- ❌ Put business logic in views - put in serializers or model methods
- ❌ Create apps outside the `apps/` folder
- ❌ Use `username` field - we use `email` as the primary identifier
- ❌ Skip tests - at minimum write happy path tests

---

## ✅ DO

- ✅ Use type hints where helpful
- ✅ Write docstrings for classes and complex methods
- ✅ Reference PBI codes in view docstrings
- ✅ Use `select_related()` and `prefetch_related()` for queries
- ✅ Validate at serializer level, not view level
- ✅ Use transactions for multi-step operations
- ✅ Log important operations
- ✅ Return consistent response format

---

## 🔐 User Roles

```python
from apps.users.models import UserRole

# Available roles
UserRole.ADMIN  # "Admin" - System administrator
UserRole.UMKM   # "UMKM" - Business owner (main user type)

# Check role in code
if request.user.role == UserRole.ADMIN:
    # Admin-specific logic

if request.user.is_umkm:  # Property shortcut
    # UMKM-specific logic
```

---

## 📝 Example: Creating a New "Products" Module

```python
# apps/products/models.py
from django.conf import settings
from django.db import models

class Product(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField("name", max_length=255)
    description = models.TextField("description", blank=True)
    hs_code = models.CharField("HS code", max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "product"
        verbose_name_plural = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# apps/products/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "hs_code", "created_at"]
        read_only_fields = ["id", "created_at"]

class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    hs_code = serializers.CharField(required=False, max_length=20)
    
    def create(self, validated_data):
        user = self.context["request"].user
        return Product.objects.create(user=user, **validated_data)


# apps/products/views.py
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.permissions import IsUMKM
from core.responses import success_response, created_response, error_response

from .models import Product
from .serializers import ProductSerializer, CreateProductSerializer

class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsUMKM]
    
    @extend_schema(
        summary="List user's products",
        responses={200: ProductSerializer(many=True)},
        tags=["Products"],
    )
    def get(self, request):
        products = Product.objects.filter(user=request.user)
        serializer = ProductSerializer(products, many=True)
        return success_response(data=serializer.data)
    
    @extend_schema(
        summary="Create a product",
        request=CreateProductSerializer,
        responses={201: ProductSerializer},
        tags=["Products"],
    )
    def post(self, request):
        serializer = CreateProductSerializer(
            data=request.data, 
            context={"request": request}
        )
        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors
            )
        product = serializer.save()
        return created_response(
            data=ProductSerializer(product).data,
            message="Product created successfully"
        )
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific app tests
pytest apps/products/tests/

# Run with coverage
pytest --cov=apps --cov-report=html
```

---

## 📚 Quick Reference

| What | Where | Example |
|------|-------|---------|
| Custom exceptions | `core/exceptions.py` | `raise NotFoundException("Not found")` |
| Response helpers | `core/responses.py` | `return success_response(data=...)` |
| Permissions | `core/permissions.py` | `IsAdmin, IsUMKM, IsAdminOrUMKM` |
| Pagination | `core/pagination.py` | `StandardResultsSetPagination` |
| User model | `apps/users/models.py` | `User`, `UserRole` |

---

**Remember: Consistency is key! When in doubt, look at existing code in `apps/authentication/` or `apps/business_profiles/` for reference.**

