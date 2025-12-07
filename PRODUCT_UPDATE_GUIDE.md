# Product Update & Compliance Fix Guide for Frontend

## Overview
Dokumen ini menjelaskan cara frontend mengupdate informasi produk dan mengimplementasikan fitur perbaikan compliance berdasarkan hasil analisis ekspor.

## Table of Contents
1. [Product Update Flow](#product-update-flow)
2. [API Endpoints](#api-endpoints)
3. [Snapshot & Change Detection](#snapshot--change-detection)
4. [Compliance Fix Workflow](#compliance-fix-workflow)
5. [Implementation Examples](#implementation-examples)

---

## Product Update Flow

### 1. Basic Product Update
Untuk mengupdate informasi produk dasar (nama, deskripsi, kategori, dll):

**Endpoint:** `PATCH /api/v1/products/{id}/`

**Request Body:**
```json
{
  "name_local": "Keripik Singkong Pedas",
  "name_english": "Spicy Cassava Chips",
  "description_local": "Keripik singkong dengan bumbu pedas level 3",
  "description_english": "Cassava chips with level 3 spicy seasoning",
  "category_id": "SNACK_001",
  "hs_code": "2008.19.00"
}
```

**Response:**
```json
{
  "id": 123,
  "name_local": "Keripik Singkong Pedas",
  "name_english": "Spicy Cassava Chips",
  "business": 45,
  "updated_at": "2025-12-07T10:30:00Z"
}
```

### 2. Update Product Enrichment
Untuk mengupdate informasi detail produk (ingredients, packaging, specifications):

**Endpoint:** `PATCH /api/v1/products/{id}/enrichment/`

**Request Body:**
```json
{
  "ingredients": [
    {
      "name": "Singkong",
      "name_en": "Cassava",
      "percentage": 70.0
    },
    {
      "name": "Minyak Kelapa Sawit",
      "name_en": "Palm Oil",
      "percentage": 20.0
    },
    {
      "name": "Bumbu Pedas",
      "name_en": "Spicy Seasoning",
      "percentage": 10.0
    }
  ],
  "material_composition": "Cassava 70%, Palm Oil 20%, Spices 10%",
  "packaging_type": "Multi-layer plastic pouch",
  "packaging_specifications": {
    "material": "PET/PE laminated",
    "weight": "100g",
    "dimensions": "20x15x5 cm",
    "sealing": "Heat sealed"
  },
  "technical_specifications": {
    "shelf_life": "6 months",
    "storage": "Store in cool, dry place",
    "net_weight": "100g",
    "moisture_content": "< 5%"
  }
}
```

---

## API Endpoints

### Product Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/products/` | List all products | Yes (UMKM/Admin) |
| GET | `/api/v1/products/{id}/` | Get product detail | Yes |
| POST | `/api/v1/products/` | Create new product | Yes (UMKM) |
| PATCH | `/api/v1/products/{id}/` | Update product | Yes (Owner) |
| DELETE | `/api/v1/products/{id}/` | Delete product | Yes (Owner) |
| POST | `/api/v1/products/{id}/enrich/` | Create/update enrichment | Yes (Owner) |
| GET | `/api/v1/products/{id}/enrichment/` | Get enrichment detail | Yes |
| PATCH | `/api/v1/products/{id}/enrichment/` | Update enrichment | Yes (Owner) |

### Export Analysis Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/export-analysis/` | List all analyses |
| GET | `/api/v1/export-analysis/{id}/` | Get analysis detail |
| POST | `/api/v1/export-analysis/` | Create new analysis |
| GET | `/api/v1/export-analysis/{id}/regulation-recommendations/` | Get regulation recommendations |

---

## Snapshot & Change Detection

### Apa itu Product Snapshot?
Setiap kali analisis ekspor dibuat, sistem menyimpan **snapshot** lengkap dari produk pada saat itu. Ini memungkinkan:
1. **Audit trail** - Melihat kondisi produk saat analisis dilakukan
2. **Change detection** - Mendeteksi jika produk telah diupdate setelah analisis

### Cara Mengecek Perubahan Produk

**Endpoint:** `GET /api/v1/export-analysis/{id}/`

**Response:**
```json
{
  "id": 44,
  "product": 123,
  "product_name": "Keripik Singkong Pedas (Updated)",
  "target_country": "US",
  "readiness_score": 75,
  "compliance_issues": [...],
  "recommendations": "...",
  
  // Snapshot information
  "product_snapshot": {
    "name_local": "Keripik Singkong Original",
    "name_english": "Original Cassava Chips",
    "ingredients": [...],
    "packaging_type": "Simple plastic bag",
    // ... data produk saat analisis dibuat
  },
  "snapshot_product_name": "Keripik Singkong Original",
  "product_changed": true  // ← PENTING! Indikator perubahan
}
```

### Interpretasi `product_changed`

```javascript
if (analysis.product_changed === true) {
  // Produk telah diupdate sejak analisis terakhir
  // Tampilkan notifikasi: "Product has been updated. Re-analysis recommended."
  // Tampilkan tombol: "Re-analyze Product"
  showReAnalysisPrompt();
} else {
  // Produk masih sama seperti saat analisis
  // Hasil analisis masih relevan
  displayAnalysisResults();
}
```

---

## Compliance Fix Workflow

### Step 1: Dapatkan Analysis & Recommendations

**Request:**
```http
GET /api/v1/export-analysis/44/ HTTP/1.1
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": 44,
  "product": 123,
  "readiness_score": 65,
  "status_grade": "MEDIUM",
  "compliance_issues": {
    "ingredient_compliance": {
      "status": "FAIL",
      "violations": [
        {
          "ingredient": "Palm Oil",
          "reason": "Requires specific certification for US export"
        }
      ]
    },
    "packaging_compliance": {
      "status": "FAIL",
      "violations": [
        {
          "issue": "Missing nutritional information panel",
          "requirement": "FDA requires nutritional facts label"
        }
      ]
    }
  },
  "recommendations": "1. Obtain RSPO certification for palm oil...\n2. Add FDA-compliant nutrition label..."
}
```

### Step 2: Dapatkan Regulation Recommendations (10 Section Guide)

**Request:**
```http
GET /api/v1/export-analysis/44/regulation-recommendations/ HTTP/1.1
Accept-Language: id
Authorization: Bearer {token}
```

**Response:**
```json
{
  "analysis_id": 44,
  "product_name": "Keripik Singkong Pedas",
  "target_country": "US",
  "target_country_name": "United States",
  "generated_at": "2025-12-07T10:30:00Z",
  "language": "id",
  "recommendations": {
    "overview": {
      "summary": "Panduan komprehensif ekspor makanan ringan ke Amerika Serikat...",
      "key_points": [
        "FDA mengatur semua produk makanan",
        "Sertifikasi HACCP diperlukan",
        "Label nutrisi wajib sesuai format FDA"
      ]
    },
    "prohibited_items": {
      "summary": "Daftar bahan yang dilarang atau dibatasi oleh FDA...",
      "key_points": [...]
    },
    "import_restrictions": {
      "summary": "Persyaratan impor khusus untuk produk makanan...",
      "key_points": [...]
    },
    "certifications": {
      "summary": "Sertifikasi yang diperlukan...",
      "action_items": [
        "Dapatkan sertifikasi HACCP",
        "Registrasi FDA Food Facility",
        "Sertifikasi halal (opsional)"
      ]
    },
    "labeling_requirements": {
      "summary": "Persyaratan label sesuai FDA...",
      "action_items": [
        "Tambahkan Nutrition Facts panel",
        "Cantumkan daftar ingredients dalam bahasa Inggris",
        "Sertakan allergen warnings"
      ]
    },
    "customs_procedures": {
      "summary": "Prosedur bea cukai...",
      "action_items": [...]
    },
    "testing_inspection": {
      "summary": "Pengujian dan inspeksi yang diperlukan...",
      "action_items": [...]
    },
    "intellectual_property": {
      "summary": "Perlindungan merek dan hak cipta...",
      "key_points": [...]
    },
    "shipping_logistics": {
      "summary": "Persyaratan pengiriman dan logistik...",
      "key_points": [...]
    },
    "timeline_costs": {
      "summary": "Estimasi waktu dan biaya...",
      "key_points": [...]
    }
  },
  "cached": false
}
```

### Step 3: Tampilkan UI Perbaikan

Frontend harus menampilkan:

1. **Compliance Status Card**
```jsx
<ComplianceCard>
  <StatusBadge score={65} grade="MEDIUM" />
  <ScoreBar percentage={65} />
  
  <IssuesList>
    <IssueItem severity="high">
      ❌ Ingredient Compliance: Palm Oil certification required
    </IssueItem>
    <IssueItem severity="high">
      ❌ Packaging Compliance: Missing FDA nutrition label
    </IssueItem>
  </IssuesList>
  
  <Button onClick={showFixModal}>Fix Compliance Issues</Button>
</ComplianceCard>
```

2. **Fix Wizard Modal**
```jsx
<FixWizard>
  <Step1_ReviewIssues issues={complianceIssues} />
  <Step2_RegulationGuide recommendations={regulationRecommendations} />
  <Step3_UpdateProduct productId={123} />
  <Step4_ReAnalyze analysisId={44} />
</FixWizard>
```

### Step 4: Update Product (Fix Issues)

**Request untuk fix packaging issue:**
```http
PATCH /api/v1/products/123/enrichment/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "packaging_specifications": {
    "material": "FDA-approved PET/PE laminated",
    "weight": "100g",
    "dimensions": "20x15x5 cm",
    "sealing": "Heat sealed",
    "has_nutrition_label": true,
    "nutrition_label_format": "FDA compliant"
  },
  "certifications": [
    {
      "name": "HACCP",
      "status": "in_progress"
    },
    {
      "name": "FDA Food Facility Registration",
      "number": "12345678",
      "status": "active"
    }
  ]
}
```

**Request untuk fix ingredient issue:**
```http
PATCH /api/v1/products/123/enrichment/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "ingredients": [
    {
      "name": "Singkong",
      "name_en": "Cassava",
      "percentage": 70.0,
      "certifications": ["Organic"]
    },
    {
      "name": "Minyak Kelapa Sawit",
      "name_en": "RSPO Certified Palm Oil",
      "percentage": 20.0,
      "certifications": ["RSPO"]  // ← Tambahkan sertifikasi
    },
    {
      "name": "Bumbu Pedas",
      "name_en": "Spicy Seasoning",
      "percentage": 10.0
    }
  ]
}
```

### Step 5: Re-analyze Product

Setelah update, sarankan user untuk re-analyze:

**Request:**
```http
POST /api/v1/export-analysis/ HTTP/1.1
Content-Type: application/json
Authorization: Bearer {token}

{
  "product_id": 123,
  "target_country_code": "US"
}
```

**Expected Response (jika fix berhasil):**
```json
{
  "id": 45,  // New analysis ID
  "product": 123,
  "target_country": "US",
  "readiness_score": 85,  // ← Score meningkat!
  "status_grade": "HIGH",
  "compliance_issues": {
    "ingredient_compliance": {
      "status": "PASS"  // ← Sekarang PASS!
    },
    "packaging_compliance": {
      "status": "PASS"  // ← Sekarang PASS!
    }
  },
  "analyzed_at": "2025-12-07T11:00:00Z"
}
```

---

## Implementation Examples

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';
import { api } from './api';

function ProductComplianceFix({ analysisId }) {
  const [analysis, setAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalysisData();
  }, [analysisId]);

  const loadAnalysisData = async () => {
    try {
      // Get analysis detail
      const analysisRes = await api.get(`/export-analysis/${analysisId}/`);
      setAnalysis(analysisRes.data);

      // Get regulation recommendations
      const recsRes = await api.get(
        `/export-analysis/${analysisId}/regulation-recommendations/`,
        { headers: { 'Accept-Language': 'id' } }
      );
      setRecommendations(recsRes.data);

      setLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleFixIngredients = async (updatedIngredients) => {
    try {
      await api.patch(`/products/${analysis.product}/enrichment/`, {
        ingredients: updatedIngredients
      });
      alert('Ingredients updated successfully!');
    } catch (error) {
      console.error('Failed to update:', error);
    }
  };

  const handleReAnalyze = async () => {
    try {
      const res = await api.post('/export-analysis/', {
        product_id: analysis.product,
        target_country_code: analysis.target_country
      });
      
      // Redirect to new analysis
      window.location.href = `/analysis/${res.data.id}`;
    } catch (error) {
      console.error('Failed to re-analyze:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="compliance-fix-container">
      {/* Product Change Warning */}
      {analysis.product_changed && (
        <div className="alert alert-warning">
          ⚠️ Product has been updated since this analysis.
          <button onClick={handleReAnalyze}>Re-analyze Now</button>
        </div>
      )}

      {/* Compliance Score */}
      <div className="score-card">
        <h3>Readiness Score: {analysis.readiness_score}/100</h3>
        <div className="progress-bar">
          <div style={{ width: `${analysis.readiness_score}%` }} />
        </div>
        <span className={`badge ${analysis.status_grade.toLowerCase()}`}>
          {analysis.status_grade}
        </span>
      </div>

      {/* Compliance Issues */}
      <div className="issues-section">
        <h4>Issues Found</h4>
        {Object.entries(analysis.compliance_issues).map(([key, issue]) => (
          <IssueCard key={key} type={key} issue={issue} />
        ))}
      </div>

      {/* Regulation Guide */}
      <div className="regulation-guide">
        <h4>Regulation Guide for {recommendations.target_country_name}</h4>
        
        {/* Overview */}
        <section>
          <h5>📋 Overview</h5>
          <p>{recommendations.recommendations.overview.summary}</p>
          <ul>
            {recommendations.recommendations.overview.key_points.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>
        </section>

        {/* Certifications */}
        <section>
          <h5>✅ Required Certifications</h5>
          <p>{recommendations.recommendations.certifications.summary}</p>
          <ul>
            {recommendations.recommendations.certifications.action_items.map((item, i) => (
              <li key={i}>
                <input type="checkbox" id={`cert-${i}`} />
                <label htmlFor={`cert-${i}`}>{item}</label>
              </li>
            ))}
          </ul>
        </section>

        {/* Labeling */}
        <section>
          <h5>🏷️ Labeling Requirements</h5>
          <p>{recommendations.recommendations.labeling_requirements.summary}</p>
          <ul>
            {recommendations.recommendations.labeling_requirements.action_items.map((item, i) => (
              <li key={i}>
                <input type="checkbox" id={`label-${i}`} />
                <label htmlFor={`label-${i}`}>{item}</label>
              </li>
            ))}
          </ul>
        </section>

        {/* ... other sections ... */}
      </div>

      {/* Fix Actions */}
      <div className="fix-actions">
        <button 
          className="btn btn-primary"
          onClick={() => openFixModal()}
        >
          Update Product Information
        </button>
        <button 
          className="btn btn-success"
          onClick={handleReAnalyze}
        >
          Re-analyze After Fixes
        </button>
      </div>
    </div>
  );
}

function IssueCard({ type, issue }) {
  const getIcon = (status) => {
    return status === 'PASS' ? '✅' : '❌';
  };

  return (
    <div className={`issue-card ${issue.status.toLowerCase()}`}>
      <h5>
        {getIcon(issue.status)} {type.replace('_', ' ').toUpperCase()}
      </h5>
      {issue.violations && (
        <ul>
          {issue.violations.map((v, i) => (
            <li key={i}>{v.reason || v.issue}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ProductComplianceFix;
```

### Vue.js Example

```vue
<template>
  <div class="compliance-fix">
    <!-- Change Warning -->
    <div v-if="analysis?.product_changed" class="alert alert-warning">
      ⚠️ Produk telah diupdate sejak analisis terakhir
      <button @click="reAnalyze">Analisis Ulang</button>
    </div>

    <!-- Score Display -->
    <div class="score-section">
      <h3>Skor Kesiapan: {{ analysis?.readiness_score }}/100</h3>
      <progress :value="analysis?.readiness_score" max="100" />
    </div>

    <!-- Issues List -->
    <div class="issues">
      <h4>Masalah yang Ditemukan:</h4>
      <div 
        v-for="(issue, key) in analysis?.compliance_issues" 
        :key="key"
        class="issue-item"
      >
        <h5>{{ formatIssueType(key) }}</h5>
        <ul v-if="issue.violations">
          <li v-for="(v, i) in issue.violations" :key="i">
            {{ v.reason || v.issue }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Regulation Guide -->
    <div v-if="recommendations" class="regulation-guide">
      <h4>Panduan Regulasi {{ recommendations.target_country_name }}</h4>
      
      <!-- Each section -->
      <section v-for="(section, key) in recommendations.recommendations" :key="key">
        <h5>{{ formatSectionTitle(key) }}</h5>
        <p>{{ section.summary }}</p>
        <ul v-if="section.action_items">
          <li v-for="(item, i) in section.action_items" :key="i">
            <input type="checkbox" :id="`action-${key}-${i}`" />
            <label :for="`action-${key}-${i}`">{{ item }}</label>
          </li>
        </ul>
        <ul v-else-if="section.key_points">
          <li v-for="(point, i) in section.key_points" :key="i">{{ point }}</li>
        </ul>
      </section>
    </div>

    <!-- Action Buttons -->
    <div class="actions">
      <button @click="showUpdateModal = true" class="btn-primary">
        Update Informasi Produk
      </button>
      <button @click="reAnalyze" class="btn-success">
        Analisis Ulang
      </button>
    </div>

    <!-- Update Modal -->
    <ProductUpdateModal 
      v-if="showUpdateModal"
      :product-id="analysis?.product"
      @close="showUpdateModal = false"
      @updated="onProductUpdated"
    />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';

export default {
  name: 'ComplianceFix',
  props: {
    analysisId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const analysis = ref(null);
    const recommendations = ref(null);
    const showUpdateModal = ref(false);

    const loadData = async () => {
      try {
        // Load analysis
        const analysisRes = await axios.get(`/api/v1/export-analysis/${props.analysisId}/`);
        analysis.value = analysisRes.data;

        // Load recommendations
        const recsRes = await axios.get(
          `/api/v1/export-analysis/${props.analysisId}/regulation-recommendations/`,
          { headers: { 'Accept-Language': 'id' } }
        );
        recommendations.value = recsRes.data;
      } catch (error) {
        console.error('Failed to load data:', error);
      }
    };

    const reAnalyze = async () => {
      try {
        const res = await axios.post('/api/v1/export-analysis/', {
          product_id: analysis.value.product,
          target_country_code: analysis.value.target_country
        });
        // Redirect to new analysis
        window.location.href = `/analysis/${res.data.id}`;
      } catch (error) {
        console.error('Re-analysis failed:', error);
      }
    };

    const onProductUpdated = () => {
      showUpdateModal.value = false;
      alert('Produk berhasil diupdate! Silakan analisis ulang.');
    };

    const formatIssueType = (type) => {
      return type.replace(/_/g, ' ').toUpperCase();
    };

    const formatSectionTitle = (key) => {
      const titles = {
        overview: '📋 Ringkasan',
        prohibited_items: '🚫 Item Terlarang',
        import_restrictions: '⚠️ Pembatasan Impor',
        certifications: '✅ Sertifikasi',
        labeling_requirements: '🏷️ Persyaratan Label',
        customs_procedures: '📦 Prosedur Bea Cukai',
        testing_inspection: '🔬 Pengujian & Inspeksi',
        intellectual_property: '©️ Hak Kekayaan Intelektual',
        shipping_logistics: '🚢 Pengiriman & Logistik',
        timeline_costs: '💰 Timeline & Biaya'
      };
      return titles[key] || key;
    };

    onMounted(loadData);

    return {
      analysis,
      recommendations,
      showUpdateModal,
      reAnalyze,
      onProductUpdated,
      formatIssueType,
      formatSectionTitle
    };
  }
};
</script>
```

---

## Best Practices

### 1. Always Check `product_changed` Flag
```javascript
// ❌ BAD: Tidak cek perubahan
function showAnalysis(analysis) {
  displayResults(analysis);
}

// ✅ GOOD: Cek perubahan dan notifikasi user
function showAnalysis(analysis) {
  if (analysis.product_changed) {
    showWarning('Product has been updated. Consider re-analyzing.');
  }
  displayResults(analysis);
}
```

### 2. Use Accept-Language Header
```javascript
// ❌ BAD: Tidak set language
const response = await fetch('/api/v1/export-analysis/44/regulation-recommendations/');

// ✅ GOOD: Set language preference
const response = await fetch(
  '/api/v1/export-analysis/44/regulation-recommendations/',
  { headers: { 'Accept-Language': 'id' } }  // atau 'en'
);
```

### 3. Handle Validation Errors
```javascript
try {
  await api.patch(`/products/${id}/enrichment/`, data);
} catch (error) {
  if (error.response?.status === 400) {
    // Validation error
    const errors = error.response.data;
    displayValidationErrors(errors);
  } else {
    // Other error
    console.error('Update failed:', error);
  }
}
```

### 4. Progressive Enhancement
```javascript
// Show loading states
setLoading(true);

// Load analysis
const analysis = await loadAnalysis(id);
setAnalysis(analysis);

// Load recommendations (additional feature)
try {
  const recommendations = await loadRecommendations(id);
  setRecommendations(recommendations);
} catch (error) {
  // Recommendations are optional, continue without them
  console.warn('Recommendations unavailable:', error);
}

setLoading(false);
```

### 5. Optimize Re-analysis
```javascript
// ❌ BAD: Re-analyze on every small change
onChange={(field, value) => {
  updateProduct(field, value);
  reAnalyze();  // Too frequent!
}}

// ✅ GOOD: Batch changes, then suggest re-analysis
const [pendingChanges, setPendingChanges] = useState([]);

onChange={(field, value) => {
  setPendingChanges([...pendingChanges, { field, value }]);
}}

onSaveAll={() => {
  updateProduct(pendingChanges);
  showReAnalysisPrompt();  // Suggest, don't force
}}
```

---

## Error Handling

### Common Error Scenarios

#### 1. Product Not Found (404)
```json
{
  "detail": "Not found."
}
```
**Action:** Redirect to product list or show error message.

#### 2. Permission Denied (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```
**Action:** Show "You can only edit your own products" message.

#### 3. Validation Error (400)
```json
{
  "ingredients": [
    "This field is required."
  ],
  "packaging_specifications": [
    "Invalid format."
  ]
}
```
**Action:** Show field-level validation errors in form.

#### 4. Product Not Enriched (400)
```json
{
  "detail": "Product must be enriched first. Use /api/v1/products/{id}/enrich/"
}
```
**Action:** Redirect to enrichment page.

#### 5. Analysis Already Exists (400)
```json
{
  "non_field_errors": [
    "Analysis for this product and country combination already exists"
  ]
}
```
**Action:** Show existing analysis or offer to view it.

---

## Testing Checklist

### Frontend Testing
- [ ] Product update form validates required fields
- [ ] Enrichment update preserves existing data
- [ ] Change detection warning displays correctly
- [ ] Re-analysis button creates new analysis
- [ ] Regulation recommendations load in correct language
- [ ] Compliance score updates after fixes
- [ ] Error messages display user-friendly text
- [ ] Loading states prevent duplicate requests
- [ ] Permission errors handled gracefully
- [ ] Responsive design works on mobile

### API Testing
- [ ] PATCH `/products/{id}/` updates basic info
- [ ] PATCH `/products/{id}/enrichment/` updates enrichment
- [ ] POST `/export-analysis/` creates new analysis
- [ ] GET `/export-analysis/{id}/` shows `product_changed` correctly
- [ ] GET `/regulation-recommendations/` returns 10 sections
- [ ] Accept-Language header changes response language
- [ ] Validation errors return 400 with details
- [ ] Permission checks enforce ownership
- [ ] Snapshot captures product state correctly
- [ ] Cache works for regulation recommendations

---

## Summary

**Key Points for Frontend Team:**

1. **Update Flow:** `Product Update → Enrichment Update → Re-analyze → Check Score`

2. **Critical APIs:**
   - `PATCH /products/{id}/` - Basic product info
   - `PATCH /products/{id}/enrichment/` - Detailed info
   - `GET /export-analysis/{id}/` - Analysis results + change detection
   - `GET /export-analysis/{id}/regulation-recommendations/` - 10-section guide

3. **Change Detection:** Always check `product_changed` flag and prompt re-analysis

4. **Regulation Guide:** Use 10-section recommendations to guide users through fixes

5. **Language Support:** Use `Accept-Language: id` or `en` header

6. **Error Handling:** Show validation errors inline, permission errors globally

**Next Steps:**
- Implement product edit form with validation
- Create compliance fix wizard component
- Add re-analysis prompt when `product_changed === true`
- Display regulation recommendations in tabbed or accordion UI
- Test complete flow from issue detection to fix to re-analysis
