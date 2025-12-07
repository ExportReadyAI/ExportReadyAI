
---

# API Documentation - Catalog Module

Base URL: `/api/v1/catalogs/`

## Authentication
Semua endpoint (kecuali public) memerlukan JWT token:
```
Authorization: Bearer <access_token>
```

---

## 1. Catalog CRUD

### List Catalogs
```
GET /api/v1/catalogs/
```
**Output:** Array of catalogs dengan `id`, `product_name`, `display_name`, `is_published`, `base_price_exw`, `primary_image`, `variant_count`

### Create Catalog
```
POST /api/v1/catalogs/
```
**Input:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| product_id | int | Yes | ID product yang akan dijadikan catalog |
| display_name | string | Yes | Nama tampilan untuk buyer |
| base_price_exw | decimal | Yes | Harga EXW dalam USD |
| marketing_description | string | No | Deskripsi marketing (bahasa bebas) |
| **export_description** | string | No | Deskripsi B2B internasional (isi manual ATAU dari AI) |
| **technical_specs** | json | No | Spesifikasi teknis (isi manual ATAU dari AI) |
| **safety_info** | json | No | Info keamanan/safety (isi manual ATAU dari AI) |
| min_order_quantity | decimal | No | Default: 1 |
| unit_type | string | No | Default: "pcs" |
| lead_time_days | int | No | Default: 14 |
| tags | array | No | Tags untuk filter |

> **Penting:** Field `export_description`, `technical_specs`, `safety_info` bisa diisi manual oleh user. AI hanya memberikan **rekomendasi** yang bisa di-accept atau di-reject.

**Output:** Full catalog object dengan `id`, semua fields, `images: []`, `variants: []`

### Get Catalog Detail
```
GET /api/v1/catalogs/{catalog_id}/
```
**Output:** Full catalog object termasuk `images`, `variants`, `export_description`, `technical_specs`, `safety_info`

### Update Catalog
```
PUT /api/v1/catalogs/{catalog_id}/
```
**Input:** Same as create (semua optional untuk partial update)

> User bisa edit `export_description`, `technical_specs`, `safety_info` kapan saja - baik sebelum maupun sesudah menggunakan AI.

### Delete Catalog
```
DELETE /api/v1/catalogs/{catalog_id}/
```

---

## 2. Catalog Images

> **Update:** Backend sekarang support **file upload langsung** dan juga **URL eksternal**.

### List/Add Images
```
GET/POST /api/v1/catalogs/{catalog_id}/images/
```

**Input (POST) - 2 opsi:**

#### Opsi 1: File Upload (multipart/form-data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | file | Yes* | File gambar (JPG, PNG, etc.) |
| alt_text | string | No | Alt text untuk accessibility |
| sort_order | int | No | Urutan tampilan (default: 0) |
| is_primary | boolean | No | Gambar utama (default: false) |

#### Opsi 2: URL Eksternal (application/json)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image_url | string (URL) | Yes* | URL gambar eksternal |
| alt_text | string | No | Alt text untuk accessibility |
| sort_order | int | No | Urutan tampilan (default: 0) |
| is_primary | boolean | No | Gambar utama (default: false) |

> *Minimal salah satu dari `image` atau `image_url` harus diisi.

**Output:**
```json
{
  "success": true,
  "message": "Image added successfully",
  "data": {
    "id": 1,
    "image": "/media/catalog_images/5/photo.jpg",
    "image_url": "",
    "url": "http://localhost:8000/media/catalog_images/5/photo.jpg",
    "alt_text": "Product photo",
    "sort_order": 0,
    "is_primary": true,
    "created_at": "2025-12-07T12:00:00Z"
  }
}
```

> **Note:** Field `url` adalah URL final yang bisa langsung dipakai untuk menampilkan gambar (otomatis mengambil dari file upload atau URL eksternal).

### Update/Delete Image
```
PUT/DELETE /api/v1/catalogs/{catalog_id}/images/{image_id}/
```

### Contoh Upload dengan JavaScript (Frontend)

```javascript
// Opsi 1: File Upload
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('is_primary', 'true');

await fetch(`/api/v1/catalogs/${catalogId}/images/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // Jangan set Content-Type untuk FormData - browser akan set otomatis
  },
  body: formData
});

// Opsi 2: URL Eksternal
await fetch(`/api/v1/catalogs/${catalogId}/images/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    image_url: 'https://example.com/image.jpg',
    is_primary: true
  })
});
```

---

## 3. Catalog Variants

### List/Add Variants
```
GET/POST /api/v1/catalogs/{catalog_id}/variants/
```
**Input (POST):**
| Field | Type | Required |
|-------|------|----------|
| variant_name | string | Yes |
| variant_price | decimal | Yes |
| attributes | json | No |
| moq_variant | decimal | No (default: 1) |
| sku | string | No |

### Update/Delete Variant
```
PUT/DELETE /api/v1/catalogs/{catalog_id}/variants/{variant_id}/
```

---

## 4. AI Features

### Ringkasan AI Features

| AI | Fungsi | Endpoint | Catatan |
|----|--------|----------|---------|
| AI 1 | Description Generator | `/catalogs/{id}/ai/description/` | Rekomendasi saja, user bisa accept/reject |
| AI 2 | Market Intelligence | `/products/{id}/ai/market-intelligence/` | Via Product |
| AI 3 | Pricing Calculator | `/products/{id}/ai/pricing/` | Via Product |

---

### AI 1: Description Generator (via Catalog)

Memberikan **rekomendasi** untuk field `export_description`, `technical_specs`, `safety_info`.

**Penting - Flow yang Benar:**
- User **BISA** isi field secara manual saat create/update catalog
- AI hanya **rekomendasi** - user pilih mau accept atau tidak
- Field tetap bisa diedit kapan saja oleh user

```
POST /api/v1/catalogs/{catalog_id}/ai/description/
```
**Input:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| save_to_catalog | boolean | No | `false` = preview saja (default), `true` = simpan ke catalog |

**Output:**
```json
{
  "success": true,
  "data": {
    "export_description": "English B2B marketing description...",
    "technical_specs": {
      "product_name": "...",
      "material": "...",
      "dimensions": "...",
      "certifications": [...]
    },
    "safety_info": {
      "material_safety": "...",
      "warnings": [...],
      "storage": "..."
    }
  },
  "saved_to_catalog": false
}
```

**Flow Frontend yang Direkomendasikan:**
```
┌─────────────────────────────────────────────────────────────┐
│  FORM CREATE/EDIT CATALOG                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Export Description:  [__________]  [💡 Get AI Rec]        │
│  Technical Specs:     [__________]  [💡 Get AI Rec]        │
│  Safety Info:         [__________]  [💡 Get AI Rec]        │
│                                                             │
│  → User bisa ketik manual langsung, ATAU                   │
│  → Klik "Get AI Rec" untuk dapat rekomendasi               │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Jika klik "Get AI Rec":
1. POST { "save_to_catalog": false } → dapat preview
2. Tampilkan modal dengan hasil AI
3. User pilih:
   - [Accept] → isi field dengan hasil AI
   - [Edit]   → user modifikasi dulu
   - [Cancel] → tutup, isi manual
4. Save catalog seperti biasa
```

---

## 5. Public Endpoints (No Auth)

### List Published Catalogs
```
GET /api/v1/catalogs/public/
```

### Get Published Catalog Detail
```
GET /api/v1/catalogs/public/{catalog_id}/
```
**Note:** Hanya menampilkan catalog dengan `is_published = true`

---

## 6. AI 2: Market Intelligence (via Product)

Rekomendasi negara tujuan ekspor berdasarkan analisis produk.

```
GET /api/v1/products/{product_id}/ai/market-intelligence/
```
**Output:** Data market intelligence yang sudah ada (404 jika belum ada)

```
POST /api/v1/products/{product_id}/ai/market-intelligence/
```
**Input:**
| Field | Type | Required |
|-------|------|----------|
| current_price_usd | decimal | No |
| production_capacity | int | No |

**Output:**
```json
{
  "success": true,
  "data": {
    "product_id": 35,
    "recommended_countries": [
      {
        "country": "United States",
        "country_code": "US",
        "score": 92,
        "reason": "...",
        "market_size": "Large",
        "competition_level": "Medium",
        "suggested_price_range": "$25 - $45",
        "entry_strategy": "..."
      }
    ],
    "countries_to_avoid": [...],
    "market_trends": [...],
    "competitive_landscape": "...",
    "growth_opportunities": [...],
    "risks_and_challenges": [...],
    "overall_recommendation": "..."
  }
}
```

**Constraint:** 1 product = 1 market intelligence. POST kedua akan ditolak (400).

---

## 7. AI 3: Pricing Calculator (via Product)

```
GET /api/v1/products/{product_id}/ai/pricing/
```

```
POST /api/v1/products/{product_id}/ai/pricing/
```
**Input:**
| Field | Type | Required |
|-------|------|----------|
| cogs_per_unit_idr | decimal | Yes |
| target_margin_percent | decimal | Yes |
| target_country_code | string | No |

**Constraint:** 1 product = 1 pricing result.

---