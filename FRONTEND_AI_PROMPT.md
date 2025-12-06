# 🤖 AI Prompt untuk Membangun Frontend ExportReady.AI

> **Gunakan prompt ini saat meminta AI (Claude, GPT, dll) untuk membangun frontend aplikasi ExportReady.AI. Copy seluruh isi file ini sebagai context untuk AI.**

---

## 📋 Context Project

Anda akan membangun **frontend aplikasi web** untuk **ExportReady.AI** - platform AI-powered untuk membantu UMKM Indonesia dalam proses ekspor produk.

**Backend sudah selesai** dan berjalan di Django REST Framework. Frontend perlu mengintegrasikan dengan backend API yang sudah ada.

---

## 🎯 Tugas Utama

Buat frontend aplikasi web yang:
1. Mengintegrasikan dengan backend API yang sudah ada
2. Mengimplementasikan semua fitur sesuai dokumentasi
3. Mengikuti best practices untuk UI/UX
4. Responsive (mobile, tablet, desktop)
5. Menggunakan TypeScript (strongly recommended)

---

## 📚 Dokumentasi yang Harus Dibaca

**WAJIB BACA** file-file berikut sebelum mulai coding:

1. **`FRONTEND_DEVELOPMENT_GUIDE.md`** - Dokumentasi lengkap:
   - Konteks bisnis & tujuan aplikasi
   - User personas & roles
   - Alur sistem & user flows
   - API reference lengkap dengan input/output
   - Business logic & rules
   - Authentication flow
   - Error handling
   - UI/UX requirements
   - Technical requirements

2. **`API_DOCUMENTATION.md`** - Referensi cepat API endpoints:
   - Semua endpoint dengan method HTTP
   - Request body structure
   - Response structure
   - Error responses

3. **`PBI_Backend.md`** - Product backlog untuk memahami fitur-fitur yang akan dibuat

---

## 🔑 Informasi Penting

### Base URL API
```
/api/v1/
```

### Authentication
- Menggunakan JWT tokens (access + refresh)
- Header: `Authorization: Bearer {access_token}`
- Auto-refresh token saat expired (401 response)

### User Roles
- **UMKM**: Pelaku usaha, hanya bisa akses data sendiri
- **Admin**: Administrator, bisa akses semua data
- **Guest**: Belum login, hanya bisa register/login

### Response Format
Semua API response mengikuti format:
```json
{
  "success": true|false,
  "message": "Human readable message",
  "data": { ... } | [ ... ],
  "errors": { ... } // hanya jika success = false
}
```

---

## 🏗️ Tech Stack yang Direkomendasikan

**Framework:**
- React + TypeScript (atau Next.js untuk SSR)
- React Router untuk routing

**State Management:**
- Redux Toolkit atau Zustand
- React Query / TanStack Query untuk server state

**HTTP Client:**
- Axios dengan interceptors untuk auth

**UI Library:**
- Material-UI, Ant Design, atau Tailwind CSS
- Pilih salah satu dan konsisten

**Form Handling:**
- React Hook Form
- Yup atau Zod untuk validation

---

## 📝 Fitur yang Harus Diimplementasikan

### 1. Authentication Pages
- [ ] **Login Page** (`/login`)
  - Form: email, password
  - POST `/api/v1/auth/login`
  - Store tokens setelah login
  - Redirect berdasarkan role dan has_business_profile

- [ ] **Register Page** (`/register`)
  - Form: email, password, full_name
  - POST `/api/v1/auth/register`
  - Validasi: email format, password min 8 chars
  - Redirect ke login setelah berhasil

### 2. Protected Routes
- [ ] Route guard untuk protected pages
- [ ] Redirect ke login jika tidak authenticated
- [ ] Check role untuk role-based routing

### 3. Dashboard
- [ ] **UMKM Dashboard** (`/dashboard`)
  - GET `/api/v1/business-profile/dashboard/summary/`
  - Display: product_count, analysis_count, costing_count, has_business_profile
  - Quick actions: Create Product, Create Analysis, Create Costing
  - CTA: "Create Business Profile" jika belum ada

- [ ] **Admin Dashboard** (`/admin/dashboard`)
  - GET `/api/v1/business-profile/dashboard/summary/`
  - Display: total_users, total_umkm, total_business_profiles, total_products, total_analysis
  - Quick links ke management pages

### 4. Business Profile Management
- [ ] **Create Business Profile** (`/business-profile/create`)
  - Form: company_name, address, production_capacity_per_month, year_established
  - POST `/api/v1/business-profile/`
  - Validasi semua field
  - Redirect ke dashboard setelah berhasil

- [ ] **View Business Profile** (`/business-profile`)
  - GET `/api/v1/business-profile/`
  - Display semua field
  - Edit button

- [ ] **Edit Business Profile** (`/business-profile/edit`)
  - Pre-fill form dengan existing data
  - PUT `/api/v1/business-profile/{profile_id}/`
  - Partial update (field optional)

- [ ] **Update Certifications** (`/business-profile/certifications`)
  - Multi-select: Halal, ISO, HACCP, SVLK
  - PATCH `/api/v1/business-profile/{profile_id}/certifications/`
  - Validasi: hanya values yang valid

### 5. User Management (Admin Only)
- [ ] **User List** (`/admin/users`)
  - GET `/api/v1/users/` dengan pagination
  - Filter: role, search
  - Table: email, full_name, role, created_at, is_active, has_business_profile
  - Delete button dengan confirmation

- [ ] **Delete User** (`/admin/users/:id/delete`)
  - DELETE `/api/v1/users/{user_id}/`
  - Confirmation dialog
  - Refresh list setelah delete

### 6. Common Components
- [ ] **Header/Navbar**
  - User info (name, role)
  - Logout button
  - Navigation menu (role-based)

- [ ] **Loading States**
  - Button loading spinner
  - Page loading skeleton
  - Data fetching indicator

- [ ] **Error Handling**
  - Toast notifications untuk errors
  - Form field errors
  - Network error handling
  - 401 auto-refresh token

- [ ] **Success Messages**
  - Toast notifications untuk success
  - Confirmation messages

---

## 🔐 Authentication Flow yang Harus Diimplementasikan

### Login Flow
```
1. User submit login form
2. POST /api/v1/auth/login
3. Store tokens (access + refresh) di localStorage
4. Store user data di state
5. Set Authorization header untuk semua requests
6. Check has_business_profile:
   - false → Redirect ke /business-profile/create
   - true → Redirect ke /dashboard
7. Check role:
   - "UMKM" → /dashboard
   - "Admin" → /admin/dashboard
```

### Token Refresh Flow
```
1. Intercept 401 response
2. POST /api/v1/auth/token/refresh/ dengan refresh_token
3. Update stored access_token
4. Retry original request
5. Jika refresh gagal → Clear tokens → Redirect ke /login
```

### Logout Flow
```
1. Clear tokens dari localStorage
2. Clear user data dari state
3. Clear Authorization header
4. Redirect ke /login
```

---

## ✅ Validasi yang Harus Diimplementasikan

### Register Form
- Email: format valid, required
- Password: min 8 karakter, required
- Full name: required, max 255 chars

### Login Form
- Email: format valid, required
- Password: required

### Business Profile Form
- Company name: required, max 255 chars
- Address: required
- Production capacity: required, integer, min 1
- Year established: required, integer, min 1900, max = current year

### Certifications
- Array of strings
- Valid values: ["Halal", "ISO", "HACCP", "SVLK"]
- Case-sensitive

---

## 🎨 UI/UX Requirements

### Design Principles
1. **Simplicity**: Clean, minimal design
2. **Accessibility**: WCAG 2.1 AA compliance
3. **Responsive**: Mobile-first, breakpoints untuk tablet & desktop
4. **User-Friendly**: Clear labels, helpful errors, loading states

### Key Pages Layout
- **Login/Register**: Centered form, simple layout
- **Dashboard**: Cards layout, summary statistics
- **Forms**: Clear labels, inline validation, error messages
- **Tables**: Sortable columns, pagination, filters

### Loading States
- Button: Disable + spinner saat loading
- Page: Skeleton screens atau spinner
- Data fetch: Loading indicator

### Error Handling
- **400**: Display field-level errors di form
- **401**: Auto-refresh token, jika gagal redirect ke login
- **403**: Show "You don't have permission" message
- **404**: Show "Resource not found" dengan back button
- **409**: Show "Resource already exists" message
- **Network**: Show "Network error" dengan retry button

---

## 📁 Project Structure yang Direkomendasikan

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios instance dengan interceptors
│   │   ├── auth.ts            # Auth endpoints
│   │   ├── users.ts           # User endpoints
│   │   └── businessProfile.ts # Business profile endpoints
│   ├── components/
│   │   ├── common/            # Button, Input, Card, etc.
│   │   ├── forms/             # Form components
│   │   └── layout/            # Header, Sidebar, Footer
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── dashboard/
│   │   │   ├── UMKMDashboard.tsx
│   │   │   └── AdminDashboard.tsx
│   │   └── business-profile/
│   │       ├── Create.tsx
│   │       ├── View.tsx
│   │       └── Edit.tsx
│   ├── hooks/
│   │   ├── useAuth.ts         # Auth hook
│   │   └── useApi.ts          # API hook
│   ├── store/
│   │   ├── authSlice.ts       # Auth state
│   │   └── userSlice.ts       # User state
│   ├── utils/
│   │   ├── validation.ts      # Validation helpers
│   │   └── formatters.ts      # Date, number formatters
│   ├── types/
│   │   ├── api.ts             # API types
│   │   └── user.ts            # User types
│   └── App.tsx
├── public/
└── package.json
```

---

## 🧪 Testing Checklist

Setelah implementasi, pastikan test:
- [ ] Login dengan valid/invalid credentials
- [ ] Register dengan valid/invalid data
- [ ] Token refresh flow
- [ ] Protected routes redirect
- [ ] Create business profile
- [ ] Update business profile
- [ ] Update certifications
- [ ] User list (Admin)
- [ ] Delete user (Admin)
- [ ] Error handling (400, 401, 403, 404, 409)
- [ ] Loading states
- [ ] Responsive design

---

## 🚀 Langkah-Langkah Implementasi

### Phase 1: Setup & Authentication
1. Setup project (React + TypeScript)
2. Setup API client dengan interceptors
3. Implement login page
4. Implement register page
5. Implement token management
6. Implement protected routes
7. Test authentication flow

### Phase 2: Dashboard & Business Profile
1. Implement dashboard (UMKM & Admin)
2. Implement create business profile
3. Implement view business profile
4. Implement edit business profile
5. Implement update certifications
6. Test semua business profile flows

### Phase 3: User Management (Admin)
1. Implement user list dengan pagination
2. Implement user filters
3. Implement delete user
4. Test admin features

### Phase 4: Polish & Testing
1. Add loading states
2. Improve error handling
3. Add success messages
4. Responsive design testing
5. Accessibility testing
6. End-to-end testing

---

## 📖 Referensi API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register user
- `POST /api/v1/auth/login/` - Login
- `GET /api/v1/auth/me/` - Get current user
- `POST /api/v1/auth/token/refresh/` - Refresh token

### Users (Admin)
- `GET /api/v1/users/` - List users
- `DELETE /api/v1/users/{user_id}/` - Delete user

### Business Profile
- `POST /api/v1/business-profile/` - Create profile
- `GET /api/v1/business-profile/` - Get profile(s)
- `PUT /api/v1/business-profile/{profile_id}/` - Update profile
- `PATCH /api/v1/business-profile/{profile_id}/certifications/` - Update certifications
- `GET /api/v1/business-profile/dashboard/summary/` - Dashboard summary

**Detail lengkap lihat `API_DOCUMENTATION.md`**

---

## ⚠️ Important Notes

1. **Backend sudah selesai** - jangan buat mock API, gunakan backend yang sudah ada
2. **Follow API contract** - jangan ubah request/response structure
3. **Handle errors properly** - semua error response harus ditangani
4. **Token management** - implement auto-refresh untuk better UX
5. **Role-based access** - check role di frontend tapi backend juga validate
6. **Validation** - validate di frontend tapi backend juga validate (double validation)
7. **Loading states** - selalu show loading indicator untuk async operations
8. **Error messages** - show user-friendly error messages, jangan technical errors

---

## 🎯 Success Criteria

Frontend dianggap selesai jika:
- ✅ Semua fitur di checklist sudah diimplementasikan
- ✅ Semua API endpoints terintegrasi dengan benar
- ✅ Authentication flow bekerja dengan baik
- ✅ Error handling comprehensive
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Loading states untuk semua async operations
- ✅ User-friendly error messages
- ✅ Role-based access control bekerja
- ✅ Code clean, maintainable, dengan TypeScript types
- ✅ Testing checklist semua passed

---

## 📞 Jika Ada Pertanyaan

Jika ada yang tidak jelas:
1. Baca `FRONTEND_DEVELOPMENT_GUIDE.md` untuk detail lengkap
2. Baca `API_DOCUMENTATION.md` untuk API reference
3. Baca `PBI_Backend.md` untuk memahami business requirements

---

**Mulai dengan membaca `FRONTEND_DEVELOPMENT_GUIDE.md` secara lengkap, kemudian mulai implementasi dari Phase 1.**

**Good luck! 🚀**

