
---

# API Documentation - Dashboard Module

Base URL: `/api/v1/business-profile/`

## Authentication
Semua endpoint memerlukan JWT token:
```
Authorization: Bearer <access_token>
```

---

## Dashboard Summary

### Get Dashboard Summary
```
GET /api/v1/business-profile/dashboard/summary/
```

Return summary statistics untuk dashboard, berbeda berdasarkan role user.

---

## Response untuk UMKM

```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "has_business_profile": true,
    "products": {
      "total": 3,
      "without_catalog": 1
    },
    "catalogs": {
      "total": 2,
      "published": 0,
      "draft": 2
    },
    "buyer_requests": {
      "total": 3,
      "pending": 3
    },
    "educational_materials": {
      "total_modules": 3,
      "total_articles": 8
    }
  }
}
```

### Field Descriptions (UMKM)

| Field | Type | Description |
|-------|------|-------------|
| has_business_profile | boolean | Apakah user sudah punya business profile |
| products.total | int | Total produk yang dimiliki |
| products.without_catalog | int | Produk yang belum punya catalog (actionable!) |
| catalogs.total | int | Total catalog |
| catalogs.published | int | Catalog yang sudah publish |
| catalogs.draft | int | Catalog yang masih draft |
| buyer_requests.total | int | Total buyer requests yang bisa dilihat |
| buyer_requests.pending | int | Buyer requests yang masih open/pending |
| educational_materials.total_modules | int | Total modul edukasi tersedia |
| educational_materials.total_articles | int | Total artikel edukasi tersedia |

### Jika UMKM Belum Punya Business Profile

```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "has_business_profile": false,
    "products": {
      "total": 0,
      "without_catalog": 0
    },
    "catalogs": {
      "total": 0,
      "published": 0,
      "draft": 0
    },
    "buyer_requests": {
      "total": 0,
      "pending": 0
    },
    "educational_materials": {
      "total_modules": 3,
      "total_articles": 8
    }
  }
}
```

---

## Response untuk Admin

```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully",
  "data": {
    "users": {
      "total": 25,
      "umkm": 15,
      "buyers": 5,
      "forwarders": 3
    },
    "business_profiles": {
      "total": 12
    },
    "products": {
      "total": 50,
      "with_enrichment": 20,
      "with_market_intelligence": 15,
      "with_pricing": 10
    },
    "catalogs": {
      "total": 30,
      "published": 18,
      "draft": 12
    },
    "buyer_requests": {
      "total": 8
    },
    "educational_materials": {
      "total_modules": 5,
      "total_articles": 25
    }
  }
}
```

### Field Descriptions (Admin)

| Field | Type | Description |
|-------|------|-------------|
| users.total | int | Total semua user di sistem |
| users.umkm | int | Total user dengan role UMKM |
| users.buyers | int | Total user dengan role Buyer |
| users.forwarders | int | Total user dengan role Forwarder |
| business_profiles.total | int | Total business profile yang terdaftar |
| products.total | int | Total semua produk di sistem |
| products.with_enrichment | int | Produk yang sudah di-enrich AI |
| products.with_market_intelligence | int | Produk dengan market intelligence |
| products.with_pricing | int | Produk dengan pricing analysis |
| catalogs.total | int | Total semua catalog |
| catalogs.published | int | Catalog yang published |
| catalogs.draft | int | Catalog yang masih draft |
| buyer_requests.total | int | Total buyer requests di sistem |
| educational_materials.total_modules | int | Total modul edukasi |
| educational_materials.total_articles | int | Total artikel edukasi |

---

## Frontend Implementation Guide

### 1. Check Business Profile Status (UMKM)

```javascript
// Fetch dashboard data
const response = await fetch('/api/v1/business-profile/dashboard/summary/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Check if user has business profile
if (!data.data.has_business_profile) {
  // Show "Create Business Profile" prompt
  showCreateProfilePrompt();
} else {
  // Show dashboard with stats
  renderDashboard(data.data);
}
```

### 2. Display Dashboard Cards (UMKM) - 4 Cards

```jsx
// React example
function UMKMDashboard({ data }) {
  return (
    <div className="dashboard-grid">
      {/* Card 1: Products */}
      <Card>
        <h3>Produk</h3>
        <Stat label="Total" value={data.products.total} />
        {data.products.without_catalog > 0 && (
          <Alert type="warning">
            {data.products.without_catalog} produk belum punya catalog
          </Alert>
        )}
      </Card>

      {/* Card 2: Catalogs */}
      <Card>
        <h3>Katalog</h3>
        <Stat label="Total" value={data.catalogs.total} />
        <Stat label="Published" value={data.catalogs.published} />
        <Stat label="Draft" value={data.catalogs.draft} />
      </Card>

      {/* Card 3: Buyer Requests */}
      <Card>
        <h3>Buyer Requests</h3>
        <Stat label="Open" value={data.buyer_requests.pending} />
      </Card>

      {/* Card 4: Educational Materials */}
      <Card>
        <h3>Materi Edukasi</h3>
        <Stat label="Modules" value={data.educational_materials.total_modules} />
        <Stat label="Articles" value={data.educational_materials.total_articles} />
        <Button onClick={() => navigate('/educational')}>
          Pelajari Sekarang
        </Button>
      </Card>
    </div>
  );
}
```

### 3. Display Admin Dashboard

```jsx
// React example
function AdminDashboard({ data }) {
  return (
    <div className="dashboard-grid">
      {/* Users Card */}
      <Card>
        <h3>Users</h3>
        <Stat label="Total" value={data.users.total} />
        <Stat label="UMKM" value={data.users.umkm} />
        <Stat label="Buyers" value={data.users.buyers} />
        <Stat label="Forwarders" value={data.users.forwarders} />
      </Card>

      {/* Business Profiles Card */}
      <Card>
        <h3>Business Profiles</h3>
        <Stat label="Total" value={data.business_profiles.total} />
      </Card>

      {/* Products Card */}
      <Card>
        <h3>Products</h3>
        <Stat label="Total" value={data.products.total} />
        <Stat label="AI Enriched" value={data.products.with_enrichment} />
      </Card>

      {/* Catalogs Card */}
      <Card>
        <h3>Catalogs</h3>
        <Stat label="Total" value={data.catalogs.total} />
        <Stat label="Published" value={data.catalogs.published} />
      </Card>

      {/* Educational Materials Card */}
      <Card>
        <h3>Materi Edukasi</h3>
        <Stat label="Modules" value={data.educational_materials.total_modules} />
        <Stat label="Articles" value={data.educational_materials.total_articles} />
        <Button onClick={() => navigate('/admin/educational')}>
          Manage Materi
        </Button>
      </Card>
    </div>
  );
}
```

### 4. Role-Based Rendering

```javascript
// Determine which dashboard to show based on user role
function Dashboard({ user, dashboardData }) {
  if (user.role === 'UMKM') {
    return <UMKMDashboard data={dashboardData} />;
  } else if (user.role === 'ADMIN') {
    return <AdminDashboard data={dashboardData} />;
  }
  return <p>Dashboard tidak tersedia untuk role ini</p>;
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "detail": "Given token not valid for any token type"
  }
}
```

### 403 Forbidden
Jika user bukan UMKM atau Admin:
```json
{
  "success": false,
  "message": "Forbidden",
  "errors": {
    "detail": "You do not have permission to perform this action."
  }
}
```

---

## Notes

1. **UMKM `products.without_catalog`**: Ini adalah actionable metric - menunjukkan produk yang belum dijadikan catalog. Frontend bisa highlight ini dan arahkan user untuk membuat catalog.

2. **UMKM `buyer_requests`**: Menampilkan semua buyer requests yang masih Open (status="Open"), karena UMKM bisa melihat dan memilih request mana yang ingin mereka respons.

3. **Admin `educational_materials`**: Admin dapat melihat jumlah modul dan artikel yang ada, dan bisa langsung navigate ke halaman manage materi edukasi.

4. **Caching**: Frontend disarankan untuk cache response ini selama 1-5 menit untuk mengurangi load.

5. **Refresh**: Panggil endpoint ini setiap kali user masuk ke dashboard atau setelah melakukan aksi yang mengubah data (create product, publish catalog, dll).
