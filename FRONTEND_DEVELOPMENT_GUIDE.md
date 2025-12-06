# 🎨 ExportReady.AI - Frontend Development Guide

> **Dokumentasi lengkap untuk membangun frontend aplikasi ExportReady.AI. Gunakan dokumentasi ini sebagai referensi utama untuk memahami konteks bisnis, alur sistem, API endpoints, dan business logic.**

---

## 📋 Daftar Isi

1. [Konteks Bisnis & Tujuan Aplikasi](#1-konteks-bisnis--tujuan-aplikasi)
2. [User Personas & Roles](#2-user-personas--roles)
3. [Alur Sistem & User Flows](#3-alur-sistem--user-flows)
4. [API Reference Lengkap](#4-api-reference-lengkap)
5. [Business Logic & Rules](#5-business-logic--rules)
6. [Authentication Flow](#6-authentication-flow)
7. [Error Handling](#7-error-handling)
8. [UI/UX Requirements](#8-uiux-requirements)
9. [Technical Requirements](#9-technical-requirements)

---

## 1. Konteks Bisnis & Tujuan Aplikasi

### 1.1. Apa itu ExportReady.AI?

**ExportReady.AI** adalah platform AI-powered untuk membantu UMKM (Usaha Mikro Kecil Menengah) Indonesia dalam proses ekspor produk mereka ke pasar internasional.

### 1.2. Masalah yang Diselesaikan

UMKM Indonesia menghadapi banyak kendala dalam ekspor:
- **Kesulitan menentukan HS Code** yang tepat untuk produk
- **Tidak memahami regulasi** negara tujuan ekspor
- **Kesulitan menghitung harga ekspor** (EXW, FOB, CIF)
- **Tidak tahu kelayakan produk** untuk diekspor ke negara tertentu
- **Kurangnya dokumentasi profesional** untuk buyer internasional

### 1.3. Solusi yang Diberikan

Platform ini menyediakan:
1. **AI-powered Product Enrichment**: Auto-generate HS Code, SKU, dan deskripsi B2B dalam bahasa Inggris
2. **Export Readiness Analysis**: Analisis kelayakan produk untuk ekspor ke negara tertentu
3. **Compliance Checker**: Cek compliance dengan regulasi negara tujuan
4. **Pricing Calculator**: Kalkulasi harga EXW, FOB, CIF dengan optimasi container
5. **Professional Documentation**: Generate PDF costing report untuk buyer

### 1.4. Value Proposition

- **Untuk UMKM**: Platform mudah digunakan yang membantu mereka siap ekspor tanpa perlu pengetahuan teknis mendalam
- **Untuk Admin**: Dashboard untuk mengelola master data (HS Code, Country Regulations) dan monitoring sistem

---

## 2. User Personas & Roles

### 2.1. UMKM (Pelaku Usaha)

**Karakteristik:**
- Pemilik usaha kecil/menengah di Indonesia
- Ingin mengekspor produk tapi kurang pengalaman
- Butuh panduan step-by-step
- Tidak terlalu tech-savvy

**Kebutuhan:**
- Interface yang sederhana dan intuitif
- Panduan jelas untuk setiap langkah
- Hasil yang mudah dipahami (score, rekomendasi)
- Dokumentasi siap pakai untuk buyer

**Akses:**
- ✅ Semua fitur untuk mengelola produk, analisis, dan costing sendiri
- ❌ Tidak bisa akses data UMKM lain
- ❌ Tidak bisa akses master data management

### 2.2. Admin (Administrator)

**Karakteristik:**
- Staff internal ExportReady.AI
- Bertanggung jawab mengelola master data
- Monitoring sistem dan user

**Kebutuhan:**
- Dashboard overview sistem
- Tools untuk manage HS Code, Country, Regulations
- User management
- Analytics dan reporting

**Akses:**
- ✅ Semua fitur UMKM
- ✅ User management
- ✅ Master data management (HS Code, Countries, Regulations)
- ✅ View semua data dari semua UMKM

### 2.3. Guest (Belum Login)

**Karakteristik:**
- Visitor yang belum register/login
- Ingin tahu tentang platform

**Akses:**
- ✅ Register akun baru
- ✅ Login
- ❌ Tidak bisa akses fitur apapun

---

## 3. Alur Sistem & User Flows

### 3.1. Onboarding Flow (UMKM)

```
1. Register
   └─> POST /api/v1/auth/register
       └─> Input: email, password, full_name
       └─> Response: user data (role = "UMKM")

2. Login
   └─> POST /api/v1/auth/login
       └─> Input: email, password
       └─> Response: user data + JWT tokens
       └─> Store tokens (access + refresh) di localStorage/sessionStorage

3. Check Business Profile
   └─> GET /api/v1/auth/me
       └─> Response: user data + has_business_profile (boolean)
       └─> Jika has_business_profile = false:
           └─> Redirect ke "Create Business Profile"
       └─> Jika has_business_profile = true:
           └─> Redirect ke Dashboard

4. Create Business Profile (jika belum ada)
   └─> POST /api/v1/business-profile/
       └─> Input: company_name, address, production_capacity_per_month, year_established
       └─> Response: business profile data
       └─> Redirect ke Dashboard
```

### 3.2. Main User Flow (UMKM)

```
Dashboard
├─> View Summary
│   └─> GET /api/v1/business-profile/dashboard/summary/
│       └─> Display: product_count, analysis_count, costing_count, has_business_profile
│
├─> Manage Business Profile
│   ├─> View Profile
│   │   └─> GET /api/v1/business-profile/
│   │
│   ├─> Update Profile
│   │   └─> PUT /api/v1/business-profile/{profile_id}/
│   │
│   └─> Update Certifications
│       └─> PATCH /api/v1/business-profile/{profile_id}/certifications/
│
├─> Manage Products (Future Module - belum ada di backend saat ini)
│   ├─> List Products
│   ├─> Create Product
│   ├─> Update Product
│   └─> Delete Product
│
├─> Export Analysis (Future Module)
│   ├─> Create Analysis
│   ├─> View Analysis
│   └─> Compare Countries
│
└─> Costing (Future Module)
    ├─> Create Costing
    ├─> View Costing
    └─> Generate PDF
```

### 3.3. Admin Flow

```
Admin Dashboard
├─> View System Summary
│   └─> GET /api/v1/business-profile/dashboard/summary/
│       └─> Display: total_users, total_umkm, total_business_profiles, total_products, total_analysis
│
├─> User Management
│   ├─> List Users
│   │   └─> GET /api/v1/users/?page=1&limit=10&role=UMKM&search=...
│   │
│   └─> Delete User
│       └─> DELETE /api/v1/users/{user_id}/
│
├─> Business Profile Management
│   └─> GET /api/v1/business-profile/?page=1&limit=10&user_id=...
│
└─> Master Data Management (Future Module)
    ├─> HS Code Management
    ├─> Country Management
    └─> Regulation Management
```

### 3.4. Authentication Flow

```
1. User Login
   └─> POST /api/v1/auth/login
   └─> Store: access_token, refresh_token

2. Set Authorization Header
   └─> Header: Authorization: Bearer {access_token}
   └─> Gunakan untuk semua authenticated requests

3. Token Expired (401 Unauthorized)
   └─> POST /api/v1/auth/token/refresh/
   └─> Body: { "refresh": refresh_token }
   └─> Response: new access_token
   └─> Update stored access_token

4. Refresh Token Expired
   └─> Redirect ke Login Page
   └─> Clear stored tokens
```

---

## 4. API Reference Lengkap

### 4.1. Base Configuration

**Base URL:**
```
/api/v1/
```

**Authentication Header:**
```
Authorization: Bearer {access_token}
```

**Content-Type:**
```
application/json
```

**Response Format:**
Semua response mengikuti format standar:
```json
{
  "success": true|false,
  "message": "Human readable message",
  "data": { ... } | [ ... ],
  "errors": { ... } // hanya jika success = false
}
```

---

### 4.2. Authentication Endpoints

#### 4.2.1. Register User

**Endpoint:** `POST /api/v1/auth/register/`

**Authentication:** ❌ Tidak diperlukan

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Validasi:**
- `email`: Required, format email valid, harus unique
- `password`: Required, minimal 8 karakter
- `full_name`: Required, maksimal 255 karakter

**Success Response (201):**
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

**Error Response (400):**
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

**Error Response (409):**
```json
{
  "success": false,
  "message": "Email already exists",
  "errors": {
    "email": ["This email is already registered"]
  }
}
```

**Frontend Action:**
- Setelah register berhasil, redirect ke Login Page
- Tampilkan success message: "Registrasi berhasil! Silakan login."

---

#### 4.2.2. Login

**Endpoint:** `POST /api/v1/auth/login/`

**Authentication:** ❌ Tidak diperlukan

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
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

**Error Response (401):**
```json
{
  "success": false,
  "message": "Invalid email or password",
  "errors": {
    "detail": "Invalid email or password"
  }
}
```

**Frontend Action:**
1. Store `tokens.access` dan `tokens.refresh` di localStorage/sessionStorage
2. Store `user` data di state management (Redux/Zustand/Context)
3. Set Authorization header untuk semua subsequent requests
4. Check `user.has_business_profile`:
   - Jika `false`: Redirect ke "Create Business Profile"
   - Jika `true`: Redirect ke Dashboard
5. Check `user.role`:
   - Jika `"UMKM"`: Redirect ke UMKM Dashboard
   - Jika `"Admin"`: Redirect ke Admin Dashboard

---

#### 4.2.3. Get Current User (Me)

**Endpoint:** `GET /api/v1/auth/me/`

**Authentication:** ✅ Required

**Headers:**
```
Authorization: Bearer {access_token}
```

**Success Response (200):**
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

**Error Response (401):**
```json
{
  "success": false,
  "message": "Unauthorized - invalid or expired token"
}
```

**Frontend Action:**
- Gunakan untuk:
  - Check authentication status saat app load
  - Get user info untuk display di header/navbar
  - Check `has_business_profile` untuk conditional routing
  - Check `role` untuk role-based UI rendering

---

#### 4.2.4. Refresh Token

**Endpoint:** `POST /api/v1/auth/token/refresh/`

**Authentication:** ❌ Tidak diperlukan (tapi butuh refresh token)

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Success Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Response (401):**
```json
{
  "detail": "Token is invalid or expired"
}
```

**Frontend Action:**
- Implementasi interceptor untuk auto-refresh:
  1. Intercept 401 response
  2. Call refresh token endpoint
  3. Update stored access_token
  4. Retry original request dengan new token
  5. Jika refresh gagal: redirect ke Login

---

### 4.3. User Endpoints

#### 4.3.1. List Users (Admin Only)

**Endpoint:** `GET /api/v1/users/`

**Authentication:** ✅ Required (Admin only)

**Query Parameters:**
- `page` (optional, integer): Nomor halaman
- `limit` (optional, integer): Jumlah item per halaman
- `role` (optional, string): Filter by role (`Admin` atau `UMKM`)
- `search` (optional, string): Search by email atau full_name

**Example Request:**
```
GET /api/v1/users/?page=1&limit=10&role=UMKM&search=john
```

**Success Response (200):**
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

**Frontend Action:**
- Tampilkan table dengan pagination
- Filter by role (dropdown: All, Admin, UMKM)
- Search box untuk email/full_name
- Display: email, full_name, role, created_at, is_active, has_business_profile
- Action button: Delete (dengan confirmation)

---

#### 4.3.2. Delete User

**Endpoint:** `DELETE /api/v1/users/{user_id}/`

**Authentication:** ✅ Required

**Path Parameters:**
- `user_id` (integer): ID user yang akan dihapus

**Success Response (200):**
```json
{
  "success": true,
  "message": "User account (user@example.com) has been deleted successfully"
}
```

**Error Response (403):**
```json
{
  "success": false,
  "message": "You can only delete your own account"
}
```

**Business Logic:**
- UMKM hanya bisa delete akun sendiri
- Admin bisa delete akun siapa saja
- Cascade delete: BusinessProfile, Product, ProductEnrichment, ExportAnalysis, Costing

**Frontend Action:**
- Show confirmation dialog sebelum delete
- Jika UMKM delete sendiri: redirect ke Login setelah berhasil
- Jika Admin delete user lain: refresh user list

---

### 4.4. Business Profile Endpoints

#### 4.4.1. Create Business Profile

**Endpoint:** `POST /api/v1/business-profile/`

**Authentication:** ✅ Required (UMKM only)

**Request Body:**
```json
{
  "company_name": "PT Contoh Perusahaan",
  "address": "Jl. Contoh No. 123, Jakarta",
  "production_capacity_per_month": 1000,
  "year_established": 2020
}
```

**Validasi:**
- `company_name`: Required, maksimal 255 karakter
- `address`: Required
- `production_capacity_per_month`: Required, integer, minimal 1
- `year_established`: Required, integer, minimal 1900, tidak boleh lebih dari tahun sekarang

**Success Response (201):**
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

**Error Response (409):**
```json
{
  "success": false,
  "message": "You already have a business profile"
}
```

**Frontend Action:**
- Form dengan validasi:
  - Company name: text input, max 255 chars
  - Address: textarea
  - Production capacity: number input, min 1
  - Year established: number input, min 1900, max = current year
- Setelah berhasil: redirect ke Dashboard atau Business Profile Detail
- Tampilkan success message

---

#### 4.4.2. Get Business Profile(s)

**Endpoint:** `GET /api/v1/business-profile/`

**Authentication:** ✅ Required

**Query Parameters (Admin only):**
- `page` (optional, integer): Nomor halaman
- `limit` (optional, integer): Jumlah item per halaman
- `user_id` (optional, integer): Filter by user_id

**Response untuk UMKM (200):**
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

**Response untuk Admin (200):**
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

**Error Response (404) - UMKM:**
```json
{
  "success": false,
  "message": "Business profile not found. Please create one first."
}
```

**Frontend Action:**
- **UMKM**: 
  - Tampilkan single profile card/detail page
  - Jika 404: show "Create Business Profile" button
- **Admin**: 
  - Tampilkan table dengan pagination
  - Filter by user_id
  - Display: company_name, user_email, user_full_name, certifications, created_at

---

#### 4.4.3. Update Business Profile

**Endpoint:** `PUT /api/v1/business-profile/{profile_id}/`

**Authentication:** ✅ Required (UMKM only, own profile)

**Path Parameters:**
- `profile_id` (integer): ID business profile

**Request Body:**
```json
{
  "company_name": "PT Perusahaan Baru",
  "address": "Jl. Baru No. 456, Bandung",
  "production_capacity_per_month": 2000,
  "year_established": 2021
}
```

**Note:** Semua field optional, hanya field yang dikirim yang akan diupdate

**Success Response (200):**
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

**Error Response (403):**
```json
{
  "success": false,
  "message": "You can only update your own business profile"
}
```

**Frontend Action:**
- Pre-fill form dengan existing data
- Allow partial update (tidak semua field harus diisi)
- Show success message setelah update
- Refresh profile data

---

#### 4.4.4. Update Certifications

**Endpoint:** `PATCH /api/v1/business-profile/{profile_id}/certifications/`

**Authentication:** ✅ Required (UMKM only, own profile)

**Path Parameters:**
- `profile_id` (integer): ID business profile

**Request Body:**
```json
{
  "certifications": ["Halal", "ISO", "HACCP", "SVLK"]
}
```

**Validasi:**
- `certifications`: Required, array of strings
- Nilai yang valid: `["Halal", "ISO", "HACCP", "SVLK"]`
- Duplikat akan dihapus otomatis
- Array kosong `[]` diperbolehkan

**Success Response (200):**
```json
{
  "success": true,
  "message": "Certifications updated successfully",
  "data": {
    "certifications": ["Halal", "ISO", "HACCP", "SVLK"]
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "certifications": ["Invalid certifications: ['INVALID']. Valid options are: ['Halal', 'ISO', 'HACCP', 'SVLK']"]
  }
}
```

**Frontend Action:**
- Multi-select checkbox atau tags input
- Options: Halal, ISO, HACCP, SVLK
- Show validation error jika ada invalid value
- Update certifications display setelah berhasil

---

### 4.5. Dashboard Endpoints

#### 4.5.1. Get Dashboard Summary

**Endpoint:** `GET /api/v1/business-profile/dashboard/summary/`

**Authentication:** ✅ Required

**Response untuk UMKM (200):**
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

**Response untuk Admin (200):**
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

**Frontend Action:**
- **UMKM Dashboard**: 
  - Display cards: Products, Analyses, Costings
  - Show "Create Business Profile" CTA jika `has_business_profile = false`
- **Admin Dashboard**: 
  - Display cards: Total Users, Total UMKM, Total Business Profiles, Total Products, Total Analyses
  - Link ke respective management pages

---

## 5. Business Logic & Rules

### 5.1. Authentication & Authorization

1. **JWT Token Management:**
   - Access token lifetime: 60 menit (default)
   - Refresh token lifetime: 7 hari (default)
   - Store tokens securely (localStorage/sessionStorage atau httpOnly cookies)
   - Auto-refresh access token sebelum expired

2. **Role-based Access:**
   - **UMKM**: Hanya bisa akses dan modify data sendiri
   - **Admin**: Bisa akses semua data
   - Check role di frontend untuk conditional rendering, tapi backend juga validate

3. **Route Protection:**
   - Protected routes: semua kecuali `/login` dan `/register`
   - Redirect ke login jika tidak authenticated
   - Redirect berdasarkan role setelah login

### 5.2. Business Profile Rules

1. **One-to-One Relationship:**
   - Setiap user (UMKM) hanya bisa punya 1 business profile
   - Jika sudah ada profile, tidak bisa create lagi (409 Conflict)

2. **Required for Features:**
   - User harus punya business profile sebelum bisa:
     - Create products
     - Create export analysis
     - Create costing
   - Check `has_business_profile` dari `/auth/me` response

3. **Certifications:**
   - Valid values: `["Halal", "ISO", "HACCP", "SVLK"]`
   - Case-sensitive
   - Duplikat akan dihapus otomatis
   - Bisa empty array `[]`

### 5.3. Validation Rules

1. **Email:**
   - Format email valid
   - Unique (tidak boleh duplicate)
   - Case-insensitive (backend akan normalize ke lowercase)

2. **Password:**
   - Minimal 8 karakter
   - Disarankan: kombinasi huruf, angka, karakter khusus

3. **Year Established:**
   - Minimal 1900
   - Maksimal = tahun sekarang
   - Integer

4. **Production Capacity:**
   - Minimal 1
   - Integer

### 5.4. Data Format

1. **Date/Time:**
   - Format: ISO 8601 (UTC)
   - Example: `"2024-01-01T00:00:00Z"`
   - Parse dan format untuk display di frontend

2. **Pagination:**
   - Default page: 1
   - Default limit: 10 (atau sesuai backend default)
   - Response structure:
     ```json
     {
       "count": 100,
       "next": "url" | null,
       "previous": "url" | null,
       "results": [...]
     }
     ```

---

## 6. Authentication Flow

### 6.1. Initial App Load

```
1. App Start
   └─> Check localStorage/sessionStorage for tokens
   ├─> If tokens exist:
   │   └─> GET /api/v1/auth/me
   │       ├─> Success (200):
   │       │   └─> Store user data
   │       │   └─> Check has_business_profile
   │       │   └─> Redirect to appropriate dashboard
   │       └─> Error (401):
   │           └─> Clear tokens
   │           └─> Redirect to Login
   └─> If no tokens:
       └─> Redirect to Login
```

### 6.2. Login Flow

```
1. User submits login form
   └─> POST /api/v1/auth/login
   ├─> Success (200):
   │   ├─> Store tokens (access + refresh)
   │   ├─> Store user data
   │   ├─> Set Authorization header
   │   ├─> Check has_business_profile:
   │   │   ├─> false: Redirect to "Create Business Profile"
   │   │   └─> true: Redirect to Dashboard
   │   └─> Check role:
   │       ├─> "UMKM": UMKM Dashboard
   │       └─> "Admin": Admin Dashboard
   └─> Error (401):
       └─> Display error message
       └─> Stay on login page
```

### 6.3. Token Refresh Flow

```
1. API Request returns 401
   └─> Intercept response
   └─> POST /api/v1/auth/token/refresh/
       └─> Body: { "refresh": refresh_token }
       ├─> Success (200):
       │   ├─> Update stored access_token
       │   ├─> Retry original request
       │   └─> Continue normal flow
       └─> Error (401):
           └─> Clear all tokens
           └─> Redirect to Login
```

### 6.4. Logout Flow

```
1. User clicks logout
   └─> Clear tokens from storage
   └─> Clear user data from state
   └─> Clear Authorization header
   └─> Redirect to Login
```

---

## 7. Error Handling

### 7.1. HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue normal flow |
| 201 | Created | Show success message, redirect or refresh |
| 400 | Bad Request | Display validation errors |
| 401 | Unauthorized | Try refresh token, if fails redirect to login |
| 403 | Forbidden | Show error: "You don't have permission" |
| 404 | Not Found | Show error: "Resource not found" |
| 409 | Conflict | Show error: "Resource already exists" |
| 500 | Server Error | Show generic error: "Something went wrong" |

### 7.2. Error Response Structure

```json
{
  "success": false,
  "message": "Human readable error message",
  "errors": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

### 7.3. Frontend Error Handling

1. **Validation Errors (400):**
   - Display field-level errors di form
   - Highlight invalid fields
   - Show error messages below each field

2. **Authentication Errors (401):**
   - Try refresh token
   - If refresh fails: redirect to login
   - Show message: "Session expired. Please login again."

3. **Permission Errors (403):**
   - Show error message
   - Hide/disable action buttons
   - Log error for debugging

4. **Not Found (404):**
   - Show 404 page atau error message
   - Provide "Go back" atau "Go to Dashboard" link

5. **Network Errors:**
   - Show: "Network error. Please check your connection."
   - Provide retry button

6. **Generic Error Handler:**
   - Catch-all untuk unexpected errors
   - Show: "Something went wrong. Please try again."
   - Log error details untuk debugging

---

## 8. UI/UX Requirements

### 8.1. Design Principles

1. **Simplicity:**
   - Clean, minimal design
   - Focus on essential features
   - Avoid clutter

2. **Accessibility:**
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader support
   - High contrast colors

3. **Responsive:**
   - Mobile-first approach
   - Breakpoints: mobile, tablet, desktop
   - Touch-friendly buttons (min 44x44px)

4. **User-Friendly:**
   - Clear labels dan instructions
   - Helpful error messages
   - Loading states untuk async operations
   - Success confirmations

### 8.2. Key Pages & Components

#### 8.2.1. Login Page
- Email input
- Password input (with show/hide toggle)
- "Remember me" checkbox (optional)
- "Forgot password?" link (future feature)
- Login button
- Link to Register page
- Error message display area

#### 8.2.2. Register Page
- Email input
- Password input (with strength indicator)
- Full name input
- Register button
- Link to Login page
- Terms & conditions checkbox (optional)
- Error message display area

#### 8.2.3. Dashboard (UMKM)
- Welcome message dengan user name
- Summary cards:
  - Products count (with link)
  - Analyses count (with link)
  - Costings count (with link)
- Quick actions:
  - Create Product
  - Create Analysis
  - Create Costing
- Recent activity (optional)
- Business profile status card

#### 8.2.4. Dashboard (Admin)
- System overview cards:
  - Total Users
  - Total UMKM
  - Total Business Profiles
  - Total Products
  - Total Analyses
- Quick links:
  - User Management
  - Business Profile Management
  - Master Data Management

#### 8.2.5. Business Profile Form
- Company name input
- Address textarea
- Production capacity number input
- Year established number input
- Certifications multi-select
- Save button
- Cancel button

#### 8.2.6. User List (Admin)
- Search bar
- Role filter dropdown
- Table dengan columns:
  - Email
  - Full Name
  - Role
  - Created At
  - Status (Active/Inactive)
  - Actions (Delete)
- Pagination controls

### 8.3. Loading States

1. **Button Loading:**
   - Disable button saat loading
   - Show spinner atau loading text
   - Prevent multiple submissions

2. **Page Loading:**
   - Show skeleton screens atau spinner
   - Display "Loading..." message

3. **Data Fetching:**
   - Show loading indicator
   - Keep previous data visible (optional)
   - Show error jika fetch fails

### 8.4. Success States

1. **Form Submission:**
   - Show success toast/notification
   - Redirect atau refresh data
   - Clear form (jika create new)

2. **Data Update:**
   - Show success message
   - Update UI dengan new data
   - Highlight changed fields (optional)

---

## 9. Technical Requirements

### 9.1. Recommended Tech Stack

**Frontend Framework:**
- React, Vue, atau Next.js (SSR recommended untuk SEO)
- TypeScript (strongly recommended)

**State Management:**
- Redux Toolkit, Zustand, atau Context API
- React Query / TanStack Query untuk server state

**HTTP Client:**
- Axios atau Fetch API
- Interceptors untuk auth dan error handling

**UI Library:**
- Material-UI, Ant Design, atau Tailwind CSS
- Consistent design system

**Form Handling:**
- React Hook Form atau Formik
- Yup atau Zod untuk validation

**Routing:**
- React Router atau Next.js Router
- Protected route components

### 9.2. Project Structure

```
frontend/
├── src/
│   ├── api/              # API client & endpoints
│   │   ├── client.ts     # Axios instance dengan interceptors
│   │   ├── auth.ts       # Auth endpoints
│   │   ├── users.ts      # User endpoints
│   │   └── businessProfile.ts
│   ├── components/       # Reusable components
│   │   ├── common/       # Button, Input, Card, etc.
│   │   ├── forms/        # Form components
│   │   └── layout/       # Header, Sidebar, Footer
│   ├── pages/            # Page components
│   │   ├── auth/
│   │   ├── dashboard/
│   │   └── business-profile/
│   ├── hooks/            # Custom hooks
│   │   ├── useAuth.ts
│   │   └── useApi.ts
│   ├── store/            # State management
│   │   ├── authSlice.ts
│   │   └── userSlice.ts
│   ├── utils/            # Utility functions
│   │   ├── validation.ts
│   │   └── formatters.ts
│   ├── types/            # TypeScript types
│   │   ├── api.ts
│   │   └── user.ts
│   └── App.tsx
├── public/
└── package.json
```

### 9.3. API Client Setup

**Example with Axios:**

```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/v1/auth/token/refresh/', {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);
        originalRequest.headers.Authorization = `Bearer ${access}`;

        return apiClient(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 9.4. Environment Variables

```env
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_ENV=development
```

### 9.5. TypeScript Types

```typescript
// types/api.ts
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data?: T;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// types/user.ts
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'Admin' | 'UMKM';
  created_at: string;
  has_business_profile?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

// types/businessProfile.ts
export interface BusinessProfile {
  id: number;
  user_id: number;
  user_email: string;
  user_full_name: string;
  company_name: string;
  address: string;
  production_capacity_per_month: number;
  certifications: ('Halal' | 'ISO' | 'HACCP' | 'SVLK')[];
  year_established: number;
  created_at: string;
  updated_at: string;
}
```

---

## 10. Testing Checklist

### 10.1. Authentication
- [ ] Register dengan valid data
- [ ] Register dengan email duplicate (409)
- [ ] Register dengan password < 8 karakter (400)
- [ ] Login dengan valid credentials
- [ ] Login dengan invalid credentials (401)
- [ ] Get current user (me) dengan valid token
- [ ] Get current user dengan invalid token (401)
- [ ] Token refresh flow
- [ ] Logout clear tokens

### 10.2. Business Profile
- [ ] Create business profile (UMKM)
- [ ] Create business profile duplicate (409)
- [ ] Get business profile (UMKM - own)
- [ ] Get business profile (Admin - all)
- [ ] Update business profile (own)
- [ ] Update business profile (other user's - 403)
- [ ] Update certifications dengan valid values
- [ ] Update certifications dengan invalid values (400)

### 10.3. User Management (Admin)
- [ ] List users dengan pagination
- [ ] Filter users by role
- [ ] Search users by email/name
- [ ] Delete user (Admin)
- [ ] Delete own account (UMKM)

### 10.4. Error Handling
- [ ] Network error handling
- [ ] 400 validation errors
- [ ] 401 unauthorized
- [ ] 403 forbidden
- [ ] 404 not found
- [ ] 500 server error

---

## 11. Deployment Considerations

### 11.1. Environment Configuration
- Development: `http://localhost:8000`
- Staging: `https://api-staging.exportready.ai`
- Production: `https://api.exportready.ai`

### 11.2. CORS Configuration
- Backend harus allow frontend origin
- Credentials: include jika menggunakan cookies

### 11.3. Security
- Store tokens securely (consider httpOnly cookies)
- HTTPS only di production
- Validate semua input di frontend (tapi backend juga validate)
- Sanitize user input untuk prevent XSS

---

## 12. Future Modules (Not Yet Implemented)

Modules berikut akan ditambahkan di masa depan:
- **Products Management** (Module 2)
- **Export Analysis** (Module 3)
- **Costing Calculator** (Module 4)
- **Master Data Management** (Module 5)

Dokumentasi untuk modules ini akan diupdate ketika backend sudah ready.


**Last Updated:** December 2024  
**Version:** 1.0  
**Maintained by:** ExportReady.AI Development Team

