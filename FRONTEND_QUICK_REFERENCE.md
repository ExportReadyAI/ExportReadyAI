# Regulation Recommendations - Quick Reference Card

## 🚀 Quick Start

### Endpoint
```
POST /api/v1/export-analysis/regulation-recommendations/
```

### Authentication
```javascript
headers: {
  'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
  'Content-Type': 'application/json'
}
```

---

## 📋 Request Options

### Option 1: From Existing Analysis
```json
{
  "analysis_id": 123,
  "language": "id"
}
```

### Option 2: New Analysis
```json
{
  "product_id": 456,
  "target_country_code": "US",
  "language": "en"
}
```

---

## 🎯 Response Quick Map

```javascript
response.data = {
  analysis_id: number,
  product_id: number,
  product_name: string,
  target_country: string,
  country_code: string,
  readiness_score: number (0-100),
  status_grade: "Ready" | "Warning" | "Critical",
  language: "id" | "en",
  regulation_recommendations: {
    // 10 sections below
  }
}
```

---

## 📦 10 Data Sections

### 1. product_classification
```javascript
{
  detected_category: string,
  hs_code_suggestion: string,
  hs_description: string,
  regulatory_category: string
}
```

### 2. required_certifications
```javascript
[{
  certification_name: string,
  regulatory_body: string,
  why_applicable: string,
  estimated_cost_idr: string,
  processing_time: string,
  how_to_obtain: string,
  priority: "critical" | "high" | "medium" | "low",
  applicable: boolean,
  not_applicable_reason: string
}]
```

### 3. material_specific_regulations
```javascript
[{
  material: string,
  percentage: string,
  applicable_regulations: [{
    regulation_name: string,
    regulation_number: string,
    requirement: string,
    compliance_action: string,
    documentation_needed: string,
    risk_if_non_compliant: string
  }]
}]
```

### 4. labeling_requirements
```javascript
[{
  requirement_name: string,
  regulation_reference: string,
  specification: string,
  language_requirement: string,
  placement: string,
  mandatory: boolean,
  example: string
}]
```

### 5. packaging_requirements
```javascript
[{
  requirement_name: string,
  current_packaging: string,
  compliance_status: "compliant" | "non_compliant" | "needs_verification",
  regulation_reference: string,
  action_needed: string,
  notes: string
}]
```

### 6. import_documentation
```javascript
[{
  document_name: string,
  required: boolean,
  issuing_authority: string,
  purpose: string,
  must_include: string[],
  estimated_cost_idr: string,
  processing_time: string
}]
```

### 7. tariff_and_duties
```javascript
{
  hs_code: string,
  mfn_duty_rate: string,
  preferential_schemes: [{
    scheme_name: string,
    preferential_rate: string,
    conditions: string,
    certificate_needed: string
  }]
}
```

### 8. prohibited_or_restricted
```javascript
{
  is_prohibited: boolean,
  is_restricted: boolean,
  restrictions: string[],
  special_permits_needed: string[]
}
```

### 9. action_priority_list ⭐ (Most Important!)
```javascript
[{
  priority_order: number,
  action: string,
  category: "Certification" | "Labeling" | "Documentation" | "Material" | "Packaging",
  estimated_time: string,
  estimated_cost_idr: string,
  blocking_export: boolean
}]
```

### 10. country_specific_notes
```javascript
string[] // Array of practical tips
```

---

## 🎨 UI Component Mapping

| Data Section | Recommended Component |
|--------------|----------------------|
| `action_priority_list` | Stepper / Checklist |
| `required_certifications` | Card Grid with Accordions |
| `import_documentation` | Interactive Checklist |
| `material_specific_regulations` | Accordion List |
| `labeling_requirements` | Info Cards with Examples |
| `packaging_requirements` | Status Cards |
| `tariff_and_duties` | Calculator Widget |
| `country_specific_notes` | Alert/Info Box |
| `product_classification` | Header Info |
| `prohibited_or_restricted` | Warning Banner |

---

## 💡 Priority Badges

```jsx
// Color mapping
const priorityColors = {
  critical: 'bg-red-500',    // Must have
  high: 'bg-orange-500',     // Strongly recommended
  medium: 'bg-yellow-500',   // Good to have
  low: 'bg-green-500'        // Optional
};

// Blocking indicator
{action.blocking_export && (
  <span className="text-red-600 font-bold">
    ⚠️ Required before export
  </span>
)}
```

---

## 🌐 Language Toggle

```jsx
const [language, setLanguage] = useState('id');

<select value={language} onChange={(e) => setLanguage(e.target.value)}>
  <option value="id">🇮🇩 Bahasa Indonesia</option>
  <option value="en">🇬🇧 English</option>
</select>
```

---

## ✅ Checklist for FE Implementation

### Phase 1: Core Display
- [ ] Fetch and display recommendations
- [ ] Language toggle (ID/EN)
- [ ] Action priority list (stepper)
- [ ] Loading and error states

### Phase 2: Interactive Elements
- [ ] Certification cards with expandable details
- [ ] Document checklist with checkboxes
- [ ] Material compliance accordion
- [ ] Labeling examples viewer

### Phase 3: Advanced Features
- [ ] Cost calculator/summary
- [ ] Timeline visualizer
- [ ] Tariff savings calculator
- [ ] Progress tracking
- [ ] PDF export

### Phase 4: Polish
- [ ] Responsive design
- [ ] Animations/transitions
- [ ] Print-friendly view
- [ ] Share functionality
- [ ] Help tooltips

---

## 🔍 Sample Data for Testing

```javascript
// Mock minimal response for UI development
const mockResponse = {
  analysis_id: 1,
  product_id: 1,
  product_name: "Tas Rotan Handmade",
  target_country: "United States",
  country_code: "US",
  readiness_score: 75,
  status_grade: "Warning",
  language: "id",
  regulation_recommendations: {
    action_priority_list: [
      {
        priority_order: 1,
        action: "Dapatkan Certificate of Origin",
        category: "Dokumentasi",
        estimated_time: "1 minggu",
        estimated_cost_idr: "100.000 - 500.000",
        blocking_export: true
      }
    ],
    required_certifications: [
      {
        certification_name: "Certificate of Origin (SKA)",
        regulatory_body: "KADIN Indonesia",
        why_applicable: "Diperlukan untuk GSP",
        estimated_cost_idr: "100.000 - 500.000",
        processing_time: "3-5 hari",
        how_to_obtain: "1. Siapkan invoice\n2. Ajukan ke KADIN",
        priority: "critical",
        applicable: true
      }
    ],
    // ... other sections
  }
};
```

---

## 🚨 Error Handling

```javascript
try {
  const response = await fetchRecommendations(productId, countryCode, language);
  setData(response.data);
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login
  } else if (error.response?.status === 403) {
    showError("You don't have permission to access this product");
  } else if (error.response?.status === 404) {
    showError("Product or country not found");
  } else {
    showError("Failed to load recommendations. Please try again.");
  }
}
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile: Stack everything */
@media (max-width: 640px) {
  .recommendations-grid { grid-template-columns: 1fr; }
}

/* Tablet: 2 columns */
@media (min-width: 641px) and (max-width: 1024px) {
  .recommendations-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop: 3 columns */
@media (min-width: 1025px) {
  .recommendations-grid { grid-template-columns: repeat(3, 1fr); }
}
```

---

## 🎯 Key UX Principles

1. **Progressive Disclosure**: Show summary first, expand for details
2. **Visual Priority**: Use colors/badges to indicate importance
3. **Cost Transparency**: Always show costs prominently
4. **Time Context**: Display processing times clearly
5. **Action-Oriented**: Focus on "what to do next"
6. **Language Preference**: Remember user's language choice
7. **Print-Friendly**: Offer downloadable/printable version
8. **Help Available**: Tooltips for technical terms

---

## 📞 Support Contacts

- **API Issues**: Backend team
- **Design Questions**: UX team  
- **Content/Copy**: Product team
- **Regulation Questions**: Compliance team

---

**Last Updated**: December 7, 2025  
**API Version**: v1  
**Status**: Ready for Frontend Integration ✅
