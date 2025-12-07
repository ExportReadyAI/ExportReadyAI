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
        
        Note: This method analyzes the CURRENT product data. The snapshot
        should be created by the caller (view/API) when storing the analysis.

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
    
    def analyze_product_from_snapshot(
        self,
        product_snapshot: dict,
        target_country_code: str,
    ) -> dict:
        """
        Run compliance analysis using product snapshot data.
        This allows analyzing historical product states.

        Args:
            product_snapshot: Product snapshot dictionary
            target_country_code: Target country ISO code

        Returns:
            Dictionary with analysis results
        """
        all_issues = []

        # Check ingredient compliance from snapshot
        ingredient_issues = self.check_ingredient_compliance(
            material_composition=product_snapshot.get("material_composition", ""),
            target_country_code=target_country_code,
        )
        all_issues.extend(ingredient_issues)

        # Check specification compliance from snapshot
        spec_issues = self.check_specification_compliance(
            quality_specs=product_snapshot.get("quality_specs", {}),
            target_country_code=target_country_code,
        )
        all_issues.extend(spec_issues)

        # Check packaging compliance from snapshot
        packaging_issues = self.check_packaging_compliance(
            packaging_type=product_snapshot.get("packaging_type", ""),
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
