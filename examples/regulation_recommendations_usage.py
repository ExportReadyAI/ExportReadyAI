"""
Example Usage Script for Regulation Recommendations API

This script demonstrates how to use the regulation recommendations endpoint
both from the backend service directly and via API calls.
"""

# Example 1: Direct Service Usage (Backend)
# ==========================================

from apps.export_analysis.services import ComplianceAIService
from apps.export_analysis.models import Country
from apps.products.models import Product

def generate_recommendations_for_product(product_id: int, country_code: str, language: str = "id"):
    """
    Generate regulation recommendations for a product and target country.
    
    Args:
        product_id: Product ID
        country_code: ISO 2-letter country code
        language: "id" for Indonesian, "en" for English
    
    Returns:
        dict: Comprehensive regulation recommendations
    """
    # Get product and country
    product = Product.objects.get(id=product_id)
    country = Country.objects.get(country_code=country_code)
    
    # Initialize AI service
    ai_service = ComplianceAIService()
    
    # First, run compliance analysis
    analysis_result = ai_service.analyze_product_compliance(
        product=product,
        target_country_code=country_code
    )
    
    # Then generate detailed recommendations
    recommendations = ai_service.generate_regulation_recommendations(
        product=product,
        target_country=country,
        compliance_issues=analysis_result["compliance_issues"],
        language=language
    )
    
    return {
        "product_name": product.name_local,
        "target_country": country.country_name,
        "readiness_score": analysis_result["readiness_score"],
        "status_grade": analysis_result["status_grade"],
        **recommendations
    }


# Example 2: API Call from Frontend (JavaScript/TypeScript)
# ===========================================================

"""
// Using fetch API
async function getRegulationRecommendations(analysisId, language = 'id') {
  const response = await fetch(
    'https://api.exportready.ai/api/v1/export-analysis/regulation-recommendations/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        language: language
      })
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch recommendations');
  }
  
  const data = await response.json();
  return data.data;
}

// Using axios
import axios from 'axios';

async function getRecommendationsForProduct(productId, countryCode, language = 'en') {
  try {
    const response = await axios.post(
      '/api/v1/export-analysis/regulation-recommendations/',
      {
        product_id: productId,
        target_country_code: countryCode,
        language: language
      },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        }
      }
    );
    
    return response.data.data;
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    throw error;
  }
}

// React Hook Example
import { useState, useEffect } from 'react';

function useRegulationRecommendations(productId, countryCode, language = 'id') {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchRecommendations() {
      try {
        setLoading(true);
        const data = await getRecommendationsForProduct(productId, countryCode, language);
        setRecommendations(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (productId && countryCode) {
      fetchRecommendations();
    }
  }, [productId, countryCode, language]);

  return { recommendations, loading, error };
}

// Usage in Component
function RegulationRecommendationsPage({ productId, countryCode }) {
  const [language, setLanguage] = useState('id');
  const { recommendations, loading, error } = useRegulationRecommendations(
    productId,
    countryCode,
    language
  );

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!recommendations) return null;

  return (
    <div className="recommendations-container">
      {/* Language Toggle */}
      <LanguageToggle value={language} onChange={setLanguage} />
      
      {/* Product Info */}
      <ProductHeader
        name={recommendations.product_name}
        country={recommendations.target_country}
        score={recommendations.readiness_score}
        grade={recommendations.status_grade}
      />
      
      {/* Action Priority List */}
      <ActionPriorityList
        actions={recommendations.regulation_recommendations.action_priority_list}
      />
      
      {/* Required Certifications */}
      <CertificationCards
        certifications={recommendations.regulation_recommendations.required_certifications}
      />
      
      {/* Labeling Requirements */}
      <LabelingRequirements
        requirements={recommendations.regulation_recommendations.labeling_requirements}
      />
      
      {/* Import Documentation */}
      <DocumentChecklist
        documents={recommendations.regulation_recommendations.import_documentation}
      />
      
      {/* Tariff Information */}
      <TariffCalculator
        tariff={recommendations.regulation_recommendations.tariff_and_duties}
      />
      
      {/* Material Regulations */}
      <MaterialCompliance
        materials={recommendations.regulation_recommendations.material_specific_regulations}
      />
      
      {/* Country Notes */}
      <CountryNotes
        notes={recommendations.regulation_recommendations.country_specific_notes}
      />
    </div>
  );
}
"""


# Example 3: Python API Client
# ==============================

import requests
from typing import Optional, Dict, Any

class ExportReadyAPIClient:
    """Python client for ExportReady.AI API."""
    
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
    
    def get_regulation_recommendations(
        self,
        analysis_id: Optional[int] = None,
        product_id: Optional[int] = None,
        target_country_code: Optional[str] = None,
        language: str = "id"
    ) -> Dict[str, Any]:
        """
        Get regulation recommendations for export.
        
        Args:
            analysis_id: Existing analysis ID (optional)
            product_id: Product ID (required if analysis_id not provided)
            target_country_code: Country code (required if analysis_id not provided)
            language: "id" or "en"
        
        Returns:
            dict: Regulation recommendations
        
        Raises:
            ValueError: If neither analysis_id nor (product_id + country_code) provided
            requests.HTTPError: If API request fails
        """
        if not analysis_id and not (product_id and target_country_code):
            raise ValueError(
                "Either analysis_id or both product_id and target_country_code must be provided"
            )
        
        payload = {"language": language}
        
        if analysis_id:
            payload["analysis_id"] = analysis_id
        else:
            payload["product_id"] = product_id
            payload["target_country_code"] = target_country_code
        
        url = f"{self.base_url}/api/v1/export-analysis/regulation-recommendations/"
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()["data"]


# Example Usage
# =============

if __name__ == "__main__":
    # Initialize client
    client = ExportReadyAPIClient(
        base_url="https://api.exportready.ai",
        access_token="your_access_token_here"
    )
    
    # Example 1: Get recommendations from existing analysis
    recommendations = client.get_regulation_recommendations(
        analysis_id=123,
        language="id"
    )
    
    print(f"Product: {recommendations['product_name']}")
    print(f"Target: {recommendations['target_country']}")
    print(f"Score: {recommendations['readiness_score']}")
    print(f"\nTop 3 Actions:")
    
    for action in recommendations['regulation_recommendations']['action_priority_list'][:3]:
        print(f"  {action['priority_order']}. {action['action']}")
        print(f"     Time: {action['estimated_time']}, Cost: {action['estimated_cost_idr']}")
    
    # Example 2: Generate new recommendations
    recommendations = client.get_regulation_recommendations(
        product_id=456,
        target_country_code="US",
        language="en"
    )
    
    print(f"\n\nCertifications Required:")
    for cert in recommendations['regulation_recommendations']['required_certifications']:
        if cert['applicable']:
            print(f"  - {cert['certification_name']}")
            print(f"    Priority: {cert['priority']}")
            print(f"    Cost: {cert['estimated_cost_idr']}")
            print(f"    Time: {cert['processing_time']}")


# Example 4: Sample Response Structure
# =====================================

sample_response = {
    "success": True,
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
            "product_classification": {
                "detected_category": "Kerajinan Tangan - Tas Rotan",
                "hs_code_suggestion": "46021200",
                "hs_description": "Barang anyaman dari bahan nabati",
                "regulatory_category": "Produk Konsumen"
            },
            "required_certifications": [
                {
                    "certification_name": "Certificate of Origin (SKA)",
                    "regulatory_body": "KADIN Indonesia",
                    "why_applicable": "Diperlukan untuk GSP di AS",
                    "estimated_cost_idr": "100.000 - 500.000",
                    "processing_time": "3-5 hari kerja",
                    "how_to_obtain": "1. Siapkan invoice\n2. Ajukan ke KADIN\n3. Bayar biaya\n4. Terima SKA",
                    "priority": "critical",
                    "applicable": True,
                    "not_applicable_reason": ""
                }
            ],
            "material_specific_regulations": [
                {
                    "material": "Rotan",
                    "percentage": "80%",
                    "applicable_regulations": [
                        {
                            "regulation_name": "CITES",
                            "regulation_number": "CITES Appendix II/III",
                            "requirement": "Pastikan rotan legal",
                            "compliance_action": "Dapatkan dokumen dari pemasok",
                            "documentation_needed": "Surat Keterangan Sumber Rotan",
                            "risk_if_non_compliant": "Produk dapat ditahan"
                        }
                    ]
                }
            ],
            "labeling_requirements": [
                {
                    "requirement_name": "Country of Origin",
                    "regulation_reference": "19 CFR Part 134",
                    "specification": "Label 'Made in Indonesia'",
                    "language_requirement": "English",
                    "placement": "Visible on product",
                    "mandatory": True,
                    "example": "Made in Indonesia"
                }
            ],
            "packaging_requirements": [
                {
                    "requirement_name": "Eco-friendly",
                    "current_packaging": "Cardboard",
                    "compliance_status": "compliant",
                    "regulation_reference": "US EPA",
                    "action_needed": "None",
                    "notes": "Already compliant"
                }
            ],
            "import_documentation": [
                {
                    "document_name": "Commercial Invoice",
                    "required": True,
                    "issuing_authority": "Eksportir",
                    "purpose": "Customs clearance",
                    "must_include": ["Product desc", "HS Code", "FOB value"],
                    "estimated_cost_idr": "0",
                    "processing_time": "1 day"
                }
            ],
            "tariff_and_duties": {
                "hs_code": "46021200",
                "mfn_duty_rate": "4.0%",
                "preferential_schemes": [
                    {
                        "scheme_name": "GSP",
                        "preferential_rate": "0%",
                        "conditions": "35% value added in Indonesia",
                        "certificate_needed": "Form A"
                    }
                ]
            },
            "prohibited_or_restricted": {
                "is_prohibited": False,
                "is_restricted": False,
                "restrictions": [],
                "special_permits_needed": []
            },
            "action_priority_list": [
                {
                    "priority_order": 1,
                    "action": "Get Certificate of Origin",
                    "category": "Documentation",
                    "estimated_time": "1 week",
                    "estimated_cost_idr": "100.000 - 500.000",
                    "blocking_export": True
                },
                {
                    "priority_order": 2,
                    "action": "Add 'Made in Indonesia' label",
                    "category": "Labeling",
                    "estimated_time": "3 days",
                    "estimated_cost_idr": "500.000",
                    "blocking_export": True
                }
            ],
            "country_specific_notes": [
                "US is strict about labeling",
                "All documents must be in English",
                "GSP can save 4% tariff"
            ]
        }
    }
}
