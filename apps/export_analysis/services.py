"""
AI Compliance Services for ExportReady.AI Module 3

Implements:
# PBI-BE-M3-04: Service: AI Compliance Checker - Ingredient
# PBI-BE-M3-05: Service: AI Compliance Checker - Specification
# PBI-BE-M3-06: Service: AI Compliance Checker - Packaging
# PBI-BE-M3-07: Service: Calculate Readiness Score
# PBI-BE-M3-08: Service: Generate Recommendations

All acceptance criteria for these PBIs are implemented in this module.
"""

import json
import logging
import re
from typing import Optional

from django.conf import settings
from openai import OpenAI

from .models import Country, CountryRegulation, ExportAnalysis, RuleCategory, StatusGrade

logger = logging.getLogger(__name__)


class ComplianceAIService:
    """
    AI Service for checking product compliance against country regulations.
    Uses Kolosal AI (OpenAI-compatible SDK).
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.KOLOSAL_API_KEY,
            base_url=settings.KOLOSAL_BASE_URL,
        )
        self.model = settings.KOLOSAL_MODEL

    def _call_ai(self, prompt: str, system_prompt: str = None) -> str:
        """
        Make a call to Kolosal AI API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            The AI response text
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Kolosal AI API error: {e}")
            raise

    def check_ingredient_compliance(
        self,
        material_composition: str,
        target_country_code: str,
    ) -> list:
        """
        # PBI-BE-M3-04: Service: AI Compliance Checker - Ingredient
        #
        # Acceptance Criteria:
        # [DONE] Input: material_composition (Product), target_country_code
        # [DONE] Query: CountryRegulation WHERE country_code = target AND rule_category = 'Ingredient'
        # [DONE] Logic: Check if any banned ingredient exists in material
        # [DONE] LLM Assist: "Apakah material '{material}' mengandung bahan terlarang: {banned_list}?"
        # [DONE] Output: Array of issues dengan severity (critical/major/minor)
        # [DONE] Issue format: {type, rule_key, your_value, required_value, description, severity}

        Args:
            material_composition: Product material composition
            target_country_code: Target country ISO code

        Returns:
            List of compliance issues
        """
        issues = []

        # Query country regulations for ingredients
        regulations = CountryRegulation.objects.filter(
            country_id=target_country_code,
            rule_category=RuleCategory.INGREDIENT,
        )

        if not regulations.exists():
            return issues

        # Collect all forbidden keywords
        forbidden_list = []
        for reg in regulations:
            if reg.forbidden_keywords:
                keywords = [k.strip() for k in reg.forbidden_keywords.split(",") if k.strip()]
                forbidden_list.extend(keywords)

        if not forbidden_list:
            return issues

        # Use AI to check for banned ingredients
        system_prompt = """Kamu adalah ahli regulasi ekspor Indonesia.
Tugasmu adalah menganalisis apakah komposisi material produk mengandung bahan yang dilarang untuk negara tujuan ekspor.

ATURAN:
- Analisis dengan teliti setiap bahan dalam material
- Jika ditemukan bahan terlarang, berikan severity level:
  - critical: Bahan berbahaya atau sangat dilarang
  - major: Bahan yang memerlukan sertifikasi khusus
  - minor: Bahan yang perlu perhatian tapi tidak kritis
- Output HARUS dalam format JSON array
- Jika tidak ada masalah, kembalikan array kosong: []"""

        prompt = f"""Analisis apakah material produk berikut mengandung bahan terlarang:

Material Produk: {material_composition}
Daftar Bahan Terlarang: {', '.join(forbidden_list)}

Berikan output dalam format JSON array:
[
  {{
    "type": "ingredient_ban",
    "rule_key": "nama_bahan_terlarang",
    "your_value": "bahan_yang_ditemukan",
    "required_value": "tidak boleh mengandung bahan ini",
    "description": "penjelasan singkat",
    "severity": "critical/major/minor"
  }}
]

Jika tidak ada masalah, kembalikan: []"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                parsed_issues = json.loads(json_match.group())
                if isinstance(parsed_issues, list):
                    issues.extend(parsed_issues)
        except Exception as e:
            logger.error(f"Error checking ingredient compliance: {e}")

        return issues

    def check_specification_compliance(
        self,
        quality_specs: dict,
        target_country_code: str,
    ) -> list:
        """
        # PBI-BE-M3-05: Service: AI Compliance Checker - Specification
        #
        # Acceptance Criteria:
        # [DONE] Input: quality_specs (Product), target_country_code
        # [DONE] Query: CountryRegulation WHERE rule_category = 'Labeling'
        # [DONE] Logic: Compare each spec dengan country standard
        # [DONE] Contoh: product.tolerance = "5mm", country.max_tolerance = "1mm" → issue
        # [DONE] LLM Assist untuk interpretasi jika format berbeda
        # [DONE] Output: Array of issues

        Args:
            quality_specs: Product quality specifications (JSON/dict)
            target_country_code: Target country ISO code

        Returns:
            List of compliance issues
        """
        issues = []

        # Query country regulations for labeling/specs
        regulations = CountryRegulation.objects.filter(
            country_id=target_country_code,
            rule_category=RuleCategory.LABELING,
        )

        if not regulations.exists():
            return issues

        # Collect all required specs
        required_specs = []
        for reg in regulations:
            if reg.required_specs:
                specs = [s.strip() for s in reg.required_specs.split(",") if s.strip()]
                required_specs.extend(specs)

        if not required_specs:
            return issues

        # Use AI to check specifications
        system_prompt = """Kamu adalah ahli quality control untuk ekspor.
Tugasmu adalah menganalisis apakah spesifikasi produk memenuhi persyaratan negara tujuan.

ATURAN:
- Periksa apakah semua spesifikasi yang diperlukan sudah ada
- Periksa apakah nilai spesifikasi memenuhi standar
- Severity levels:
  - critical: Spesifikasi wajib yang tidak ada atau tidak memenuhi standar
  - major: Spesifikasi penting yang perlu perbaikan
  - minor: Spesifikasi opsional yang disarankan
- Output HARUS dalam format JSON array
- Jika tidak ada masalah, kembalikan array kosong: []"""

        quality_specs_str = json.dumps(quality_specs) if isinstance(quality_specs, dict) else str(quality_specs)

        prompt = f"""Analisis apakah spesifikasi produk memenuhi persyaratan negara tujuan:

Spesifikasi Produk: {quality_specs_str}
Persyaratan Wajib: {', '.join(required_specs)}

Berikan output dalam format JSON array:
[
  {{
    "type": "specification_missing",
    "rule_key": "nama_spesifikasi",
    "your_value": "nilai_produk_atau_tidak_ada",
    "required_value": "nilai_yang_diperlukan",
    "description": "penjelasan singkat",
    "severity": "critical/major/minor"
  }}
]

Jika tidak ada masalah, kembalikan: []"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                parsed_issues = json.loads(json_match.group())
                if isinstance(parsed_issues, list):
                    issues.extend(parsed_issues)
        except Exception as e:
            logger.error(f"Error checking specification compliance: {e}")

        return issues

    def check_packaging_compliance(
        self,
        packaging_type: str,
        target_country_code: str,
    ) -> list:
        """
        # PBI-BE-M3-06: Service: AI Compliance Checker - Packaging
        #
        # Acceptance Criteria:
        # [DONE] Input: packaging_type (Product), target_country_code
        # [DONE] Query: CountryRegulation WHERE rule_category = 'Physical'
        # [DONE] Logic: Check packaging requirements
        # [DONE] Contoh: packaging = "Kayu" + country = "AU" → require ISPM-15
        # [DONE] Output: Array of issues dengan required certifications

        Args:
            packaging_type: Product packaging type
            target_country_code: Target country ISO code

        Returns:
            List of compliance issues
        """
        issues = []

        # Query country regulations for physical/packaging
        regulations = CountryRegulation.objects.filter(
            country_id=target_country_code,
            rule_category=RuleCategory.PHYSICAL,
        )

        if not regulations.exists():
            return issues

        # Collect packaging requirements
        packaging_requirements = []
        for reg in regulations:
            if reg.required_specs:
                reqs = [r.strip() for r in reg.required_specs.split(",") if r.strip()]
                packaging_requirements.extend(reqs)
            if reg.description_rule:
                packaging_requirements.append(reg.description_rule)

        # Use AI to check packaging compliance
        system_prompt = """Kamu adalah ahli regulasi packaging ekspor.
Tugasmu adalah menganalisis apakah jenis kemasan produk memenuhi persyaratan negara tujuan.

ATURAN:
- Periksa sertifikasi yang diperlukan (misal: ISPM-15 untuk kayu)
- Periksa standar kemasan untuk food safety jika relevan
- Severity levels:
  - critical: Kemasan tidak memenuhi standar dasar
  - major: Memerlukan sertifikasi tambahan
  - minor: Rekomendasi perbaikan kemasan
- Output HARUS dalam format JSON array
- Jika tidak ada masalah, kembalikan array kosong: []"""

        prompt = f"""Analisis apakah kemasan produk memenuhi persyaratan negara tujuan:

Jenis Kemasan: {packaging_type}
Negara Tujuan: {target_country_code}
Persyaratan Kemasan: {', '.join(packaging_requirements) if packaging_requirements else 'Standar umum'}

Berikan output dalam format JSON array:
[
  {{
    "type": "packaging_requirement",
    "rule_key": "nama_persyaratan",
    "your_value": "kondisi_kemasan_saat_ini",
    "required_value": "persyaratan_yang_harus_dipenuhi",
    "description": "penjelasan dan sertifikasi yang diperlukan",
    "severity": "critical/major/minor"
  }}
]

Jika tidak ada masalah, kembalikan: []"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                parsed_issues = json.loads(json_match.group())
                if isinstance(parsed_issues, list):
                    issues.extend(parsed_issues)
        except Exception as e:
            logger.error(f"Error checking packaging compliance: {e}")

        return issues

    def calculate_readiness_score(self, compliance_issues: list) -> tuple:
        """
        # PBI-BE-M3-07: Service: Calculate Readiness Score
        #
        # Acceptance Criteria:
        # [DONE] Input: Array of all compliance issues
        # [DONE] Base score = 100
        # [DONE] Deduction: critical = -20, major = -10, minor = -5
        # [DONE] Minimum score = 0
        # [DONE] Output: readiness_score (integer 0-100)

        Args:
            compliance_issues: List of all compliance issues

        Returns:
            Tuple of (readiness_score, status_grade)
        """
        base_score = 100
        deductions = {
            "critical": 20,
            "major": 10,
            "minor": 5,
        }

        total_deduction = 0
        for issue in compliance_issues:
            severity = issue.get("severity", "minor").lower()
            total_deduction += deductions.get(severity, 5)

        readiness_score = max(0, base_score - total_deduction)

        # Determine status grade
        if readiness_score >= 80:
            status_grade = StatusGrade.READY
        elif readiness_score >= 50:
            status_grade = StatusGrade.WARNING
        else:
            status_grade = StatusGrade.CRITICAL

        return readiness_score, status_grade

    def generate_recommendations(self, compliance_issues: list) -> str:
        """
        # PBI-BE-M3-08: Service: Generate Recommendations
        #
        # Acceptance Criteria:
        # [DONE] Input: Array of compliance issues
        # [DONE] LLM Prompt: "Berdasarkan issues berikut, berikan rekomendasi perbaikan yang actionable: {issues}"
        # [DONE] Format: numbered list, bahasa Indonesia
        # [DONE] Output: recommendations (text)

        Args:
            compliance_issues: List of compliance issues

        Returns:
            Recommendations text
        """
        if not compliance_issues:
            return "Produk Anda sudah memenuhi semua persyaratan ekspor untuk negara tujuan. Pastikan untuk menjaga kualitas dan dokumentasi tetap up-to-date."

        system_prompt = """Kamu adalah konsultan ekspor berpengalaman untuk UMKM Indonesia.
Tugasmu adalah memberikan rekomendasi perbaikan yang praktis dan actionable.

ATURAN:
- Gunakan bahasa Indonesia yang mudah dipahami
- Berikan rekomendasi dalam format numbered list
- Fokus pada solusi praktis, bukan teori
- Sertakan langkah-langkah konkret yang bisa dilakukan
- Prioritaskan berdasarkan severity (critical dulu)
- Maksimal 5-7 rekomendasi utama"""

        issues_str = json.dumps(compliance_issues, indent=2, ensure_ascii=False)

        prompt = f"""Berdasarkan temuan compliance berikut, berikan rekomendasi perbaikan yang actionable:

{issues_str}

Berikan rekomendasi dalam format numbered list:"""

        try:
            response = self._call_ai(prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback recommendations
            recommendations = ["1. Tinjau kembali komposisi material produk Anda"]
            for i, issue in enumerate(compliance_issues[:5], 2):
                recommendations.append(f"{i}. Perbaiki: {issue.get('description', issue.get('rule_key', 'masalah yang ditemukan'))}")
            return "\n".join(recommendations)

    def analyze_product_compliance(
        self,
        product,
        target_country_code: str,
    ) -> dict:
        """
        Full compliance analysis - combines all AI compliance checkers.

        Args:
            product: Product model instance
            target_country_code: Target country ISO code

        Returns:
            Dictionary with analysis results
        """
        all_issues = []

        # Check ingredient compliance
        ingredient_issues = self.check_ingredient_compliance(
            material_composition=product.material_composition or "",
            target_country_code=target_country_code,
        )
        all_issues.extend(ingredient_issues)

        # Check specification compliance
        spec_issues = self.check_specification_compliance(
            quality_specs=product.quality_specs or {},
            target_country_code=target_country_code,
        )
        all_issues.extend(spec_issues)

        # Check packaging compliance
        packaging_issues = self.check_packaging_compliance(
            packaging_type=product.packaging_type or "",
            target_country_code=target_country_code,
        )
        all_issues.extend(packaging_issues)

        # Calculate readiness score and status grade
        readiness_score, status_grade = self.calculate_readiness_score(all_issues)

        # Generate recommendations
        recommendations = self.generate_recommendations(all_issues)

        return {
            "compliance_issues": all_issues,
            "readiness_score": readiness_score,
            "status_grade": status_grade,
            "recommendations": recommendations,
        }

    def generate_regulation_recommendations(
        self,
        product,
        target_country: Country,
        compliance_issues: list,
        language: str = "id",
    ) -> dict:
        """
        Generate comprehensive regulation recommendations for export.
        Provides SPECIFIC guidance on certifications, labeling, documentation, etc.

        Args:
            product: Product model instance
            target_country: Country model instance
            compliance_issues: List of detected compliance issues
            language: Output language ('id' for Indonesian, 'en' for English)

        Returns:
            Dictionary with detailed regulation recommendations
        """
        # Get product enrichment data if available
        hs_code = ""
        if hasattr(product, "enrichment") and product.enrichment:
            hs_code = product.enrichment.hs_code_recommendation or ""

        # Prepare compliance issues summary
        compliance_issues_json = json.dumps(compliance_issues, indent=2, ensure_ascii=False)

        # Define bilingual system prompt
        if language == "en":
            system_prompt = """You are an expert international trade compliance advisor specializing in Indonesian UMKM exports.
Your task is to provide SPECIFIC, ACTIONABLE regulation recommendations for exporting Indonesian products to target countries.

CRITICAL REQUIREMENTS:
- Be SPECIFIC: cite actual regulation numbers (19 CFR, EU Regulation numbers, etc.)
- Provide REAL cost estimates in IDR (Indonesian Rupiah)
- Give ACTIONABLE steps, not generic advice
- Tailor recommendations to the EXACT product and materials provided
- Include processing times, regulatory bodies, and step-by-step guidance
- Output MUST be valid JSON matching the exact schema provided"""
        else:
            system_prompt = """Kamu adalah ahli kepatuhan perdagangan internasional yang berspesialisasi dalam ekspor UMKM Indonesia.
Tugasmu adalah memberikan rekomendasi regulasi yang SPESIFIK dan DAPAT DITINDAKLANJUTI untuk ekspor produk Indonesia ke negara tujuan.

PERSYARATAN KRITIS:
- Berikan SPESIFIK: sebutkan nomor regulasi aktual (19 CFR, nomor Regulasi EU, dll.)
- Berikan estimasi biaya NYATA dalam IDR (Rupiah Indonesia)
- Berikan langkah-langkah yang DAPAT DITINDAKLANJUTI, bukan saran umum
- Sesuaikan rekomendasi dengan produk dan material yang TEPAT
- Sertakan waktu pemrosesan, badan regulasi, dan panduan langkah demi langkah
- Output HARUS berupa JSON valid yang sesuai dengan skema yang diberikan"""

        # Prepare user prompt with bilingual template
        if language == "en":
            prompt = f"""Analyze the following product and provide SPECIFIC regulation recommendations for export to the target country.

## PRODUCT DATA
- Product Name: {product.name_local}
- Category: {product.category_id}
- Material Composition: {product.material_composition or 'Not specified'}
- Packaging Type: {product.packaging_type or 'Not specified'}
- HS Code: {hs_code or 'Not yet determined'}
- Description: {product.description_local[:200]}...
- Weight: {product.weight_net} kg (net), {product.weight_gross} kg (gross)

## TARGET COUNTRY
- Country: {target_country.country_name} ({target_country.country_code})
- Region: {target_country.region}

## EXISTING COMPLIANCE ISSUES DETECTED
{compliance_issues_json}

## YOUR TASK
Provide SPECIFIC regulation recommendations in valid JSON format:

{{
    "regulation_recommendations": {{
        "product_classification": {{
            "detected_category": "string - detected product category",
            "hs_code_suggestion": "string - 6-8 digit HS code",
            "hs_description": "string - HS code description",
            "regulatory_category": "string - regulatory category (Consumer Product/Food/Cosmetic/etc)"
        }},
        "required_certifications": [
            {{
                "certification_name": "string - exact certification name",
                "regulatory_body": "string - regulatory authority name",
                "why_applicable": "string - why this certification is needed for this product",
                "estimated_cost_idr": "string - cost range in Rupiah (e.g., '5,000,000 - 10,000,000')",
                "processing_time": "string - estimated processing time (e.g., '2-3 months')",
                "how_to_obtain": "string - step-by-step guidance to obtain certification",
                "priority": "critical/high/medium/low",
                "applicable": true/false,
                "not_applicable_reason": "string - if not applicable, explain why"
            }}
        ],
        "material_specific_regulations": [
            {{
                "material": "string - material name from composition",
                "percentage": "string - percentage in product",
                "applicable_regulations": [
                    {{
                        "regulation_name": "string - regulation name",
                        "regulation_number": "string - regulation number if available",
                        "requirement": "string - what is required",
                        "compliance_action": "string - action needed to comply",
                        "documentation_needed": "string - required documentation",
                        "risk_if_non_compliant": "string - risk if non-compliant"
                    }}
                ]
            }}
        ],
        "labeling_requirements": [
            {{
                "requirement_name": "string - requirement name",
                "regulation_reference": "string - regulation reference",
                "specification": "string - detailed specification",
                "language_requirement": "string - required language(s)",
                "placement": "string - label placement",
                "mandatory": true/false,
                "example": "string - example label format"
            }}
        ],
        "packaging_requirements": [
            {{
                "requirement_name": "string - requirement name",
                "current_packaging": "string - current packaging used",
                "compliance_status": "compliant/non_compliant/needs_verification",
                "regulation_reference": "string - regulation reference",
                "action_needed": "string - action needed",
                "notes": "string - additional notes"
            }}
        ],
        "import_documentation": [
            {{
                "document_name": "string - document name",
                "required": true/false,
                "issuing_authority": "string - issuing authority in Indonesia",
                "purpose": "string - document purpose",
                "must_include": ["string - required information"],
                "estimated_cost_idr": "string - cost estimate",
                "processing_time": "string - processing time"
            }}
        ],
        "tariff_and_duties": {{
            "hs_code": "string - recommended HS code",
            "mfn_duty_rate": "string - normal tariff rate",
            "preferential_schemes": [
                {{
                    "scheme_name": "string - preferential scheme name (GSP, FTA, etc)",
                    "preferential_rate": "string - preferential rate",
                    "conditions": "string - conditions to qualify",
                    "certificate_needed": "string - required certificate"
                }}
            ]
        }},
        "prohibited_or_restricted": {{
            "is_prohibited": false,
            "is_restricted": false,
            "restrictions": ["string - list of restrictions if any"],
            "special_permits_needed": ["string - special permits if needed"]
        }},
        "action_priority_list": [
            {{
                "priority_order": 1,
                "action": "string - action to take",
                "category": "string - category (Certification/Labeling/Documentation/etc)",
                "estimated_time": "string - time estimate",
                "estimated_cost_idr": "string - cost estimate",
                "blocking_export": true/false
            }}
        ],
        "country_specific_notes": [
            "string - specific notes for target country"
        ]
    }}
}}

Provide ONLY the JSON output, no additional text."""
        else:  # Indonesian
            prompt = f"""Analisis produk berikut dan berikan rekomendasi regulasi SPESIFIK untuk ekspor ke negara tujuan.

## DATA PRODUK
- Nama Produk: {product.name_local}
- Kategori: {product.category_id}
- Komposisi Material: {product.material_composition or 'Tidak ditentukan'}
- Jenis Kemasan: {product.packaging_type or 'Tidak ditentukan'}
- Kode HS: {hs_code or 'Belum ditentukan'}
- Deskripsi: {product.description_local[:200]}...
- Berat: {product.weight_net} kg (netto), {product.weight_gross} kg (bruto)

## NEGARA TUJUAN
- Negara: {target_country.country_name} ({target_country.country_code})
- Wilayah: {target_country.region}

## MASALAH KEPATUHAN YANG TERDETEKSI
{compliance_issues_json}

## TUGAS ANDA
Berikan rekomendasi regulasi SPESIFIK dalam format JSON valid:

{{
    "regulation_recommendations": {{
        "product_classification": {{
            "detected_category": "string - kategori produk yang terdeteksi",
            "hs_code_suggestion": "string - kode HS 6-8 digit",
            "hs_description": "string - deskripsi kode HS",
            "regulatory_category": "string - kategori regulasi (Produk Konsumen/Makanan/Kosmetik/dll)"
        }},
        "required_certifications": [
            {{
                "certification_name": "string - nama sertifikasi lengkap",
                "regulatory_body": "string - nama lembaga pengawas",
                "why_applicable": "string - mengapa sertifikasi ini diperlukan untuk produk ini",
                "estimated_cost_idr": "string - range biaya dalam Rupiah (contoh: '5.000.000 - 10.000.000')",
                "processing_time": "string - estimasi waktu proses (contoh: '2-3 bulan')",
                "how_to_obtain": "string - panduan langkah demi langkah untuk mendapatkan sertifikasi",
                "priority": "critical/high/medium/low",
                "applicable": true/false,
                "not_applicable_reason": "string - jika tidak applicable, jelaskan alasannya"
            }}
        ],
        "material_specific_regulations": [
            {{
                "material": "string - nama material dari komposisi",
                "percentage": "string - persentase dalam produk",
                "applicable_regulations": [
                    {{
                        "regulation_name": "string - nama regulasi",
                        "regulation_number": "string - nomor regulasi jika ada",
                        "requirement": "string - apa yang diwajibkan",
                        "compliance_action": "string - tindakan yang harus dilakukan",
                        "documentation_needed": "string - dokumen yang diperlukan",
                        "risk_if_non_compliant": "string - risiko jika tidak patuh"
                    }}
                ]
            }}
        ],
        "labeling_requirements": [
            {{
                "requirement_name": "string - nama persyaratan",
                "regulation_reference": "string - referensi regulasi",
                "specification": "string - spesifikasi detail",
                "language_requirement": "string - bahasa yang wajib digunakan",
                "placement": "string - lokasi penempatan label",
                "mandatory": true/false,
                "example": "string - contoh format label"
            }}
        ],
        "packaging_requirements": [
            {{
                "requirement_name": "string - nama persyaratan",
                "current_packaging": "string - kemasan yang digunakan saat ini",
                "compliance_status": "compliant/non_compliant/needs_verification",
                "regulation_reference": "string - referensi regulasi",
                "action_needed": "string - tindakan yang diperlukan",
                "notes": "string - catatan tambahan"
            }}
        ],
        "import_documentation": [
            {{
                "document_name": "string - nama dokumen",
                "required": true/false,
                "issuing_authority": "string - lembaga penerbit di Indonesia",
                "purpose": "string - tujuan dokumen",
                "must_include": ["string - informasi yang harus tercantum"],
                "estimated_cost_idr": "string - estimasi biaya",
                "processing_time": "string - waktu pemrosesan"
            }}
        ],
        "tariff_and_duties": {{
            "hs_code": "string - kode HS yang direkomendasikan",
            "mfn_duty_rate": "string - tarif normal",
            "preferential_schemes": [
                {{
                    "scheme_name": "string - nama skema preferensi (GSP, FTA, dll)",
                    "preferential_rate": "string - tarif preferensi",
                    "conditions": "string - syarat untuk mendapatkan preferensi",
                    "certificate_needed": "string - sertifikat yang diperlukan"
                }}
            ]
        }},
        "prohibited_or_restricted": {{
            "is_prohibited": false,
            "is_restricted": false,
            "restrictions": ["string - daftar pembatasan jika ada"],
            "special_permits_needed": ["string - izin khusus jika diperlukan"]
        }},
        "action_priority_list": [
            {{
                "priority_order": 1,
                "action": "string - tindakan yang harus dilakukan",
                "category": "string - kategori (Sertifikasi/Labeling/Dokumentasi/dll)",
                "estimated_time": "string - estimasi waktu",
                "estimated_cost_idr": "string - estimasi biaya",
                "blocking_export": true/false
            }}
        ],
        "country_specific_notes": [
            "string - catatan khusus untuk negara tujuan"
        ]
    }}
}}

Berikan HANYA output JSON, tanpa teks tambahan."""

        try:
            response = self._call_ai(prompt, system_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                logger.warning(f"Could not extract JSON from AI response: {response[:200]}...")
                return self._generate_fallback_recommendations(product, target_country, compliance_issues, language)

        except Exception as e:
            logger.error(f"Error generating regulation recommendations: {e}")
            return self._generate_fallback_recommendations(product, target_country, compliance_issues, language)

    def _generate_fallback_recommendations(
        self,
        product,
        target_country: Country,
        compliance_issues: list,
        language: str = "id",
    ) -> dict:
        """
        Generate fallback recommendations if AI call fails.
        Provides basic structure with available data.
        """
        if language == "en":
            return {
                "regulation_recommendations": {
                    "product_classification": {
                        "detected_category": f"Category {product.category_id}",
                        "hs_code_suggestion": getattr(product.enrichment, "hs_code_recommendation", "00000000") if hasattr(product, "enrichment") else "00000000",
                        "hs_description": "HS Code requires verification",
                        "regulatory_category": "General Consumer Product"
                    },
                    "required_certifications": [
                        {
                            "certification_name": f"Export Certification for {target_country.country_name}",
                            "regulatory_body": f"{target_country.country_name} Customs Authority",
                            "why_applicable": "Required for product import",
                            "estimated_cost_idr": "1,000,000 - 5,000,000",
                            "processing_time": "1-2 months",
                            "how_to_obtain": "Contact local trade authority for specific requirements",
                            "priority": "high",
                            "applicable": True,
                            "not_applicable_reason": ""
                        }
                    ],
                    "material_specific_regulations": [],
                    "labeling_requirements": [
                        {
                            "requirement_name": "Product Labeling",
                            "regulation_reference": "Standard import requirements",
                            "specification": "Product name, origin, materials, and manufacturer information",
                            "language_requirement": "English or local language",
                            "placement": "Visible on product packaging",
                            "mandatory": True,
                            "example": "Product: [Name] | Origin: Indonesia | Materials: [List]"
                        }
                    ],
                    "packaging_requirements": [],
                    "import_documentation": [
                        {
                            "document_name": "Certificate of Origin",
                            "required": True,
                            "issuing_authority": "Kamar Dagang dan Industri (KADIN) Indonesia",
                            "purpose": "Prove product origin for tariff benefits",
                            "must_include": ["Product description", "HS Code", "Origin country"],
                            "estimated_cost_idr": "100,000 - 500,000",
                            "processing_time": "3-5 business days"
                        }
                    ],
                    "tariff_and_duties": {
                        "hs_code": getattr(product.enrichment, "hs_code_recommendation", "00000000") if hasattr(product, "enrichment") else "00000000",
                        "mfn_duty_rate": "Requires verification",
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
                            "action": "Verify HS Code classification",
                            "category": "Classification",
                            "estimated_time": "1 week",
                            "estimated_cost_idr": "0",
                            "blocking_export": True
                        },
                        {
                            "priority_order": 2,
                            "action": f"Research {target_country.country_name} import requirements",
                            "category": "Documentation",
                            "estimated_time": "2 weeks",
                            "estimated_cost_idr": "0",
                            "blocking_export": True
                        }
                    ],
                    "country_specific_notes": [
                        f"Please consult with {target_country.country_name} trade authorities for the most current regulations.",
                        "Requirements may vary based on product specifics and recent policy changes."
                    ]
                }
            }
        else:  # Indonesian
            return {
                "regulation_recommendations": {
                    "product_classification": {
                        "detected_category": f"Kategori {product.category_id}",
                        "hs_code_suggestion": getattr(product.enrichment, "hs_code_recommendation", "00000000") if hasattr(product, "enrichment") else "00000000",
                        "hs_description": "Kode HS memerlukan verifikasi",
                        "regulatory_category": "Produk Konsumen Umum"
                    },
                    "required_certifications": [
                        {
                            "certification_name": f"Sertifikasi Ekspor untuk {target_country.country_name}",
                            "regulatory_body": f"Otoritas Bea Cukai {target_country.country_name}",
                            "why_applicable": "Diperlukan untuk impor produk",
                            "estimated_cost_idr": "1.000.000 - 5.000.000",
                            "processing_time": "1-2 bulan",
                            "how_to_obtain": "Hubungi otoritas perdagangan lokal untuk persyaratan spesifik",
                            "priority": "high",
                            "applicable": True,
                            "not_applicable_reason": ""
                        }
                    ],
                    "material_specific_regulations": [],
                    "labeling_requirements": [
                        {
                            "requirement_name": "Label Produk",
                            "regulation_reference": "Persyaratan impor standar",
                            "specification": "Nama produk, asal, material, dan informasi produsen",
                            "language_requirement": "Bahasa Inggris atau bahasa lokal",
                            "placement": "Terlihat pada kemasan produk",
                            "mandatory": True,
                            "example": "Produk: [Nama] | Asal: Indonesia | Material: [Daftar]"
                        }
                    ],
                    "packaging_requirements": [],
                    "import_documentation": [
                        {
                            "document_name": "Surat Keterangan Asal (Certificate of Origin)",
                            "required": True,
                            "issuing_authority": "Kamar Dagang dan Industri (KADIN) Indonesia",
                            "purpose": "Membuktikan asal produk untuk manfaat tarif",
                            "must_include": ["Deskripsi produk", "Kode HS", "Negara asal"],
                            "estimated_cost_idr": "100.000 - 500.000",
                            "processing_time": "3-5 hari kerja"
                        }
                    ],
                    "tariff_and_duties": {
                        "hs_code": getattr(product.enrichment, "hs_code_recommendation", "00000000") if hasattr(product, "enrichment") else "00000000",
                        "mfn_duty_rate": "Memerlukan verifikasi",
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
                            "action": "Verifikasi klasifikasi kode HS",
                            "category": "Klasifikasi",
                            "estimated_time": "1 minggu",
                            "estimated_cost_idr": "0",
                            "blocking_export": True
                        },
                        {
                            "priority_order": 2,
                            "action": f"Riset persyaratan impor {target_country.country_name}",
                            "category": "Dokumentasi",
                            "estimated_time": "2 minggu",
                            "estimated_cost_idr": "0",
                            "blocking_export": True
                        }
                    ],
                    "country_specific_notes": [
                        f"Silakan berkonsultasi dengan otoritas perdagangan {target_country.country_name} untuk regulasi terkini.",
                        "Persyaratan dapat bervariasi berdasarkan spesifik produk dan perubahan kebijakan terbaru."
                    ]
                }
            }
