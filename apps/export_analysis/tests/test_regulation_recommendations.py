"""
Tests for Regulation Recommendation API

Tests the comprehensive regulation recommendation system that provides
specific guidance on certifications, labeling, documentation, and compliance
for Indonesian UMKM exports.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.business_profiles.models import BusinessProfile
from apps.export_analysis.models import Country, CountryRegulation, ExportAnalysis, RuleCategory
from apps.products.models import Product, ProductEnrichment
from apps.users.models import User, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def umkm_user(db):
    """Create UMKM user with business profile."""
    user = User.objects.create_user(
        email="umkm@test.com",
        password="testpass123",
        full_name="UMKM User",
        role=UserRole.UMKM,
    )
    BusinessProfile.objects.create(
        user=user,
        business_name="Test Business",
        business_type="Handicraft",
        address="Jakarta",
    )
    return user


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        full_name="Admin User",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def country_us(db):
    """Create US country with regulations."""
    country = Country.objects.create(
        country_code="US",
        country_name="United States",
        region="North America",
    )
    
    # Add some regulations
    CountryRegulation.objects.create(
        country=country,
        rule_category=RuleCategory.INGREDIENT,
        forbidden_keywords="Lead, Mercury, Asbestos",
        description_rule="US Consumer Product Safety Commission regulations",
    )
    
    CountryRegulation.objects.create(
        country=country,
        rule_category=RuleCategory.LABELING,
        required_specs="Product Name, Origin, Material Composition, Safety Warnings",
        description_rule="19 CFR Part 134 - Country of Origin Marking",
    )
    
    CountryRegulation.objects.create(
        country=country,
        rule_category=RuleCategory.PHYSICAL,
        required_specs="ISPM-15 for wood packaging",
        description_rule="USDA APHIS packaging requirements",
    )
    
    return country


@pytest.fixture
def product_with_enrichment(db, umkm_user):
    """Create product with enrichment."""
    product = Product.objects.create(
        business=umkm_user.business_profile,
        name_local="Tas Rotan Handmade",
        category_id=1,
        description_local="Tas rotan berkualitas tinggi dengan desain modern",
        material_composition="Rotan 80%, Kulit Sintetis 15%, Kain Katun 5%",
        production_technique="Handwoven",
        finishing_type="Natural Varnish",
        quality_specs={"durability": "High", "water_resistant": "Yes"},
        durability_claim="Tahan hingga 5 tahun dengan perawatan normal",
        packaging_type="Cardboard Box with Bubble Wrap",
        dimensions_l_w_h={"length": 30, "width": 20, "height": 25},
        weight_net=0.5,
        weight_gross=0.7,
    )
    
    ProductEnrichment.objects.create(
        product=product,
        hs_code_recommendation="46021200",
        sku_generated="HAN-RAT-001",
        name_english_b2b="Handmade Rattan Handbag",
        description_english_b2b="High-quality handwoven rattan bag with modern design",
    )
    
    return product


@pytest.fixture
def analysis_with_issues(db, product_with_enrichment, country_us):
    """Create export analysis with compliance issues."""
    return ExportAnalysis.objects.create(
        product=product_with_enrichment,
        target_country=country_us,
        readiness_score=75,
        status_grade="Warning",
        compliance_issues=[
            {
                "type": "specification_missing",
                "rule_key": "Safety Warning",
                "your_value": "not provided",
                "required_value": "must include safety warnings",
                "description": "US requires safety warnings on consumer products",
                "severity": "major"
            },
            {
                "type": "packaging_requirement",
                "rule_key": "ISPM-15",
                "your_value": "cardboard packaging",
                "required_value": "wood packaging must be ISPM-15 certified",
                "description": "If using wood packaging, ISPM-15 certification required",
                "severity": "minor"
            }
        ],
        recommendations="1. Add safety warnings to product labeling\n2. Verify packaging compliance",
    )


@pytest.mark.django_db
class TestRegulationRecommendationAPI:
    """Test regulation recommendation endpoint."""

    def test_generate_recommendations_from_analysis_id_indonesian(
        self, api_client, umkm_user, analysis_with_issues
    ):
        """Test generating recommendations from existing analysis in Indonesian."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("regulation-recommendations")
        
        with patch("apps.export_analysis.services.ComplianceAIService._call_ai") as mock_ai:
            # Mock AI response
            mock_response = {
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
                            "regulatory_body": "Kamar Dagang dan Industri (KADIN) Indonesia",
                            "why_applicable": "Diperlukan untuk mendapatkan preferensi tarif GSP di AS",
                            "estimated_cost_idr": "100.000 - 500.000",
                            "processing_time": "3-5 hari kerja",
                            "how_to_obtain": "1. Siapkan invoice dan packing list\n2. Ajukan ke KADIN setempat\n3. Bayar biaya administrasi\n4. Dapatkan SKA Form A",
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
                                    "regulation_name": "CITES (Convention on International Trade in Endangered Species)",
                                    "regulation_number": "CITES Appendix II/III",
                                    "requirement": "Pastikan rotan bukan dari spesies dilindungi",
                                    "compliance_action": "Dapatkan dokumen dari pemasok yang menyatakan rotan berasal dari sumber legal",
                                    "documentation_needed": "Surat Keterangan Sumber Rotan dari Dinas Kehutanan",
                                    "risk_if_non_compliant": "Produk dapat ditahan atau ditolak di bea cukai AS"
                                }
                            ]
                        }
                    ],
                    "labeling_requirements": [
                        {
                            "requirement_name": "Country of Origin Marking",
                            "regulation_reference": "19 CFR Part 134",
                            "specification": "Label harus mencantumkan 'Made in Indonesia' dengan jelas dan permanen",
                            "language_requirement": "Bahasa Inggris",
                            "placement": "Pada produk atau kemasan yang mudah terlihat",
                            "mandatory": True,
                            "example": "Made in Indonesia | Handcrafted Rattan"
                        }
                    ],
                    "packaging_requirements": [
                        {
                            "requirement_name": "Kemasan Ramah Lingkungan",
                            "current_packaging": "Kardus dengan bubble wrap",
                            "compliance_status": "compliant",
                            "regulation_reference": "US EPA Guidelines",
                            "action_needed": "Sudah sesuai, tidak ada tindakan diperlukan",
                            "notes": "Kardus dapat didaur ulang, bubble wrap sebaiknya diganti dengan alternatif ramah lingkungan"
                        }
                    ],
                    "import_documentation": [
                        {
                            "document_name": "Commercial Invoice",
                            "required": True,
                            "issuing_authority": "Eksportir (Anda)",
                            "purpose": "Dokumen dasar untuk bea cukai",
                            "must_include": ["Deskripsi produk", "Kode HS", "Nilai FOB", "Origin Indonesia"],
                            "estimated_cost_idr": "0 (buat sendiri)",
                            "processing_time": "1 hari"
                        },
                        {
                            "document_name": "Packing List",
                            "required": True,
                            "issuing_authority": "Eksportir (Anda)",
                            "purpose": "Detail isi kemasan untuk pemeriksaan",
                            "must_include": ["Jumlah barang", "Berat", "Dimensi kemasan"],
                            "estimated_cost_idr": "0 (buat sendiri)",
                            "processing_time": "1 hari"
                        },
                        {
                            "document_name": "Certificate of Origin (Form A)",
                            "required": True,
                            "issuing_authority": "KADIN Indonesia",
                            "purpose": "Mendapatkan preferensi tarif GSP",
                            "must_include": ["Deskripsi barang", "Kode HS", "Kriteria origin"],
                            "estimated_cost_idr": "100.000 - 500.000",
                            "processing_time": "3-5 hari kerja"
                        }
                    ],
                    "tariff_and_duties": {
                        "hs_code": "46021200",
                        "mfn_duty_rate": "4.0%",
                        "preferential_schemes": [
                            {
                                "scheme_name": "Generalized System of Preferences (GSP)",
                                "preferential_rate": "0% (duty-free)",
                                "conditions": "Produk harus memenuhi kriteria origin Indonesia (minimal 35% value added)",
                                "certificate_needed": "Certificate of Origin Form A"
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
                            "action": "Dapatkan Certificate of Origin (Form A) dari KADIN",
                            "category": "Dokumentasi",
                            "estimated_time": "1 minggu",
                            "estimated_cost_idr": "100.000 - 500.000",
                            "blocking_export": True
                        },
                        {
                            "priority_order": 2,
                            "action": "Tambahkan label 'Made in Indonesia' pada produk",
                            "category": "Labeling",
                            "estimated_time": "3 hari",
                            "estimated_cost_idr": "500.000 (cetak label)",
                            "blocking_export": True
                        },
                        {
                            "priority_order": 3,
                            "action": "Verifikasi sumber rotan legal dengan dokumen dari pemasok",
                            "category": "Material",
                            "estimated_time": "1 minggu",
                            "estimated_cost_idr": "0",
                            "blocking_export": False
                        }
                    ],
                    "country_specific_notes": [
                        "Amerika Serikat sangat ketat dalam hal labeling dan dokumentasi",
                        "Pastikan semua dokumen dalam bahasa Inggris",
                        "GSP dapat menghemat biaya tarif hingga 4% dari nilai barang",
                        "Pertimbangkan bekerja dengan freight forwarder berpengalaman untuk ekspor ke AS"
                    ]
                }
            }
            
            mock_ai.return_value = json.dumps(mock_response)
            
            response = api_client.post(
                url,
                {"analysis_id": analysis_with_issues.id, "language": "id"},
                format="json"
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "regulation_recommendations" in data["data"]
        assert data["data"]["language"] == "id"
        
        regs = data["data"]["regulation_recommendations"]
        assert "product_classification" in regs
        assert "required_certifications" in regs
        assert len(regs["required_certifications"]) > 0
        assert "action_priority_list" in regs

    def test_generate_recommendations_from_product_and_country_english(
        self, api_client, umkm_user, product_with_enrichment, country_us
    ):
        """Test generating recommendations from product + country in English."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("regulation-recommendations")
        
        with patch("apps.export_analysis.services.ComplianceAIService._call_ai") as mock_ai:
            # Mock AI response in English
            mock_response = {
                "regulation_recommendations": {
                    "product_classification": {
                        "detected_category": "Handicraft - Rattan Bag",
                        "hs_code_suggestion": "46021200",
                        "hs_description": "Articles of vegetable plaiting materials",
                        "regulatory_category": "Consumer Product"
                    },
                    "required_certifications": [
                        {
                            "certification_name": "Certificate of Origin (COO)",
                            "regulatory_body": "Indonesian Chamber of Commerce and Industry (KADIN)",
                            "why_applicable": "Required for GSP tariff preference in US",
                            "estimated_cost_idr": "100,000 - 500,000",
                            "processing_time": "3-5 business days",
                            "how_to_obtain": "1. Prepare invoice and packing list\n2. Submit to local KADIN office\n3. Pay administrative fee\n4. Receive COO Form A",
                            "priority": "critical",
                            "applicable": True,
                            "not_applicable_reason": ""
                        }
                    ],
                    "material_specific_regulations": [],
                    "labeling_requirements": [
                        {
                            "requirement_name": "Country of Origin Marking",
                            "regulation_reference": "19 CFR Part 134",
                            "specification": "Must clearly display 'Made in Indonesia' permanently",
                            "language_requirement": "English",
                            "placement": "Visible on product or packaging",
                            "mandatory": True,
                            "example": "Made in Indonesia | Handcrafted Rattan"
                        }
                    ],
                    "packaging_requirements": [],
                    "import_documentation": [],
                    "tariff_and_duties": {
                        "hs_code": "46021200",
                        "mfn_duty_rate": "4.0%",
                        "preferential_schemes": []
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
                            "action": "Obtain Certificate of Origin (Form A) from KADIN",
                            "category": "Documentation",
                            "estimated_time": "1 week",
                            "estimated_cost_idr": "100,000 - 500,000",
                            "blocking_export": True
                        }
                    ],
                    "country_specific_notes": [
                        "United States is strict about labeling and documentation"
                    ]
                }
            }
            
            mock_ai.return_value = json.dumps(mock_response)
            
            response = api_client.post(
                url,
                {
                    "product_id": product_with_enrichment.id,
                    "target_country_code": "US",
                    "language": "en"
                },
                format="json"
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["language"] == "en"
        assert "regulation_recommendations" in data["data"]

    def test_missing_parameters(self, api_client, umkm_user):
        """Test validation when neither analysis_id nor product+country provided."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("regulation-recommendations")
        
        response = api_client.post(url, {"language": "id"}, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized_access(self, api_client):
        """Test that unauthenticated users cannot access the endpoint."""
        url = reverse("regulation-recommendations")
        
        response = api_client.post(
            url,
            {"analysis_id": 1, "language": "id"},
            format="json"
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_wrong_user_cannot_access_other_analysis(
        self, api_client, admin_user, analysis_with_issues
    ):
        """Test that users cannot access analyses that don't belong to them."""
        # Create another UMKM user
        other_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            full_name="Other User",
            role=UserRole.UMKM,
        )
        BusinessProfile.objects.create(
            user=other_user,
            business_name="Other Business",
            business_type="Textile",
            address="Bandung",
        )
        
        api_client.force_authenticate(user=other_user)
        url = reverse("regulation-recommendations")
        
        response = api_client.post(
            url,
            {"analysis_id": analysis_with_issues.id, "language": "id"},
            format="json"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_default_language_is_indonesian(
        self, api_client, umkm_user, analysis_with_issues
    ):
        """Test that default language is Indonesian when not specified."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("regulation-recommendations")
        
        with patch("apps.export_analysis.services.ComplianceAIService._call_ai") as mock_ai:
            mock_response = {"regulation_recommendations": {}}
            mock_ai.return_value = json.dumps(mock_response)
            
            response = api_client.post(
                url,
                {"analysis_id": analysis_with_issues.id},
                format="json"
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["language"] == "id"

    def test_fallback_recommendations_on_ai_failure(
        self, api_client, umkm_user, analysis_with_issues
    ):
        """Test that fallback recommendations are provided if AI fails."""
        api_client.force_authenticate(user=umkm_user)
        url = reverse("regulation-recommendations")
        
        with patch("apps.export_analysis.services.ComplianceAIService._call_ai") as mock_ai:
            # Simulate AI failure
            mock_ai.side_effect = Exception("AI service unavailable")
            
            response = api_client.post(
                url,
                {"analysis_id": analysis_with_issues.id, "language": "en"},
                format="json"
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "regulation_recommendations" in data["data"]
        # Fallback should still provide basic structure
        regs = data["data"]["regulation_recommendations"]
        assert "product_classification" in regs
        assert "action_priority_list" in regs


@pytest.mark.django_db
class TestRegulationRecommendationService:
    """Test the regulation recommendation service methods."""

    def test_generate_regulation_recommendations_structure(
        self, product_with_enrichment, country_us
    ):
        """Test that generated recommendations have correct structure."""
        from apps.export_analysis.services import ComplianceAIService
        
        service = ComplianceAIService()
        compliance_issues = [
            {
                "type": "specification_missing",
                "severity": "major",
                "description": "Missing safety warning"
            }
        ]
        
        with patch.object(service, "_call_ai") as mock_ai:
            mock_response = {
                "regulation_recommendations": {
                    "product_classification": {},
                    "required_certifications": [],
                    "material_specific_regulations": [],
                    "labeling_requirements": [],
                    "packaging_requirements": [],
                    "import_documentation": [],
                    "tariff_and_duties": {},
                    "prohibited_or_restricted": {},
                    "action_priority_list": [],
                    "country_specific_notes": []
                }
            }
            mock_ai.return_value = json.dumps(mock_response)
            
            result = service.generate_regulation_recommendations(
                product=product_with_enrichment,
                target_country=country_us,
                compliance_issues=compliance_issues,
                language="id"
            )
        
        assert "regulation_recommendations" in result
        regs = result["regulation_recommendations"]
        assert "product_classification" in regs
        assert "required_certifications" in regs
        assert "action_priority_list" in regs

    def test_fallback_recommendations_structure(
        self, product_with_enrichment, country_us
    ):
        """Test fallback recommendations have required structure."""
        from apps.export_analysis.services import ComplianceAIService
        
        service = ComplianceAIService()
        result = service._generate_fallback_recommendations(
            product=product_with_enrichment,
            target_country=country_us,
            compliance_issues=[],
            language="en"
        )
        
        assert "regulation_recommendations" in result
        regs = result["regulation_recommendations"]
        
        # Check all required keys
        assert "product_classification" in regs
        assert "required_certifications" in regs
        assert "material_specific_regulations" in regs
        assert "labeling_requirements" in regs
        assert "packaging_requirements" in regs
        assert "import_documentation" in regs
        assert "tariff_and_duties" in regs
        assert "prohibited_or_restricted" in regs
        assert "action_priority_list" in regs
        assert "country_specific_notes" in regs
        
        # Check some content
        assert len(regs["required_certifications"]) > 0
        assert len(regs["action_priority_list"]) > 0
