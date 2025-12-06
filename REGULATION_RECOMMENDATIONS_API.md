# Regulation Recommendations API Documentation

## Overview
The Regulation Recommendations API provides comprehensive, AI-powered guidance for Indonesian UMKM exports. It delivers SPECIFIC, actionable recommendations covering certifications, labeling, documentation, tariffs, and country-specific requirements.

**Key Features:**
- ✅ Bilingual support (Indonesian/English)
- ✅ Specific cost estimates in IDR
- ✅ Processing time estimates
- ✅ Step-by-step guidance
- ✅ Priority-based action lists
- ✅ Material-specific regulations
- ✅ Real regulation references (19 CFR, EU numbers, etc.)

---

## Endpoint

### `POST /api/v1/export-analysis/regulation-recommendations/`

Generate comprehensive regulation recommendations for exporting products to a target country.

**Authentication:** Required (Bearer Token)

---

## Request Parameters

### Option 1: Using Existing Analysis
```json
{
  "analysis_id": 123,
  "language": "id"  // "id" for Indonesian (default), "en" for English
}
```

### Option 2: Using Product + Country
```json
{
  "product_id": 456,
  "target_country_code": "US",
  "language": "en"  // "id" for Indonesian (default), "en" for English
}
```

**Note:** You must provide either `analysis_id` OR both `product_id` and `target_country_code`.

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `analysis_id` | integer | Conditional* | ID of existing export analysis |
| `product_id` | integer | Conditional* | ID of product to analyze |
| `target_country_code` | string(2) | Conditional* | ISO 2-letter country code (e.g., "US", "JP", "AU") |
| `language` | string | No | Output language: `"id"` (Indonesian, default) or `"en"` (English) |

*Either `analysis_id` OR (`product_id` + `target_country_code`) must be provided.

---

## Response Structure

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Regulation recommendations generated successfully",
  "data": {
    "analysis_id": 123,
    "product_id": 456,
    "product_name": "Tas Rotan Handmade",
    "target_country": "United States",
    "country_code": "US",
    "readiness_score": 75,
    "status_grade": "Warning",
    "language": "id",
    "regulation_recommendations": {
      "product_classification": { ... },
      "required_certifications": [ ... ],
      "material_specific_regulations": [ ... ],
      "labeling_requirements": [ ... ],
      "packaging_requirements": [ ... ],
      "import_documentation": [ ... ],
      "tariff_and_duties": { ... },
      "prohibited_or_restricted": { ... },
      "action_priority_list": [ ... ],
      "country_specific_notes": [ ... ]
    }
  }
}
```

---

## Detailed Response Schema

### 1. Product Classification
```json
"product_classification": {
  "detected_category": "Kerajinan Tangan - Tas Rotan",
  "hs_code_suggestion": "46021200",
  "hs_description": "Barang anyaman dari bahan nabati",
  "regulatory_category": "Produk Konsumen"
}
```

### 2. Required Certifications
Array of certifications needed for export:

```json
"required_certifications": [
  {
    "certification_name": "Certificate of Origin (SKA)",
    "regulatory_body": "Kamar Dagang dan Industri (KADIN) Indonesia",
    "why_applicable": "Diperlukan untuk mendapatkan preferensi tarif GSP di AS",
    "estimated_cost_idr": "100.000 - 500.000",
    "processing_time": "3-5 hari kerja",
    "how_to_obtain": "1. Siapkan invoice dan packing list\n2. Ajukan ke KADIN setempat\n3. Bayar biaya administrasi\n4. Dapatkan SKA Form A",
    "priority": "critical",  // critical | high | medium | low
    "applicable": true,
    "not_applicable_reason": ""
  }
]
```

**Priority Levels:**
- `critical`: Must have before export
- `high`: Strongly recommended
- `medium`: Good to have
- `low`: Optional

### 3. Material-Specific Regulations
Regulations for each material in the product composition:

```json
"material_specific_regulations": [
  {
    "material": "Rotan",
    "percentage": "80%",
    "applicable_regulations": [
      {
        "regulation_name": "CITES",
        "regulation_number": "CITES Appendix II/III",
        "requirement": "Pastikan rotan bukan dari spesies dilindungi",
        "compliance_action": "Dapatkan dokumen dari pemasok",
        "documentation_needed": "Surat Keterangan Sumber Rotan",
        "risk_if_non_compliant": "Produk dapat ditahan di bea cukai"
      }
    ]
  }
]
```

### 4. Labeling Requirements
Specific labeling standards with regulation references:

```json
"labeling_requirements": [
  {
    "requirement_name": "Country of Origin Marking",
    "regulation_reference": "19 CFR Part 134",
    "specification": "Label harus mencantumkan 'Made in Indonesia' dengan jelas dan permanen",
    "language_requirement": "Bahasa Inggris",
    "placement": "Pada produk atau kemasan yang mudah terlihat",
    "mandatory": true,
    "example": "Made in Indonesia | Handcrafted Rattan"
  }
]
```

### 5. Packaging Requirements
```json
"packaging_requirements": [
  {
    "requirement_name": "Kemasan Ramah Lingkungan",
    "current_packaging": "Kardus dengan bubble wrap",
    "compliance_status": "compliant",  // compliant | non_compliant | needs_verification
    "regulation_reference": "US EPA Guidelines",
    "action_needed": "Sudah sesuai, tidak ada tindakan diperlukan",
    "notes": "Kardus dapat didaur ulang"
  }
]
```

### 6. Import Documentation
Complete checklist of required documents:

```json
"import_documentation": [
  {
    "document_name": "Commercial Invoice",
    "required": true,
    "issuing_authority": "Eksportir (Anda)",
    "purpose": "Dokumen dasar untuk bea cukai",
    "must_include": [
      "Deskripsi produk",
      "Kode HS",
      "Nilai FOB",
      "Origin Indonesia"
    ],
    "estimated_cost_idr": "0 (buat sendiri)",
    "processing_time": "1 hari"
  }
]
```

### 7. Tariff and Duties
```json
"tariff_and_duties": {
  "hs_code": "46021200",
  "mfn_duty_rate": "4.0%",
  "preferential_schemes": [
    {
      "scheme_name": "Generalized System of Preferences (GSP)",
      "preferential_rate": "0% (duty-free)",
      "conditions": "Produk harus memenuhi kriteria origin Indonesia",
      "certificate_needed": "Certificate of Origin Form A"
    }
  ]
}
```

### 8. Prohibited or Restricted
```json
"prohibited_or_restricted": {
  "is_prohibited": false,
  "is_restricted": false,
  "restrictions": [],
  "special_permits_needed": []
}
```

### 9. Action Priority List
Prioritized to-do list with time and cost estimates:

```json
"action_priority_list": [
  {
    "priority_order": 1,
    "action": "Dapatkan Certificate of Origin (Form A) dari KADIN",
    "category": "Dokumentasi",  // Certification | Labeling | Documentation | Material | Packaging
    "estimated_time": "1 minggu",
    "estimated_cost_idr": "100.000 - 500.000",
    "blocking_export": true  // true = must complete before export
  }
]
```

**Categories:**
- `Certification`: Obtaining certifications
- `Labeling`: Label creation/modification
- `Documentation`: Document preparation
- `Material`: Material verification/sourcing
- `Packaging`: Packaging changes

### 10. Country-Specific Notes
```json
"country_specific_notes": [
  "Amerika Serikat sangat ketat dalam hal labeling dan dokumentasi",
  "Pastikan semua dokumen dalam bahasa Inggris",
  "GSP dapat menghemat biaya tarif hingga 4% dari nilai barang"
]
```

---

## Error Responses

### 400 Bad Request
Missing or invalid parameters:
```json
{
  "success": false,
  "message": "Validation error",
  "errors": {
    "non_field_errors": [
      "Either 'analysis_id' or both 'product_id' and 'target_country_code' must be provided"
    ]
  }
}
```

### 401 Unauthorized
Missing or invalid authentication:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
Trying to access another user's analysis:
```json
{
  "success": false,
  "message": "You can only access your own analyses"
}
```

### 404 Not Found
Analysis, product, or country not found:
```json
{
  "success": false,
  "message": "Analysis not found"
}
```

### 500 Internal Server Error
AI service failure (fallback recommendations provided):
```json
{
  "success": false,
  "message": "Failed to generate recommendations: AI service unavailable"
}
```

---

## Usage Examples

### Example 1: Get Recommendations for Existing Analysis (Indonesian)

**Request:**
```bash
curl -X POST https://api.exportready.ai/api/v1/export-analysis/regulation-recommendations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 123,
    "language": "id"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Rekomendasi regulasi berhasil dibuat",
  "data": {
    "analysis_id": 123,
    "product_id": 456,
    "product_name": "Tas Rotan Handmade",
    "target_country": "United States",
    "country_code": "US",
    "readiness_score": 75,
    "status_grade": "Warning",
    "language": "id",
    "regulation_recommendations": {
      // ... full recommendations object
    }
  }
}
```

### Example 2: Generate New Analysis with Recommendations (English)

**Request:**
```bash
curl -X POST https://api.exportready.ai/api/v1/export-analysis/regulation-recommendations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 456,
    "target_country_code": "JP",
    "language": "en"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Regulation recommendations generated successfully",
  "data": {
    "analysis_id": 124,
    "product_id": 456,
    "product_name": "Tas Rotan Handmade",
    "target_country": "Japan",
    "country_code": "JP",
    "readiness_score": 85,
    "status_grade": "Ready",
    "language": "en",
    "regulation_recommendations": {
      // ... full recommendations object in English
    }
  }
}
```

---

## Frontend Integration Guide

### 1. Displaying Action Priority List

Show as a checklist/stepper with:
- Priority badge (critical = red, high = orange, medium = yellow, low = green)
- Time estimate
- Cost estimate
- "Blocking Export" warning if applicable

```jsx
// Example React Component
<div className="action-priority-list">
  {actionList.map((action) => (
    <div key={action.priority_order} className="action-item">
      <div className="priority-badge" data-priority={action.priority}>
        {action.priority_order}
      </div>
      <div className="action-content">
        <h4>{action.action}</h4>
        <div className="action-meta">
          <span className="category">{action.category}</span>
          <span className="time">{action.estimated_time}</span>
          <span className="cost">{action.estimated_cost_idr}</span>
          {action.blocking_export && (
            <span className="warning">⚠️ Required before export</span>
          )}
        </div>
      </div>
    </div>
  ))}
</div>
```

### 2. Certification Cards

Display certifications with expandable details:

```jsx
<div className="certifications-grid">
  {certifications.map((cert) => (
    <Card key={cert.certification_name}>
      <CardHeader>
        <h3>{cert.certification_name}</h3>
        <Badge variant={cert.priority}>{cert.priority}</Badge>
      </CardHeader>
      <CardContent>
        <p className="why">{cert.why_applicable}</p>
        <div className="meta">
          <div>💰 {cert.estimated_cost_idr}</div>
          <div>⏱️ {cert.processing_time}</div>
        </div>
        <Accordion>
          <AccordionItem title="How to Obtain">
            <p>{cert.how_to_obtain}</p>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  ))}
</div>
```

### 3. Document Checklist

Interactive checklist for required documents:

```jsx
<div className="document-checklist">
  {documents.map((doc) => (
    <div key={doc.document_name} className="document-item">
      <Checkbox id={doc.document_name} />
      <label htmlFor={doc.document_name}>
        <h4>
          {doc.document_name}
          {doc.required && <span className="required">*</span>}
        </h4>
        <p>{doc.purpose}</p>
        <div className="document-meta">
          <span>📍 {doc.issuing_authority}</span>
          <span>💰 {doc.estimated_cost_idr}</span>
          <span>⏱️ {doc.processing_time}</span>
        </div>
      </label>
    </div>
  ))}
</div>
```

### 4. Material Compliance Viewer

Show regulations for each material:

```jsx
<div className="material-regulations">
  {materials.map((mat) => (
    <Accordion key={mat.material}>
      <AccordionItem 
        title={`${mat.material} (${mat.percentage})`}
        badge={mat.applicable_regulations.length}
      >
        {mat.applicable_regulations.map((reg) => (
          <div key={reg.regulation_name} className="regulation">
            <h5>{reg.regulation_name}</h5>
            {reg.regulation_number && (
              <span className="reg-number">{reg.regulation_number}</span>
            )}
            <p><strong>Requirement:</strong> {reg.requirement}</p>
            <p><strong>Action:</strong> {reg.compliance_action}</p>
            <Alert variant="warning">{reg.risk_if_non_compliant}</Alert>
          </div>
        ))}
      </AccordionItem>
    </Accordion>
  ))}
</div>
```

### 5. Tariff Calculator

Show potential savings with preferential schemes:

```jsx
<div className="tariff-calculator">
  <h3>Tariff Information</h3>
  <div className="hs-code">
    <strong>HS Code:</strong> {tariff.hs_code}
  </div>
  <div className="duty-rates">
    <div className="normal-rate">
      <span>Normal MFN Rate:</span>
      <span className="rate">{tariff.mfn_duty_rate}</span>
    </div>
    {tariff.preferential_schemes.map((scheme) => (
      <div key={scheme.scheme_name} className="preferential-rate">
        <h4>{scheme.scheme_name}</h4>
        <div className="rate-savings">
          <span className="rate">{scheme.preferential_rate}</span>
          <Badge variant="success">Savings!</Badge>
        </div>
        <p className="conditions">{scheme.conditions}</p>
        <p className="certificate">📜 {scheme.certificate_needed}</p>
      </div>
    ))}
  </div>
</div>
```

---

## Best Practices

### 1. Language Selection
- Default to Indonesian for UMKM users in Indonesia
- Provide language toggle (ID/EN) prominently
- Store user preference

### 2. Progressive Disclosure
- Show summary/overview first
- Use accordions for detailed sections
- Highlight critical/blocking items

### 3. Cost Transparency
- Always display costs in IDR
- Show cost ranges (min-max)
- Sum up total estimated costs

### 4. Timeline Visualization
- Show estimated timeline as Gantt chart or calendar
- Highlight parallel vs sequential tasks
- Calculate total time to export readiness

### 5. Downloadable Report
- Offer PDF export of recommendations
- Include print-friendly version
- Add QR codes for document links

### 6. Progress Tracking
- Allow users to mark actions as complete
- Save progress to backend
- Show completion percentage

### 7. Help & Support
- Add tooltips for technical terms
- Link to regulation texts
- Provide contact info for authorities

---

## Testing

Run tests with:
```bash
pytest apps/export_analysis/tests/test_regulation_recommendations.py -v
```

---

## Notes

1. **AI-Powered**: Recommendations are generated by AI based on product details, materials, and target country regulations. Always review with trade experts.

2. **Fallback Handling**: If AI service fails, fallback recommendations with basic structure are provided.

3. **Real-time Updates**: Regulations change frequently. Always verify with official sources before export.

4. **Cost Estimates**: Costs are estimates in IDR and may vary. Check with actual service providers.

5. **Bilingual Support**: Both Indonesian and English outputs follow the same schema for consistent frontend rendering.

---

## Support

For API issues or questions:
- Backend: Contact development team
- Regulations: Consult with trade compliance team
- Frontend: See integration examples above
