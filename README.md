# ExportReady.AI Backend API

AI Platform for Indonesian UMKM Export - Backend API Services

## Tech Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL (Supabase)
- **Password Hashing**: bcrypt
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

## Project Structure

```
exportready-backend/
├── config/                     # Project configuration
│   ├── settings/
│   │   ├── base.py            # Base settings (shared)
│   │   ├── development.py     # Development settings
│   │   ├── production.py      # Production settings
│   │   └── test.py            # Test settings
│   ├── urls.py                # Root URL configuration
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point
├── apps/                       # Django applications
│   ├── authentication/        # Auth endpoints (register, login, me)
│   ├── users/                 # User management
│   └── business_profiles/     # Business profile management
├── core/                       # Shared utilities
│   ├── exceptions.py          # Custom exception handling
│   ├── pagination.py          # Pagination classes
│   ├── permissions.py         # Permission classes
│   └── responses.py           # Response helpers
├── requirements/               # Requirements files
│   ├── base.txt               # Base dependencies
│   ├── development.txt        # Development dependencies
│   ├── production.txt         # Production dependencies
│   └── test.txt               # Test dependencies
├── manage.py
├── pytest.ini                 # Pytest configuration
├── pyproject.toml             # Ruff/Black configuration
└── env.example                # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (or Supabase account)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd exportready-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Development
   pip install -r requirements/development.txt
   
   # Production
   pip install -r requirements/production.txt
   ```

4. **Configure environment**
   ```bash
   # Copy env.example to .env
   copy env.example .env   # Windows
   cp env.example .env     # macOS/Linux
   
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication (`/api/v1/auth/`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register/` | Register new user | No |
| POST | `/login/` | Login user | No |
| GET | `/me/` | Get current user | Yes |
| POST | `/token/refresh/` | Refresh JWT token | No |

### Users (`/api/v1/users/`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/` | List all users | Yes | Admin |
| DELETE | `/{id}/` | Delete user | Yes | UMKM (own) |

### Business Profile (`/api/v1/business-profile/`)

| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/` | Get profile(s) | Yes | Admin, UMKM |
| POST | `/` | Create profile | Yes | UMKM |
| PUT | `/{id}/` | Update profile | Yes | UMKM (own) |
| PATCH | `/{id}/certifications/` | Update certifications | Yes | UMKM (own) |
| GET | `/dashboard/summary/` | Get dashboard summary | Yes | Admin, UMKM |

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `[]` |
| `DATABASE_URL` | Database connection URL | Required |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token lifetime | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token lifetime | `7` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | `[]` |
| `CORS_ALLOW_ALL_ORIGINS` | Allow all CORS origins | `False` |

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Success message",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "errors": { ... }
}
```

### Paginated Response
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": [ ... ],
  "pagination": {
    "count": 100,
    "page": 1,
    "limit": 10,
    "total_pages": 10,
    "next": "http://...",
    "previous": null
  }
}
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/authentication/tests/test_views.py
```

### Code Quality
```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .
ruff check . --fix

# Pre-commit hooks (if installed)
pre-commit run --all-files
```

### Database Migrations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## Production Deployment

1. Set `DEBUG=False`
2. Configure proper `ALLOWED_HOSTS`
3. Set up proper database
4. Configure CORS properly
5. Use gunicorn for serving:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```

## License

Proprietary - ExportReady.AI

