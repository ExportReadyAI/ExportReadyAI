# Export Analysis System Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Features](#core-features)
4. [API Endpoints](#api-endpoints)
5. [Data Models](#data-models)
6. [AI Compliance Service](#ai-compliance-service)
7. [Product Snapshot System](#product-snapshot-system)
8. [Regulation Recommendations](#regulation-recommendations)
9. [Use Cases & Workflows](#use-cases--workflows)
10. [Error Handling](#error-handling)
11. [Performance & Optimization](#performance--optimization)
12. [Security & Permissions](#security--permissions)

---

## Overview

### Purpose
Export Analysis System adalah fitur inti dari ExportReady.AI yang memungkinkan UMKM Indonesia untuk:
- Menganalisis kesiapan produk untuk ekspor ke negara tujuan
- Mendapatkan compliance score dan status grade
- Menerima rekomendasi perbaikan yang actionable
- Membandingkan persyaratan regulasi antar negara
- Melacak perubahan produk dengan audit trail

### Key Benefits
- ✅ **AI-Powered Analysis**: Menggunakan Kolosal AI untuk analisis compliance otomatis
- ✅ **Comprehensive Checks**: Ingredient, specification, packaging compliance
- ✅ **Product Snapshot**: Audit trail untuk setiap analisis
- ✅ **Change Detection**: Deteksi otomatis jika produk berubah setelah analisis
- ✅ **Multi-Country Comparison**: Bandingkan persyaratan hingga 5 negara sekaligus
- ✅ **Actionable Recommendations**: Panduan 10 section untuk setiap negara

### Technology Stack
- **Backend**: Django 5.0 + Django REST Framework
- **AI Service**: Kolosal AI (OpenAI-compatible API)
- **Database**: PostgreSQL with JSONField
- **Authentication**: JWT with role-based access control

---

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend UI   │
│  (React/Vue)    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────────┐
│         Django REST API                 │
│  ┌─────────────────────────────────┐   │
│  │  Export Analysis Views          │   │
│  │  - List/Create/Detail           │   │
│  │  - Reanalyze/Delete/Compare     │   │
│  │  - Regulation Recommendations   │   │
│  └──────────┬──────────────────────┘   │
│             │                           │
│  ┌──────────▼──────────────────────┐   │
│  │  Compliance AI Service          │   │
│  │  - analyze_product_compliance() │   │
│  │  - check_ingredient_compliance()│   │
│  │  - check_specification_...()    │   │
│  │  - check_packaging_compliance() │   │
│  │  - generate_recommendations()   │   │
│  │  - calculate_readiness_score()  │   │
│  └──────────┬──────────────────────┘   │
│             │                           │
└─────────────┼───────────────────────────┘
              │
              ▼
    ┌─────────────────┐
    │   Kolosal AI    │
    │  (GPT-4-like)   │
    └─────────────────┘
              │
              ▼
    ┌─────────────────┐
    │  PostgreSQL DB  │
    │  - ExportAnalysis
    │  - Product      │
    │  - Country      │
    │  - Enrichment   │
    └─────────────────┘
```

### Component Responsibilities

#### 1. Views Layer (`apps/export_analysis/views.py`)
- Handle HTTP requests/responses
- Permission & ownership validation
- Query parameter parsing
- Pagination logic
- Serialization coordination

#### 2. Service Layer (`apps/export_analysis/services.py`)
- AI integration and prompt engineering
- Business logic for compliance checking
- Score calculation algorithms
- Recommendation generation
- Fallback handling when AI unavailable

#### 3. Model Layer (`apps/export_analysis/models.py`)
- Database schema definition
- Data validation
- Snapshot creation and comparison
- Cache management
- Auto-timestamp handling

#### 4. Serializer Layer (`apps/export_analysis/serializers.py`)
- Request validation
- Response formatting
- Nested data handling
- Ownership validation

---

## Core Features

### Feature 1: Export Analysis Creation (PBI-BE-M3-03)

**Purpose**: Create new export analysis for product-country combination

**Process Flow**:
```
1. User submits: product_id, target_country_code
2. Validate: product ownership, enrichment exists, unique combination
3. Fetch: Product + ProductEnrichment data
4. AI Analysis: 4 API calls to Kolosal AI
   - Ingredient compliance check
   - Specification compliance check
   - Packaging compliance check
   - Generate recommendations
5. Calculate: Readiness score (0-100)
6. Create: Product snapshot for audit trail
7. Save: ExportAnalysis record
8. Return: Complete analysis result
```

**Endpoint**: `POST /api/v1/export-analysis/`

**Request Body**:
```json
{
  "product_id": 123,
  "target_country_code": "US"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Export analysis created successfully",
  "data": {
    "id": 44,
    "product": 123,
    "product_name": "Keripik Singkong Pedas",
    "target_country": "US",
    "country_name": "United States",
    "readiness_score": 75,
    "status_grade": "MEDIUM",
    "compliance_issues": {
      "ingredient_compliance": {
        "status": "FAIL",
        "score": 60,
        "violations": [
          {
            "ingredient": "Palm Oil",
            "reason": "Requires RSPO certification for US export"
          }
        ]
      },
      "specification_compliance": {
        "status": "PASS",
        "score": 85,
        "violations": []
      },
      "packaging_compliance": {
        "status": "FAIL",
        "score": 70,
        "violations": [
          {
            "issue": "Missing FDA nutritional facts label",
            "requirement": "21 CFR 101.9"
          }
        ]
      }
    },
    "recommendations": "1. Obtain RSPO certification...\n2. Add FDA-compliant nutrition label...",
    "product_snapshot": {
      "name_local": "Keripik Singkong Pedas",
      "name_english": "Spicy Cassava Chips",
      "ingredients": [...],
      "packaging_type": "Multi-layer plastic pouch",
      "snapshot_created_at": "2025-12-07T10:30:00Z"
    },
    "snapshot_product_name": "Keripik Singkong Pedas",
    "product_changed": false,
    "analyzed_at": "2025-12-07T10:30:00Z"
  }
}
```

**Validation Rules**:
- ✅ Product must exist and belong to authenticated user
- ✅ Product must have ProductEnrichment
- ✅ Product-country combination must be unique (no duplicates)
- ✅ Country code must exist in database

---

### Feature 2: Export Analysis List (PBI-BE-M3-01)

**Purpose**: List all export analyses with filtering and pagination

**Endpoint**: `GET /api/v1/export-analysis/`

**Query Parameters**:
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | Page number (default: 1) | `?page=2` |
| `limit` | integer | Items per page (default: 10) | `?limit=20` |
| `country_code` | string | Filter by country | `?country_code=US` |
| `score_min` | integer | Minimum readiness score | `?score_min=70` |
| `score_max` | integer | Maximum readiness score | `?score_max=90` |
| `search` | string | Search product/country name | `?search=keripik` |

**Access Control**:
- **UMKM**: Only see analyses for their own products
- **Admin**: See all analyses

**Response Example**:
```json
{
  "success": true,
  "message": "Export analyses retrieved successfully",
  "data": [
    {
      "id": 44,
      "product": 123,
      "product_name": "Keripik Singkong Pedas",
      "target_country": "US",
      "country_code": "US",
      "country_name": "United States",
      "readiness_score": 75,
      "status_grade": "MEDIUM",
      "analyzed_at": "2025-12-07T10:30:00Z",
      "created_at": "2025-12-07T10:25:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 45,
    "pages": 5
  }
}
```

---

### Feature 3: Export Analysis Detail (PBI-BE-M3-02)

**Purpose**: Get complete analysis details including snapshot and change detection

**Endpoint**: `GET /api/v1/export-analysis/{id}/`

**Key Features**:
- ✅ Full compliance issues breakdown
- ✅ Product snapshot for audit trail
- ✅ Change detection (`product_changed` flag)
- ✅ Actionable recommendations

**Response Example**:
```json
{
  "success": true,
  "message": "Export analysis retrieved successfully",
  "data": {
    "id": 44,
    "product": 123,
    "product_name": "Keripik Singkong Pedas (Updated)",
    "product_category": "SNACK_001",
    "product_material": "Cassava 70%, Palm Oil 20%, Spices 10%",
    "product_packaging": "Multi-layer plastic pouch",
    "target_country": "US",
    "country_code": "US",
    "country_name": "United States",
    "country_region": "North America",
    "readiness_score": 75,
    "status_grade": "MEDIUM",
    "compliance_issues": { ... },
    "recommendations": "...",
    "product_snapshot": {
      "name_local": "Keripik Singkong Original",
      "ingredients": [ ... ],
      "snapshot_created_at": "2025-12-07T10:30:00Z"
    },
    "snapshot_product_name": "Keripik Singkong Original",
    "product_changed": true,  // ← Product updated after analysis!
    "analyzed_at": "2025-12-07T10:30:00Z",
    "created_at": "2025-12-07T10:25:00Z"
  }
}
```

---

### Feature 4: Re-analyze Product (PBI-BE-M3-09)

**Purpose**: Re-run analysis with updated product data

**When to Use**:
- Product information has been updated
- `product_changed` flag is `true`
- User fixed compliance issues
- Need fresh analysis with current data

**Endpoint**: `POST /api/v1/export-analysis/{id}/reanalyze/`

**Process**:
```
1. Fetch latest product data from database
2. Re-run all AI compliance checks (4 API calls)
3. Recalculate readiness score
4. Create NEW product snapshot
5. Clear regulation recommendations cache
6. Update analyzed_at timestamp
7. Return updated analysis
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Export analysis re-analyzed successfully",
  "data": {
    "id": 44,
    "readiness_score": 85,  // ← Improved!
    "status_grade": "HIGH",
    "compliance_issues": {
      "ingredient_compliance": {
        "status": "PASS"  // ← Fixed!
      },
      "packaging_compliance": {
        "status": "PASS"  // ← Fixed!
      }
    },
    "product_snapshot": {
      // NEW snapshot with updated data
      "name_local": "Keripik Singkong Pedas (RSPO Certified)",
      "snapshot_created_at": "2025-12-07T11:00:00Z"
    },
    "product_changed": false,  // ← Reset to false
    "analyzed_at": "2025-12-07T11:00:00Z"  // ← New timestamp
  }
}
```

**Important Notes**:
- ⏱️ **Long-running operation**: May take 30-60 seconds (4 AI API calls)
- 🔄 **Always uses latest data**: Fetches from database, not cache
- 📸 **Creates new snapshot**: Old snapshot preserved for history
- 🗑️ **Clears cache**: Regulation recommendations regenerated on next request

**Handling "Broken Pipe" Errors**:
```javascript
// Frontend: Increase timeout for re-analysis
const reanalyze = async (analysisId) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000); // 2 minutes
  
  try {
    const response = await fetch(
      `/api/v1/export-analysis/${analysisId}/reanalyze/`,
      {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    clearTimeout(timeout);
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      // Timeout - poll for results
      return pollForResults(analysisId);
    }
    throw error;
  }
};
```

---

### Feature 5: Multi-Country Comparison (PBI-BE-M3-13)

**Purpose**: Compare export requirements for up to 5 countries simultaneously

**Endpoint**: `POST /api/v1/export-analysis/compare/`

**Request Body**:
```json
{
  "product_id": 123,
  "country_codes": ["US", "JP", "AU", "SG", "UK"]
}
```

**Process**:
1. Validate all country codes exist
2. Create **single product snapshot** (fair comparison)
3. For each country:
   - Check if analysis exists → use existing
   - If not exists → run new analysis
4. All new analyses use **same snapshot** (consistency)
5. Return array of results

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Comparison completed for 5 countries",
  "data": [
    {
      "id": 44,
      "country_code": "US",
      "country_name": "United States",
      "readiness_score": 75,
      "status_grade": "MEDIUM",
      "compliance_issues": { ... }
    },
    {
      "id": 45,
      "country_code": "JP",
      "country_name": "Japan",
      "readiness_score": 90,
      "status_grade": "HIGH",
      "compliance_issues": { ... }
    },
    // ... 3 more countries
  ]
}
```

**Use Cases**:
- 🌏 **Market Selection**: Find easiest market to enter
- 📊 **Requirements Comparison**: Compare regulatory complexity
- 🎯 **Priority Planning**: Focus on high-scoring countries first
- 💰 **Cost Analysis**: Estimate compliance costs per market

---

### Feature 6: Regulation Recommendations (NEW)

**Purpose**: Get detailed, actionable 10-section guide for export compliance

**Endpoint**: `GET /api/v1/export-analysis/{id}/regulation-recommendations/`

**Headers**:
```
Accept-Language: id   // Indonesian (default)
Accept-Language: en   // English
```

**10 Section Structure**:
1. **Overview** - High-level summary and key points
2. **Prohibited Items** - Banned/restricted ingredients
3. **Import Restrictions** - Quotas, licenses, special conditions
4. **Certifications** - Required certificates and registrations
5. **Labeling Requirements** - Label format, language, mandatory info
6. **Customs Procedures** - Import procedures and documentation
7. **Testing & Inspection** - Required tests and quality standards
8. **Intellectual Property** - Trademark and brand protection
9. **Shipping & Logistics** - Packaging, shipping, cold chain
10. **Timeline & Costs** - Estimated time and expenses

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Regulation recommendations retrieved successfully",
  "data": {
    "analysis_id": 44,
    "country_code": "US",
    "product_name": "Keripik Singkong Pedas",
    "recommendations": {
      "overview": {
        "summary": "Panduan komprehensif ekspor makanan ringan ke Amerika Serikat...",
        "key_points": [
          "FDA mengatur semua produk makanan impor",
          "Sertifikasi HACCP diperlukan untuk produsen",
          "Label nutrisi wajib mengikuti format FDA"
        ]
      },
      "prohibited_items": {
        "summary": "Daftar bahan yang dilarang atau dibatasi oleh FDA...",
        "key_points": [
          "Pewarna sintetis tertentu dilarang (Red 2, Yellow 5)",
          "MSG dibatasi maksimal 0.5%",
          "Pengawet sodium benzoate maksimal 0.1%"
        ]
      },
      "certifications": {
        "summary": "Sertifikasi yang diperlukan untuk ekspor ke US...",
        "action_items": [
          "Dapatkan sertifikasi HACCP dari badan terakreditasi",
          "Registrasi FDA Food Facility (form 2541)",
          "Prior Notice untuk setiap shipment (form 2541a)",
          "Sertifikasi halal (opsional, meningkatkan daya saing)"
        ]
      },
      "labeling_requirements": {
        "summary": "Persyaratan label makanan sesuai FDA 21 CFR 101...",
        "action_items": [
          "Tambahkan Nutrition Facts panel (format FDA)",
          "Cantumkan ingredients dalam bahasa Inggris, urut descending",
          "Sertakan allergen warnings untuk 8 allergen utama",
          "Net weight dalam oz dan gram",
          "Nama dan alamat distributor US"
        ]
      },
      "customs_procedures": {
        "summary": "Prosedur bea cukai US untuk produk makanan...",
        "action_items": [
          "Gunakan HS Code yang tepat (2008.19.00 untuk cassava chips)",
          "Siapkan dokumen: Commercial Invoice, Packing List, Bill of Lading",
          "FDA Prior Notice minimal 2 jam sebelum arrival",
          "Bea masuk: 6.4% untuk snack foods"
        ]
      },
      "testing_inspection": {
        "summary": "Pengujian laboratorium yang diperlukan...",
        "action_items": [
          "Uji mikrobiologi: Total plate count, E.coli, Salmonella",
          "Uji kimia: Heavy metals (Pb, Cd, Hg), pesticide residue",
          "Uji nutrisi: Untuk verifikasi label nutrisi",
          "Inspeksi visual FDA di port of entry (random)"
        ]
      },
      "intellectual_property": {
        "summary": "Perlindungan merek dan desain di pasar US...",
        "key_points": [
          "Daftarkan trademark di USPTO sebelum ekspor",
          "Lindungi desain kemasan dengan design patent",
          "Monitor counterfeit products di e-commerce",
          "Registrasi copyright untuk branding materials"
        ]
      },
      "shipping_logistics": {
        "summary": "Persyaratan pengiriman dan logistik...",
        "key_points": [
          "Gunakan cold chain jika produk sensitif suhu",
          "Kemasan tahan lama minimal 30 hari transit",
          "Label shipping: 'FOOD PRODUCT', 'KEEP DRY'",
          "Asuransi cargo minimal 110% nilai FOB",
          "Gunakan freight forwarder berpengalaman dengan FDA clearance"
        ]
      },
      "timeline_costs": {
        "summary": "Estimasi waktu dan biaya ekspor ke US...",
        "key_points": [
          "Persiapan dokumen: 2-4 minggu",
          "Sertifikasi HACCP: 4-8 minggu",
          "FDA facility registration: 1 hari",
          "Pengiriman Jakarta-LA: 14-21 hari (sea freight)",
          "Total biaya compliance: $5,000-$15,000 (one-time)",
          "Biaya per shipment: $2,000-$5,000 (recurring)"
        ]
      }
    },
    "from_cache": false
  }
}
```

**Caching Mechanism**:
- ✅ First request: Generate recommendations → save to `regulation_recommendations_cache`
- ✅ Subsequent requests: Return cached version (instant response)
- ✅ Cache cleared on: Product re-analysis, manual cache clear
- ✅ Language-agnostic: Same cache for all languages (AI generates on-demand)

---

### Feature 7: Delete Analysis (PBI-BE-M3-10)

**Purpose**: Delete export analysis record

**Endpoint**: `DELETE /api/v1/export-analysis/{id}/`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Export analysis deleted successfully"
}
```

---

### Feature 8: Country Management

#### List Countries (PBI-BE-M3-11)

**Endpoint**: `GET /api/v1/countries/`

**Query Parameters**:
- `region` - Filter by region (e.g., "Asia", "Europe")
- `search` - Search by country name or code

**Response**:
```json
{
  "success": true,
  "message": "Countries retrieved successfully",
  "data": [
    {
      "country_code": "US",
      "country_name": "United States",
      "region": "North America",
      "regulations_count": 45
    }
  ]
}
```

#### Country Detail (PBI-BE-M3-12)

**Endpoint**: `GET /api/v1/countries/{country_code}/`

**Response**:
```json
{
  "success": true,
  "message": "Country retrieved successfully",
  "data": {
    "country_code": "US",
    "country_name": "United States",
    "region": "North America",
    "regulations": [
      {
        "id": 1,
        "rule_category": "INGREDIENT",
        "forbidden_keywords": ["red 2", "yellow 5"],
        "required_specs": null,
        "description_rule": "FDA banned food colors"
      }
    ],
    "regulations_by_category": {
      "INGREDIENT": [ ... ],
      "PACKAGING": [ ... ],
      "SPECIFICATION": [ ... ]
    }
  }
}
```

---

## Data Models

### ExportAnalysis Model

**Location**: `apps/export_analysis/models.py`

**Schema**:
```python
class ExportAnalysis(models.Model):
    # Relations
    product = ForeignKey(Product)
    target_country = ForeignKey(Country)
    
    # Analysis Results
    readiness_score = IntegerField()  # 0-100
    status_grade = CharField(choices=StatusGrade)  # LOW/MEDIUM/HIGH
    compliance_issues = JSONField()
    recommendations = TextField()
    
    # Product Snapshot (Audit Trail)
    product_snapshot = JSONField(default=dict)
    
    # Regulation Recommendations Cache
    regulation_recommendations_cache = JSONField(default=dict)
    
    # Timestamps
    analyzed_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)
```

**Status Grade Logic**:
```python
class StatusGrade(models.TextChoices):
    LOW = "LOW"       # score < 60
    MEDIUM = "MEDIUM" # 60 <= score < 80
    HIGH = "HIGH"     # score >= 80
```

**Key Methods**:

#### 1. `create_product_snapshot(product)`
```python
def create_product_snapshot(self, product):
    """
    Create immutable snapshot of product data at analysis time.
    Used for audit trail and change detection.
    """
    snapshot = {
        "product_id": product.id,
        "name_local": product.name_local,
        "name_english": product.name_english,
        "description_local": product.description_local,
        "description_english": product.description_english,
        "category_id": product.category_id,
        "hs_code": product.hs_code,
        "snapshot_created_at": timezone.now().isoformat()
    }
    
    if hasattr(product, 'enrichment'):
        snapshot["enrichment"] = {
            "ingredients": product.enrichment.ingredients,
            "material_composition": product.enrichment.material_composition,
            "packaging_type": product.enrichment.packaging_type,
            "packaging_specifications": product.enrichment.packaging_specifications,
            "technical_specifications": product.enrichment.technical_specifications
        }
    
    return snapshot
```

#### 2. `is_product_changed()`
```python
def is_product_changed(self):
    """
    Compare current product data with snapshot.
    Returns True if product has been modified since analysis.
    """
    if not self.product_snapshot:
        return False
    
    product = self.product
    snapshot = self.product_snapshot
    
    # Compare basic fields
    if product.name_local != snapshot.get("name_local"):
        return True
    if product.name_english != snapshot.get("name_english"):
        return True
    
    # Compare enrichment if exists
    if hasattr(product, 'enrichment') and "enrichment" in snapshot:
        enrichment = product.enrichment
        snapshot_enrichment = snapshot["enrichment"]
        
        if enrichment.ingredients != snapshot_enrichment.get("ingredients"):
            return True
        if enrichment.packaging_type != snapshot_enrichment.get("packaging_type"):
            return True
    
    return False
```

#### 3. `get_snapshot_product_name()`
```python
def get_snapshot_product_name(self):
    """Get product name from snapshot."""
    if not self.product_snapshot:
        return self.product.name_local
    return self.product_snapshot.get("name_local", self.product.name_local)
```

**Unique Constraint**:
```python
class Meta:
    unique_together = [["product", "target_country"]]
```
Prevents duplicate analyses for same product-country combination.

---

### Country Model

**Schema**:
```python
class Country(models.Model):
    country_code = CharField(max_length=2, primary_key=True)  # ISO 3166-1 alpha-2
    country_name = CharField(max_length=100)
    region = CharField(max_length=50)  # e.g., "Asia", "Europe"
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**Related Model**: `CountryRegulation`
```python
class CountryRegulation(models.Model):
    country = ForeignKey(Country, related_name="regulations")
    rule_category = CharField(choices=RuleCategory)
    forbidden_keywords = JSONField(default=list)  # e.g., ["red 2", "msg"]
    required_specs = JSONField(default=dict)
    description_rule = TextField()
```

**Rule Categories**:
- `INGREDIENT` - Ingredient restrictions
- `PACKAGING` - Packaging requirements
- `SPECIFICATION` - Technical specifications
- `CERTIFICATION` - Required certifications
- `LABELING` - Label requirements

---

## AI Compliance Service

### ComplianceAIService Class

**Location**: `apps/export_analysis/services.py`

**Purpose**: Integrate with Kolosal AI for compliance analysis

**Configuration**:
```python
class ComplianceAIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.KOLOSAL_API_KEY,
            base_url="https://api.kolosal.ai/v1"
        )
        self.model = "gpt-4o-2024-08-06"
```

### Core Methods

#### 1. `analyze_product_compliance(product, country_code)`

**Main orchestrator method** - runs complete analysis pipeline.

```python
def analyze_product_compliance(self, product, country_code):
    """
    Complete compliance analysis pipeline.
    Returns: {
        "readiness_score": int,
        "status_grade": str,
        "compliance_issues": dict,
        "recommendations": str
    }
    """
    # 1. Ingredient compliance (API call 1)
    ingredient_result = self.check_ingredient_compliance(
        ingredients=product.enrichment.ingredients,
        country_code=country_code
    )
    
    # 2. Specification compliance (API call 2)
    spec_result = self.check_specification_compliance(
        specifications=product.enrichment.technical_specifications,
        country_code=country_code
    )
    
    # 3. Packaging compliance (API call 3)
    packaging_result = self.check_packaging_compliance(
        packaging=product.enrichment.packaging_specifications,
        country_code=country_code
    )
    
    # 4. Calculate overall score
    readiness_score = self.calculate_readiness_score(
        ingredient_result,
        spec_result,
        packaging_result
    )
    
    # 5. Generate recommendations (API call 4)
    recommendations = self.generate_recommendations(
        product=product,
        country_code=country_code,
        compliance_results={
            "ingredient": ingredient_result,
            "specification": spec_result,
            "packaging": packaging_result
        }
    )
    
    return {
        "readiness_score": readiness_score,
        "status_grade": self._get_status_grade(readiness_score),
        "compliance_issues": {
            "ingredient_compliance": ingredient_result,
            "specification_compliance": spec_result,
            "packaging_compliance": packaging_result
        },
        "recommendations": recommendations
    }
```

**Performance**: ~30-60 seconds (4 sequential API calls)

---

#### 2. `check_ingredient_compliance(ingredients, country_code)`

**Purpose**: Check if ingredients comply with country regulations

**Input**:
```python
ingredients = [
    {"name": "Singkong", "name_en": "Cassava", "percentage": 70.0},
    {"name": "Minyak Sawit", "name_en": "Palm Oil", "percentage": 20.0},
    {"name": "Bumbu Pedas", "name_en": "Spices", "percentage": 10.0}
]
```

**AI Prompt**:
```
You are a food safety compliance expert. Analyze these ingredients for export to {country_name}.

Ingredients:
- Cassava (70%)
- Palm Oil (20%)
- Spices (10%)

Check against country regulations and return JSON:
{
  "status": "PASS|FAIL",
  "score": 0-100,
  "violations": [
    {"ingredient": "Palm Oil", "reason": "Requires RSPO certification"}
  ],
  "notes": "Additional observations"
}
```

**Output**:
```python
{
    "status": "FAIL",
    "score": 65,
    "violations": [
        {
            "ingredient": "Palm Oil",
            "reason": "Requires RSPO certification for US export",
            "regulation": "USDA organic standards"
        }
    ],
    "notes": "Most ingredients are acceptable, but palm oil certification needed"
}
```

---

#### 3. `check_specification_compliance(specifications, country_code)`

**Purpose**: Validate technical specifications meet country standards

**Input**:
```python
specifications = {
    "shelf_life": "6 months",
    "storage": "Store in cool, dry place",
    "net_weight": "100g",
    "moisture_content": "< 5%",
    "oil_content": "< 30%"
}
```

**Output**:
```python
{
    "status": "PASS",
    "score": 90,
    "violations": [],
    "notes": "All specifications meet FDA requirements"
}
```

---

#### 4. `check_packaging_compliance(packaging, country_code)`

**Purpose**: Verify packaging meets regulatory requirements

**Input**:
```python
packaging = {
    "material": "PET/PE laminated",
    "weight": "100g",
    "dimensions": "20x15x5 cm",
    "sealing": "Heat sealed",
    "has_nutrition_label": False  # ← Problem!
}
```

**Output**:
```python
{
    "status": "FAIL",
    "score": 70,
    "violations": [
        {
            "issue": "Missing FDA-required nutritional facts label",
            "requirement": "21 CFR 101.9 - Nutrition labeling",
            "severity": "critical"
        },
        {
            "issue": "Net weight not displayed in oz",
            "requirement": "Must show both metric and imperial units",
            "severity": "moderate"
        }
    ],
    "notes": "Packaging material is acceptable but labeling incomplete"
}
```

---

#### 5. `calculate_readiness_score(ingredient, spec, packaging)`

**Purpose**: Calculate weighted overall score

**Algorithm**:
```python
def calculate_readiness_score(self, ingredient_result, spec_result, packaging_result):
    """
    Weighted average of compliance scores:
    - Ingredients: 40% (most critical)
    - Specifications: 30%
    - Packaging: 30%
    """
    weights = {
        "ingredient": 0.40,
        "specification": 0.30,
        "packaging": 0.30
    }
    
    total_score = (
        ingredient_result["score"] * weights["ingredient"] +
        spec_result["score"] * weights["specification"] +
        packaging_result["score"] * weights["packaging"]
    )
    
    return round(total_score)
```

**Example**:
```python
ingredient_score = 65
spec_score = 90
packaging_score = 70

readiness_score = (65 * 0.4) + (90 * 0.3) + (70 * 0.3)
                = 26 + 27 + 21
                = 74
```

---

#### 6. `generate_recommendations(product, country_code, compliance_results)`

**Purpose**: Generate actionable fix recommendations

**AI Prompt**:
```
Based on compliance analysis for {product_name} export to {country_name}:

Issues Found:
- Ingredient: Palm Oil requires RSPO certification
- Packaging: Missing FDA nutrition label

Generate 3-5 specific, actionable recommendations to fix these issues.
Format as numbered list with clear action steps.
```

**Output**:
```
1. Obtain RSPO (Roundtable on Sustainable Palm Oil) certification from authorized body
   - Contact: RSPO Secretariat (www.rspo.org)
   - Timeline: 8-12 weeks
   - Cost: $1,500-$3,000

2. Add FDA-compliant Nutrition Facts label to packaging
   - Use FDA format (21 CFR 101.9)
   - Include: Calories, Fat, Sodium, Carbs, Protein
   - Get lab testing for accurate values
   - Timeline: 2-4 weeks

3. Update packaging to show net weight in both grams and ounces
   - Example: "NET WT 100g (3.5 oz)"
   - Consult FDA packaging guidelines

4. Consider halal certification to expand market reach
   - Optional but increases marketability
   - Recognized certifiers: IFANCA, ISNA
```

---

#### 7. `generate_regulation_recommendations(product_snapshot, country_code, language)`

**Purpose**: Generate comprehensive 10-section export guide

**Note**: Currently uses **fallback mode** (no AI calls) - returns structured template data.

**Future Enhancement**: Will use AI with this prompt structure:
```
Generate a comprehensive export regulation guide for {product_name} to {country_name}.

Product Details:
{product_snapshot}

Return JSON with 10 sections:
1. overview: {summary, key_points[]}
2. prohibited_items: {summary, key_points[]}
3. import_restrictions: {summary, key_points[]}
4. certifications: {summary, action_items[]}
5. labeling_requirements: {summary, action_items[]}
6. customs_procedures: {summary, action_items[]}
7. testing_inspection: {summary, action_items[]}
8. intellectual_property: {summary, key_points[]}
9. shipping_logistics: {summary, key_points[]}
10. timeline_costs: {summary, key_points[]}

Language: {language} (id or en)
```

**Current Implementation** (Fallback):
```python
def _generate_fallback_recommendations(self, country_code, language="id"):
    """Fallback recommendations when AI unavailable."""
    country = Country.objects.get(country_code=country_code)
    
    if language == "id":
        return {
            "overview": {
                "summary": f"Panduan ekspor ke {country.country_name}...",
                "key_points": [...]
            },
            # ... 9 more sections
        }
    else:  # English
        return {
            "overview": {
                "summary": f"Export guide to {country.country_name}...",
                "key_points": [...]
            },
            # ... 9 more sections
        }
```

---

## Product Snapshot System

### Purpose
Product snapshots provide **immutable audit trail** - preserving exact product state at analysis time.

### Why Snapshots?

**Problem Without Snapshots**:
```
1. User analyzes product on Dec 1 → Score: 65
2. User updates product on Dec 5
3. User views old analysis → Shows score 65 but product data has changed!
4. Confusion: "Why is my score low? My product looks good now!"
```

**Solution With Snapshots**:
```
1. User analyzes product on Dec 1 → Score: 65, Snapshot created
2. User updates product on Dec 5
3. User views old analysis → Shows score 65 with ORIGINAL product data
4. System detects: "product_changed: true" → Prompts re-analysis
```

### Snapshot Data Structure

```python
{
    "product_id": 123,
    "name_local": "Keripik Singkong Original",
    "name_english": "Original Cassava Chips",
    "description_local": "Keripik singkong renyah",
    "description_english": "Crispy cassava chips",
    "category_id": "SNACK_001",
    "hs_code": "2008.19.00",
    
    "enrichment": {
        "ingredients": [
            {"name": "Singkong", "name_en": "Cassava", "percentage": 70.0},
            {"name": "Minyak Sawit", "name_en": "Palm Oil", "percentage": 20.0}
        ],
        "material_composition": "Cassava 70%, Palm Oil 20%",
        "packaging_type": "Simple plastic bag",
        "packaging_specifications": {
            "material": "LDPE plastic",
            "weight": "100g",
            "has_nutrition_label": false
        },
        "technical_specifications": {
            "shelf_life": "3 months",
            "moisture_content": "< 5%"
        }
    },
    
    "snapshot_created_at": "2025-12-01T10:30:00Z"
}
```

### Change Detection Algorithm

```python
def is_product_changed(self):
    """
    Compare current vs snapshot data to detect changes.
    Checks: name, description, ingredients, packaging, specifications.
    """
    if not self.product_snapshot:
        return False
    
    product = self.product
    snapshot = self.product_snapshot
    
    # Check basic fields
    basic_fields = ["name_local", "name_english", "category_id", "hs_code"]
    for field in basic_fields:
        if getattr(product, field) != snapshot.get(field):
            return True
    
    # Check enrichment fields
    if hasattr(product, 'enrichment') and "enrichment" in snapshot:
        enrichment = product.enrichment
        snap_enrichment = snapshot["enrichment"]
        
        # Deep comparison of JSON fields
        if enrichment.ingredients != snap_enrichment.get("ingredients"):
            return True
        if enrichment.packaging_specifications != snap_enrichment.get("packaging_specifications"):
            return True
        if enrichment.technical_specifications != snap_enrichment.get("technical_specifications"):
            return True
    
    return False
```

### Use Cases

#### Use Case 1: View Historical Analysis
```
User views analysis from 2 weeks ago
→ Shows product data AS IT WAS 2 weeks ago
→ User understands why score was low then
→ User can see what changed since then
```

#### Use Case 2: Audit Trail
```
Admin reviews all analyses for compliance audit
→ Each analysis shows exact product state at analysis time
→ Can verify: "Was the product compliant when exported?"
→ Legal protection if issues arise later
```

#### Use Case 3: Change Prompt
```
User views analysis with product_changed: true
→ UI shows: "⚠️ Product updated since analysis"
→ Button: "Re-analyze with Current Data"
→ User updates analysis to reflect current state
```

#### Use Case 4: A/B Testing
```
User wants to compare: "How does score change if I update packaging?"
→ View old analysis (before packaging update)
→ Run re-analysis (after packaging update)
→ Compare scores side-by-side
→ Decide: "Is the packaging update worth it?"
```

---

## Use Cases & Workflows

### Workflow 1: First-Time Analysis

```mermaid
sequenceDiagram
    User->>Frontend: Select product & target country
    Frontend->>API: POST /export-analysis
    API->>Database: Validate product, country
    API->>AI Service: analyze_product_compliance()
    AI Service->>Kolosal AI: 4 API calls (ingredient, spec, packaging, recommendations)
    Kolosal AI-->>AI Service: Compliance results
    AI Service->>AI Service: Calculate readiness score
    AI Service-->>API: Analysis result
    API->>Database: Create ExportAnalysis + snapshot
    Database-->>API: Analysis saved
    API-->>Frontend: Return analysis (201 Created)
    Frontend->>User: Display score, issues, recommendations
```

**Timeline**: 30-60 seconds

---

### Workflow 2: Fix Issues & Re-analyze

```mermaid
sequenceDiagram
    User->>Frontend: View analysis (score: 65, product_changed: true)
    Frontend->>User: Show warning: "Product updated"
    User->>Frontend: Click "View Recommendations"
    Frontend->>API: GET /regulation-recommendations
    API-->>Frontend: 10-section guide
    User->>Frontend: Update product based on guide
    Frontend->>API: PATCH /products/{id}/enrichment
    API->>Database: Update product
    User->>Frontend: Click "Re-analyze"
    Frontend->>API: POST /export-analysis/{id}/reanalyze
    API->>AI Service: Re-run analysis with new data
    API->>Database: Update analysis + new snapshot
    API-->>Frontend: New analysis (score: 85)
    Frontend->>User: Show improved score!
```

**Timeline**: 1-2 minutes (user updates) + 30-60 seconds (re-analysis)

---

### Workflow 3: Multi-Country Comparison

```mermaid
sequenceDiagram
    User->>Frontend: Select product + 5 countries
    Frontend->>API: POST /export-analysis/compare
    API->>Database: Check existing analyses
    API->>AI Service: Run analysis for new countries
    AI Service->>Kolosal AI: Multiple API calls
    API->>Database: Create analyses with SAME snapshot
    API-->>Frontend: Array of 5 analysis results
    Frontend->>User: Display comparison table
    User->>Frontend: Sort by readiness_score
    User->>User: Decision: "Target Japan first (score: 90)"
```

**Timeline**: 2-5 minutes (depends on how many are new)

---

### Workflow 4: Regulation Deep-Dive

```mermaid
sequenceDiagram
    User->>Frontend: View analysis detail
    Frontend->>User: Show compliance issues
    User->>Frontend: Click "Detailed Regulation Guide"
    Frontend->>API: GET /regulation-recommendations
    API->>Database: Check cache
    alt Cache exists
        Database-->>API: Return cached recommendations
        API-->>Frontend: Recommendations (instant)
    else No cache
        API->>AI Service: generate_regulation_recommendations()
        AI Service-->>API: 10-section guide
        API->>Database: Save to cache
        API-->>Frontend: Recommendations
    end
    Frontend->>User: Display 10 sections with action items
    User->>Frontend: Check off completed tasks
    Frontend->>LocalStorage: Save progress
```

**Timeline**: <1 second (cached) or 5-10 seconds (generate)

---

## Error Handling

### Common Errors & Solutions

#### 1. Product Not Enriched (400)
```json
{
  "success": false,
  "message": "Product must be enriched first. Use /api/v1/products/{id}/enrich/"
}
```
**Solution**: Redirect user to enrichment page

---

#### 2. Duplicate Analysis (400)
```json
{
  "success": false,
  "message": "Analysis for this product and country combination already exists"
}
```
**Solution**: Show existing analysis or offer to view/re-analyze

---

#### 3. Permission Denied (403)
```json
{
  "success": false,
  "message": "You don't have permission to access this analysis"
}
```
**Solution**: UMKM trying to access another user's analysis

---

#### 4. AI Service Failure (500)
```json
{
  "success": false,
  "message": "Compliance analysis failed: OpenAI API timeout"
}
```
**Solution**: 
- Retry mechanism in backend
- Show user: "Analysis in progress, please wait..."
- Implement async task queue (Celery)

---

#### 5. Business Profile Not Found (400)
```json
{
  "success": false,
  "message": "Business profile not found"
}
```
**Solution**: User must create business profile first

---

### Broken Pipe Error

**Cause**: Frontend timeout while backend still processing

**Impact**: 
- ✅ Analysis **COMPLETES** successfully
- ✅ Data **SAVED** to database
- ❌ Response not sent to client

**Solutions**:

1. **Increase Frontend Timeout** (Quick Fix)
```javascript
fetch(url, {
  signal: AbortSignal.timeout(120000) // 2 minutes
})
```

2. **Polling Pattern** (Recommended)
```javascript
// Start analysis
await fetch('/api/v1/export-analysis/', { method: 'POST', ... })

// Poll for completion
const checkStatus = async () => {
  const response = await fetch(`/api/v1/export-analysis/${id}/`);
  const data = await response.json();
  
  // Check if analyzed_at is recent (last 2 minutes)
  const analyzedAt = new Date(data.data.analyzed_at);
  if (Date.now() - analyzedAt < 120000) {
    return data; // Done!
  }
  
  // Wait 3 seconds, try again
  await new Promise(resolve => setTimeout(resolve, 3000));
  return checkStatus();
};
```

3. **Async Task Queue** (Production-Grade)
```python
# Use Celery for background processing
@shared_task
def analyze_product_async(product_id, country_code):
    # ... run analysis
    pass

# View returns immediately with task_id
response = {
    "task_id": "abc123",
    "status": "processing",
    "check_status_url": "/api/v1/tasks/abc123/"
}
```

---

## Performance & Optimization

### Current Performance

| Operation | Duration | API Calls | Cacheable |
|-----------|----------|-----------|-----------|
| Create Analysis | 30-60s | 4 | No |
| Re-analyze | 30-60s | 4 | No |
| Get Detail | <100ms | 0 | Yes |
| Get Regulation Recs (cached) | <50ms | 0 | Yes |
| Get Regulation Recs (new) | 5-10s | 1 | Yes |
| Compare 5 Countries | 2-5min | 4-20 | Partial |

### Optimization Strategies

#### 1. Parallel AI Calls
**Current**: Sequential (4 calls = 40s)
```python
result1 = check_ingredient()  # 10s
result2 = check_specification()  # 10s
result3 = check_packaging()  # 10s
result4 = generate_recommendations()  # 10s
```

**Optimized**: Parallel (4 calls = 10s)
```python
import asyncio

results = await asyncio.gather(
    check_ingredient_async(),
    check_specification_async(),
    check_packaging_async(),
    generate_recommendations_async()
)
```

**Benefit**: 4x faster (40s → 10s)

---

#### 2. Caching Strategy

**What to Cache**:
- ✅ Regulation recommendations (per analysis)
- ✅ Country regulations (rarely change)
- ✅ Analysis results (until re-analyzed)
- ❌ Product data (changes frequently)

**Implementation**:
```python
# Cache regulation recommendations
if analysis.regulation_recommendations_cache:
    return cached_data  # <50ms

# Cache country data
@cache_page(60 * 60 * 24)  # 24 hours
def country_detail(request, country_code):
    # ...
```

---

#### 3. Database Optimization

**Indexes**:
```python
class ExportAnalysis(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['product', 'target_country']),
            models.Index(fields=['analyzed_at']),
            models.Index(fields=['readiness_score']),
        ]
```

**Select Related**:
```python
# Bad: N+1 query problem
analyses = ExportAnalysis.objects.all()
for analysis in analyses:
    print(analysis.product.name)  # Query each time!
    print(analysis.target_country.name)  # Query each time!

# Good: Single query with joins
analyses = ExportAnalysis.objects.select_related(
    'product', 'target_country'
).all()
```

---

#### 4. Async Task Queue (Celery)

**Setup**:
```python
# celery.py
from celery import Celery

app = Celery('exportready')
app.config_from_object('django.conf:settings', namespace='CELERY')

# tasks.py
@shared_task
def analyze_product_async(product_id, country_code):
    # Long-running analysis
    result = ai_service.analyze_product_compliance(...)
    return result.id
```

**View**:
```python
def post(self, request):
    # Trigger async task
    task = analyze_product_async.delay(product_id, country_code)
    
    return Response({
        "task_id": task.id,
        "status_url": f"/api/v1/tasks/{task.id}/"
    }, status=202)  # 202 Accepted
```

**Benefits**:
- ✅ Instant API response (<100ms)
- ✅ No timeout issues
- ✅ Can handle high load
- ✅ Retry failed tasks

---

## Security & Permissions

### Authentication
- **Required**: All endpoints require JWT authentication
- **Header**: `Authorization: Bearer <access_token>`

### Authorization Rules

#### UMKM (Business Users)
```python
# Can only access their own products' analyses
if user.role == UserRole.UMKM:
    if analysis.product.business_id != user.business_profile.id:
        return 403 Forbidden
```

**Allowed Operations**:
- ✅ Create analysis for own products
- ✅ View own analyses
- ✅ Re-analyze own analyses
- ✅ Delete own analyses
- ✅ Compare own products
- ❌ View other users' analyses
- ❌ Delete other users' analyses

#### Admin
```python
# Can access all analyses
if user.role == UserRole.ADMIN:
    queryset = ExportAnalysis.objects.all()
```

**Allowed Operations**:
- ✅ View all analyses
- ✅ Delete any analysis
- ✅ Access all countries
- ✅ Monitor system usage

### Data Privacy

**Sensitive Data**:
- Product formulations (ingredients, specifications)
- Business compliance status
- Export destinations

**Protection**:
- ✅ Row-level security (ownership checks)
- ✅ Encrypted database connection
- ✅ No sensitive data in logs
- ✅ GDPR-compliant data retention

---

## API Summary Table

| Endpoint | Method | Auth | Description | PBI |
|----------|--------|------|-------------|-----|
| `/api/v1/export-analysis/` | GET | Yes | List analyses with filters | M3-01 |
| `/api/v1/export-analysis/` | POST | Yes | Create new analysis | M3-03 |
| `/api/v1/export-analysis/{id}/` | GET | Yes | Get analysis detail | M3-02 |
| `/api/v1/export-analysis/{id}/` | DELETE | Yes | Delete analysis | M3-10 |
| `/api/v1/export-analysis/{id}/reanalyze/` | POST | Yes | Re-run analysis | M3-09 |
| `/api/v1/export-analysis/compare/` | POST | Yes | Multi-country comparison | M3-13 |
| `/api/v1/export-analysis/{id}/regulation-recommendations/` | GET | Yes | Get 10-section guide | NEW |
| `/api/v1/countries/` | GET | Yes | List countries | M3-11 |
| `/api/v1/countries/{code}/` | GET | Yes | Country detail | M3-12 |

---

## Appendix

### Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, DELETE, reanalyze |
| 201 | Created | Successful POST (create analysis) |
| 400 | Bad Request | Validation error, missing enrichment |
| 403 | Forbidden | Permission denied (wrong owner) |
| 404 | Not Found | Analysis/Product/Country not found |
| 500 | Server Error | AI service failure, unexpected error |

### Environment Variables

```bash
# Kolosal AI Configuration
KOLOSAL_API_KEY=your_api_key_here
KOLOSAL_API_BASE_URL=https://api.kolosal.ai/v1
KOLOSAL_MODEL=gpt-4o-2024-08-06

# Database
DATABASE_URL=postgresql://user:pass@host:5432/exportready

# Django
DEBUG=False
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=api.exportready.ai
```

### Testing Commands

```bash
# Run all export analysis tests
pytest apps/export_analysis/tests/

# Test specific view
pytest apps/export_analysis/tests/test_views.py::TestExportAnalysisCreate

# Test with coverage
pytest --cov=apps/export_analysis --cov-report=html

# Load test (locust)
locust -f locustfile.py --host=http://localhost:8000
```

### Future Enhancements

1. **Parallel AI Calls**: Reduce analysis time from 40s to 10s
2. **WebSocket Updates**: Real-time progress updates during analysis
3. **Batch Analysis**: Analyze multiple products simultaneously
4. **Historical Comparison**: Compare analysis results over time
5. **Export Cost Calculator**: Estimate total export costs
6. **Document Generator**: Auto-generate export documentation
7. **Compliance Reminders**: Alert when regulations change
8. **AI Training**: Fine-tune model on historical data

---

## Support & Maintenance

### Logs Location
```bash
# Django logs
logs/django.log

# Celery logs (if implemented)
logs/celery.log

# AI service logs
logs/ai_service.log
```

### Monitoring Metrics
- Analysis creation rate (per hour)
- AI API success rate
- Average analysis duration
- Cache hit rate
- Error rate by type

### Maintenance Tasks
- **Daily**: Monitor AI API quotas
- **Weekly**: Review failed analyses
- **Monthly**: Update country regulations
- **Quarterly**: AI model performance review

---

**Last Updated**: December 7, 2025
**Version**: 1.0
**Maintained By**: ExportReady.AI Backend Team
