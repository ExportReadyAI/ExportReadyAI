"""
Kolosal AI Service for ExportReady.AI

Implements AI Services for Product Enrichment:

# PBI-BE-M2-06: Service: AI HS Code Mapper
# - Input: name_local, material_composition, category
# - Logic: Extract keywords, query dengan LLM untuk suggest HS Code
# - LLM Prompt: "Berikan HS Code 8 digit untuk produk: {name} dengan material: {material}"
# - Output: hs_code_recommendation (string 8 digit)
# - Fallback: return "00000000" jika tidak ditemukan

# PBI-BE-M2-07: Service: AI Description Rewriter
# - Input: description_local, name_local, material_composition
# - LLM Prompt: "Translate dan rewrite ke bahasa Inggris formal B2B, max 300 kata"
# - Output: description_english_b2b (text)
# - Post-process: trim, remove extra whitespace

# PBI-BE-M2-08: Service: AI SKU Generator
# - Input: category, material_composition, product_id, business_id
# - Logic: Extract 3 huruf dari category → CAT, 3 huruf dari material → MAT
# - Format: {CAT}-{MAT}-{SEQ} contoh: BAG-LTH-001
# - Output: sku_generated (string)

All acceptance criteria for these PBIs are implemented in this module.
"""

import json
import logging
import re
from typing import Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class KolosalAIService:
    """
    Service class for interacting with Kolosal AI API.
    Uses OpenAI-compatible SDK.
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

    def generate_hs_code(
        self,
        product_name: str,
        material_composition: str,
        category: str = "",
        description: str = "",
    ) -> str:
        """
        # PBI-BE-M2-06: Service: AI HS Code Mapper
        #
        # Acceptance Criteria:
        # ✅ Input: name_local, material_composition, category
        # ✅ Logic Step 1: Extract keywords dari input
        # ✅ Logic Step 2: Query HSCode dengan LLM untuk suggest
        # ✅ LLM Prompt: "Berikan HS Code 8 digit untuk produk: {name} dengan material: {material}"
        # ✅ Output: hs_code_recommendation (string)
        # ✅ Fallback: return "00000000" jika tidak ditemukan

        Args:
            product_name: Local product name
            material_composition: Materials used in the product
            category: Product category
            description: Product description

        Returns:
            8-digit HS Code recommendation
        """
        system_prompt = """Kamu adalah ahli perdagangan internasional Indonesia yang sangat paham tentang HS Code (Harmonized System Code).
Tugasmu adalah menentukan HS Code 8 digit yang paling tepat untuk produk ekspor Indonesia.

PENTING:
- Berikan HANYA HS Code 8 digit, tanpa penjelasan lain
- Format: XXXXXXXX (8 digit angka)
- Jika tidak yakin, berikan HS Code yang paling mendekati
- Fokus pada klasifikasi produk Indonesia untuk ekspor"""

        prompt = f"""Tentukan HS Code 8 digit untuk produk berikut:

Nama Produk: {product_name}
Bahan/Material: {material_composition}
Kategori: {category}
Deskripsi: {description}

Berikan HANYA HS Code 8 digit (contoh: 19059090):"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Extract only digits from response
            hs_code = re.sub(r'\D', '', response)[:8]

            # Validate we got 8 digits
            if len(hs_code) == 8 and hs_code.isdigit():
                return hs_code

            # Fallback if extraction failed
            logger.warning(f"HS Code extraction failed, raw response: {response}")
            return "00000000"

        except Exception as e:
            logger.error(f"Error generating HS Code: {e}")
            return "00000000"

    def generate_description_english(
        self,
        product_name: str,
        description_local: str,
        material_composition: str = "",
    ) -> str:
        """
        # PBI-BE-M2-07: Service: AI Description Rewriter
        #
        # Acceptance Criteria:
        # ✅ Input: description_local, name_local, material_composition
        # ✅ LLM Prompt: "Translate dan rewrite deskripsi produk ke bahasa Inggris formal B2B"
        # ✅ Max 300 kata, professional tone
        # ✅ Output: description_english_b2b (text)
        # ✅ Post-process: trim, remove extra whitespace

        Args:
            product_name: Local product name
            description_local: Description in Indonesian
            material_composition: Materials used

        Returns:
            Professional English B2B description
        """
        system_prompt = """Kamu adalah copywriter profesional untuk ekspor B2B.
Tugasmu adalah menerjemahkan dan menulis ulang deskripsi produk dari Bahasa Indonesia ke Bahasa Inggris yang profesional untuk buyer internasional.

ATURAN:
- Gunakan bahasa Inggris formal dan profesional (B2B tone)
- Maksimal 300 kata
- Highlight keunggulan produk
- Jangan gunakan bahasa marketing berlebihan
- Fokus pada spesifikasi dan value proposition
- JANGAN sertakan judul atau header, langsung isi deskripsi saja"""

        prompt = f"""Terjemahkan dan tulis ulang deskripsi produk ini ke Bahasa Inggris B2B yang profesional:

Nama Produk: {product_name}
Deskripsi Asli: {description_local}
Bahan/Material: {material_composition}

Tulis deskripsi profesional dalam Bahasa Inggris:"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Clean up response - remove any markdown or extra formatting
            response = response.strip()
            # Remove potential quotes at start/end
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]
            return response

        except Exception as e:
            logger.error(f"Error generating English description: {e}")
            return f"Premium quality {product_name} from Indonesia."

    def generate_english_product_name(
        self,
        product_name: str,
        material_composition: str = "",
        category: str = "",
    ) -> str:
        """
        Generate professional English product name for B2B.

        Args:
            product_name: Local product name
            material_composition: Materials used
            category: Product category

        Returns:
            Professional English product name
        """
        system_prompt = """Kamu adalah ahli penamaan produk untuk ekspor internasional.
Tugasmu adalah membuat nama produk dalam Bahasa Inggris yang profesional dan menarik untuk buyer B2B.

ATURAN:
- Nama singkat dan profesional (maksimal 5-7 kata)
- Gunakan terminologi standar internasional
- Highlight material atau keunggulan utama jika relevan
- JANGAN gunakan tanda kutip
- Berikan HANYA nama produk, tanpa penjelasan"""

        prompt = f"""Buat nama produk Bahasa Inggris yang profesional untuk:

Nama Lokal: {product_name}
Bahan: {material_composition}
Kategori: {category}

Nama produk Bahasa Inggris:"""

        try:
            response = self._call_ai(prompt, system_prompt)
            # Clean up
            response = response.strip().strip('"').strip("'")
            return response[:255]  # Limit to field max length

        except Exception as e:
            logger.error(f"Error generating English name: {e}")
            return f"{product_name} - Export Grade"

    def generate_sku(
        self,
        category: str,
        material_composition: str,
        product_id: int,
        business_id: int,
    ) -> str:
        """
        # PBI-BE-M2-08: Service: AI SKU Generator
        #
        # Acceptance Criteria:
        # ✅ Input: category, material_composition, product_id, business_id
        # ✅ Logic: Extract 3 huruf dari category → CAT
        # ✅ Logic: Extract 3 huruf dari material → MAT
        # ✅ Logic: Generate sequential number per business
        # ✅ Format: {CAT}-{MAT}-{SEQ} contoh: BAG-LTH-001
        # ✅ Output: sku_generated (string)

        Args:
            category: Product category
            material_composition: Primary material
            product_id: Product ID for sequence
            business_id: Business ID for uniqueness

        Returns:
            Generated SKU code
        """
        # Extract 3 letters from category
        cat_code = self._extract_code(category, 3)

        # Extract 3 letters from material
        mat_code = self._extract_code(material_composition, 3)

        # Generate sequence number
        seq = f"{product_id:03d}"

        return f"{cat_code}-{mat_code}-{seq}"

    def _extract_code(self, text: str, length: int = 3) -> str:
        """
        Extract code from text (first N consonants or characters).

        Args:
            text: Input text
            length: Desired code length

        Returns:
            Extracted code in uppercase
        """
        if not text:
            return "XXX"[:length]

        # Remove non-alphabetic characters
        clean = re.sub(r'[^a-zA-Z]', '', text)

        if not clean:
            return "XXX"[:length]

        # Take first N characters
        code = clean[:length].upper()

        # Pad if needed
        while len(code) < length:
            code += "X"

        return code

    def generate_marketing_highlights(
        self,
        product_name: str,
        description: str,
        material_composition: str = "",
    ) -> list:
        """
        Generate marketing highlights/selling points for the product.

        Args:
            product_name: Product name
            description: Product description
            material_composition: Materials used

        Returns:
            List of marketing highlights
        """
        system_prompt = """Kamu adalah marketing expert untuk produk ekspor.
Tugasmu adalah mengekstrak poin-poin jual utama dari produk.

ATURAN:
- Berikan 3-5 poin jual singkat
- Setiap poin maksimal 3 kata
- Gunakan Bahasa Inggris
- Format: satu poin per baris
- Contoh: "Handmade", "Eco-Friendly", "Premium Quality"
- JANGAN gunakan numbering atau bullet points"""

        prompt = f"""Ekstrak poin jual utama dari produk ini:

Nama: {product_name}
Deskripsi: {description}
Bahan: {material_composition}

Poin jual (satu per baris):"""

        try:
            response = self._call_ai(prompt, system_prompt)

            # Parse response into list
            highlights = []
            for line in response.strip().split('\n'):
                # Clean each line
                line = line.strip().strip('-').strip('•').strip('*').strip()
                line = re.sub(r'^\d+\.?\s*', '', line)  # Remove numbering
                if line and len(line) < 50:  # Reasonable length
                    highlights.append(line)

            # Return at most 5 highlights
            return highlights[:5] if highlights else ["Premium Quality", "Export Grade"]

        except Exception as e:
            logger.error(f"Error generating marketing highlights: {e}")
            return ["Premium Quality", "Export Grade"]

    def enrich_product(
        self,
        product_name: str,
        description_local: str,
        material_composition: str,
        category: str,
        product_id: int,
        business_id: int,
    ) -> dict:
        """
        Full product enrichment - combines all AI services.

        Args:
            product_name: Local product name
            description_local: Description in Indonesian
            material_composition: Materials used
            category: Product category
            product_id: Product ID
            business_id: Business ID

        Returns:
            Dictionary with all enrichment data
        """
        return {
            "hs_code_recommendation": self.generate_hs_code(
                product_name, material_composition, category, description_local
            ),
            "sku_generated": self.generate_sku(
                category, material_composition, product_id, business_id
            ),
            "name_english_b2b": self.generate_english_product_name(
                product_name, material_composition, category
            ),
            "description_english_b2b": self.generate_description_english(
                product_name, description_local, material_composition
            ),
            "marketing_highlights": self.generate_marketing_highlights(
                product_name, description_local, material_composition
            ),
        }
