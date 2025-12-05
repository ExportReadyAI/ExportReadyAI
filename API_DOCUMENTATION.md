# Dokumentasi API ExportReady.AI

Dokumentasi lengkap semua endpoint API beserta struktur JSON body dan response.

## Base URL
```
/api/v1/
```

## Authentication
Kebanyakan endpoint memerlukan JWT token di header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### 1.1. Register User
**POST** `/api/v1/auth/register/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "UMKM",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

**Validasi:**
- `email`: Required, format email valid, harus unique
- `password`: Required, minimal 8 karakter
- `full_name`: Required, maksimal 255 karakter

---

### 1.2. Login
**POST** `/api/v1/auth/login/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "UMKM",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
  }
}
```

---

### 1.3. Get Current User (Me)
**GET** `/api/v1/auth/me/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "UMKM",
    "created_at": "2024-01-01T00:00:00Z",
    "has_business_profile": true
  }
}
```

---

### 1.4. Refresh Token
**POST** `/api/v1/auth/token/refresh/`

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 2. User Endpoints

### 2.1. List Users (Admin Only)
**GET** `/api/v1/users/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional): Nomor halaman
- `limit` (optional): Jumlah item per halaman
- `role` (optional): Filter by role (`Admin` atau `UMKM`)
- `search` (optional): Search by email atau full_name

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "count": 10,
    "next": "http://example.com/api/v1/users/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe",
        "role": "UMKM",
        "created_at": "2024-01-01T00:00:00Z",
        "is_active": true,
        "has_business_profile": true
      }
    ]
  }
}
```

---

### 2.2. Delete User
**DELETE** `/api/v1/users/{user_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User account (user@example.com) has been deleted successfully"
}
```

**Note:** 
- UMKM hanya bisa menghapus akun sendiri
- Admin bisa menghapus akun siapa saja
- Cascade delete: BusinessProfile, Product, ProductEnrichment, ExportAnalysis, Costing

---

## 3. Business Profile Endpoints

### 3.1. Create Business Profile
**POST** `/api/v1/business-profile/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "company_name": "PT Contoh Perusahaan",
  "address": "Jl. Contoh No. 123, Jakarta",
  "production_capacity_per_month": 1000,
  "year_established": 2020
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Business profile created successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "user_email": "user@example.com",
    "user_full_name": "John Doe",
    "company_name": "PT Contoh Perusahaan",
    "address": "Jl. Contoh No. 123, Jakarta",
    "production_capacity_per_month": 1000,
    "certifications": [],
    "year_established": 2020,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Validasi:**
- `company_name`: Required, maksimal 255 karakter
- `address`: Required
- `production_capacity_per_month`: Required, integer, minimal 1
- `year_established`: Required, integer, minimal 1900, tidak boleh lebih dari tahun sekarang

---

### 3.2. Get Business Profile(s)
**GET** `/api/v1/business-profile/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters (Admin only):**
- `page` (optional): Nomor halaman
- `limit` (optional): Jumlah item per halaman
- `user_id` (optional): Filter by user_id

**Response untuk UMKM (200 OK):**
```json
{
  "success": true,
  "message": "Business profile retrieved successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "user_email": "user@example.com",
    "user_full_name": "John Doe",
    "company_name": "PT Contoh Perusahaan",
    "address": "Jl. Contoh No. 123, Jakarta",
    "production_capacity_per_month": 1000,
    "certifications": ["Halal", "ISO"],
    "year_established": 2020,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Response untuk Admin (200 OK):**
```json
{
  "success": true,
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "user_id": 1,
        "user_email": "user@example.com",
        "user_full_name": "John Doe",
        "company_name": "PT Contoh Perusahaan",
        "address": "Jl. Contoh No. 123, Jakarta",
        "production_capacity_per_month": 1000,
        "certifications": ["Halal", "ISO"],
        "year_established": 2020,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

**Note:**
- UMKM: Mengembalikan profil bisnis mereka sendiri
- Admin: Mengembalikan semua profil dengan pagination

---

### 3.3. Update Business Profile
**PUT** `/api/v1/business-profile/{profile_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "company_name": "PT Perusahaan Baru",
  "address": "Jl. Baru No. 456, Bandung",
  "production_capacity_per_month": 2000,
  "year_established": 2021
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Business profile updated successfully",
  "data": {
    "id": 1,
    "user_id": 1,
    "user_email": "user@example.com",
    "user_full_name": "John Doe",
    "company_name": "PT Perusahaan Baru",
    "address": "Jl. Baru No. 456, Bandung",
    "production_capacity_per_month": 2000,
    "certifications": ["Halal", "ISO"],
    "year_established": 2021,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T01:00:00Z"
  }
}
```

**Validasi:**
- Semua field optional, hanya field yang dikirim yang akan diupdate
- `company_name`: Maksimal 255 karakter
- `production_capacity_per_month`: Integer, minimal 1
- `year_established`: Integer, minimal 1900, tidak boleh lebih dari tahun sekarang

---

### 3.4. Update Certifications
**PATCH** `/api/v1/business-profile/{profile_id}/certifications/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "certifications": ["Halal", "ISO", "HACCP", "SVLK"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Certifications updated successfully",
  "data": {
    "certifications": ["Halal", "ISO", "HACCP", "SVLK"]
  }
}
```

**Validasi:**
- `certifications`: Required, array of strings
- Nilai yang valid: `["Halal", "ISO", "HACCP", "SVLK"]`
- Duplikat akan dihapus otomatis
- Array kosong `[]` diperbolehkan

---

## 4. Dashboard Endpoints

### 4.1. Get Dashboard Summary
**GET** `/api/v1/business-profile/dashboard/summary/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response untuk UMKM (200 OK):**
```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "product_count": 0,
    "analysis_count": 0,
    "costing_count": 0,
    "has_business_profile": true
  }
}
```

**Response untuk Admin (200 OK):**
```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "total_users": 10,
    "total_umkm": 8,
    "total_business_profiles": 5,
    "total_products": 0,
    "total_analysis": 0
  }
}
```

---

## 5. API Documentation Endpoints

### 5.1. OpenAPI Schema
**GET** `/api/schema/`

Mengembalikan OpenAPI schema dalam format JSON/YAML.

---

### 5.2. Swagger UI
**GET** `/api/docs/`

Interactive API documentation menggunakan Swagger UI.

---

### 5.3. ReDoc
**GET** `/api/redoc/`

Interactive API documentation menggunakan ReDoc.

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "email": ["Email is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "message": "Invalid email or password",
  "errors": {
    "detail": "Invalid email or password"
  }
}
```

### 403 Forbidden
```json
{
  "success": false,
  "message": "You can only update your own business profile"
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "Business profile not found"
}
```

### 409 Conflict
```json
{
  "success": false,
  "message": "Email already exists",
  "errors": {
    "email": ["This email is already registered"]
  }
}
```

---

## Catatan Penting

1. **Authentication**: Semua endpoint kecuali `/auth/register/` dan `/auth/login/` memerlukan JWT token di header Authorization.

2. **Role-based Access**:
   - **UMKM**: Hanya bisa mengakses dan mengubah data sendiri
   - **Admin**: Bisa mengakses semua data

3. **Pagination**: Endpoint yang mendukung pagination menggunakan format:
   - Query params: `page`, `limit`
   - Response: `count`, `next`, `previous`, `results`

4. **Date Format**: Semua timestamp menggunakan format ISO 8601 (UTC): `YYYY-MM-DDTHH:MM:SSZ`

5. **Certifications**: Nilai yang valid untuk certifications:
   - `"Halal"`
   - `"ISO"`
   - `"HACCP"`
   - `"SVLK"`

