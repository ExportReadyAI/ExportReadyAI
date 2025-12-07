
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
| Field | Type | Required |
|-------|------|----------|
| product_id | int | Yes |
| display_name | string | Yes |
| base_price_exw | decimal | Yes |
| marketing_description | string | No |
| min_order_quantity | decimal | No (default: 1) |
| unit_type | string | No (default: "pcs") |
| lead_time_days | int | No (default: 14) |
| tags | array | No |

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

### Delete Catalog
```
DELETE /api/v1/catalogs/{catalog_id}/
```

---

## 2. Catalog Images

### List/Add Images
```
GET/POST /api/v1/catalogs/{catalog_id}/images/
```
**Input (POST):**
| Field | Type | Required |
|-------|------|----------|
| image_url | string | Yes |
| alt_text | string | No |
| sort_order | int | No (default: 0) |
| is_primary | boolean | No (default: false) |

### Update/Delete Image
```
PUT/DELETE /api/v1/catalogs/{catalog_id}/images/{image_id}/
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

| AI | Fungsi | Endpoint | Syarat |
|----|--------|----------|--------|
| AI 1 | Description Generator | `/catalogs/{id}/ai/description/` | Perlu Catalog |

> **Penting:** AI 2 & AI 3 diakses via **Product**, tidak perlu buat Catalog dulu.

---

### AI 1: Description Generator (via Catalog)
Membantu mengisi field catalog (`export_description`, `technical_specs`, `safety_info`)

```
POST /api/v1/catalogs/{catalog_id}/ai/description/
```
**Input:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| save_to_catalog | boolean | No | `true` = simpan ke catalog, `false` = preview saja |

**Output:**
```json
{
  "export_description": "English B2B marketing description...",
  "technical_specs": {
    "product_name": "...",
    "material": "...",
    "dimensions": "...",
    "weight_net": "...",
    "finishing": "...",
    "packaging": "...",
    "certifications": [...],
    "care_instructions": "..."
  },
  "safety_info": {
    "material_safety": "...",
    "warnings": [...],
    "storage": "...",
    "handling": "..."
  },
  "saved_to_catalog": true/false
}
```

**Flow FE:**
1. User klik "Get Recommendation" → `POST { }` → Tampilkan preview
2. User review → klik "Accept" → `POST { "save_to_catalog": true }` → Simpan ke catalog

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


error :

### AI 2: Market Intelligence (via Product)
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
  "countries_to_avoid": [
    { "country": "...", "country_code": "...", "reason": "..." }
  ],
  "market_trends": ["..."],
  "competitive_landscape": "...",
  "growth_opportunities": ["..."],
  "risks_and_challenges": ["..."],
  "overall_recommendation": "..."
}
```

**Constraint:** 1 product = 1 market intelligence. POST kedua akan ditolak (400).

---