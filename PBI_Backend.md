# 📋 Product Backlog BACKEND - ExportReady.AI
## Platform AI untuk Ekspor UMKM Indonesia

> **Keterangan Role:**
> - **Guest** = Belum login (hanya akses Register & Login)
> - **Admin** = Administrator sistem
> - **UMKM** = Pelaku usaha (user utama)

> **Sync dengan Frontend:**
> - Setiap endpoint BE memiliki pasangan UI di FE
> - Format: `PBI-BE-Mx-xx` ↔ `PBI-FE-Mx-xx`

---

## 🟩 MODUL 1: IDENTITAS BISNIS (User & BusinessProfile)

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M1-01 | | API: POST /auth/register | Guest | ✅ Endpoint menerima body: email, password, full_name |
| | | | | ✅ Validasi server-side: email format valid |
| | | | | ✅ Validasi server-side: email belum terdaftar (unique) |
| | | | | ✅ Validasi server-side: password minimal 8 karakter |
| | | | | ✅ Password di-hash menggunakan bcrypt sebelum disimpan |
| | | | | ✅ Role default = "UMKM" |
| | | | | ✅ Response success: 201 Created dengan user data (tanpa password) |
| | | | | ✅ Response error: 400 Bad Request dengan error message |
| | | | | ✅ Response error: 409 Conflict jika email sudah ada |
| PBI-BE-M1-02 | | API: POST /auth/login | Guest | ✅ Endpoint menerima body: email, password |
| | | | | ✅ Validasi kredensial dengan database |
| | | | | ✅ Compare password dengan bcrypt |
| | | | | ✅ Generate JWT token jika valid |
| | | | | ✅ Token berisi: user_id, email, role, exp |
| | | | | ✅ Response success: 200 OK dengan token dan user data |
| | | | | ✅ Response error: 401 Unauthorized jika kredensial salah |
| PBI-BE-M1-03 | | API: GET /auth/me | Admin, UMKM | ✅ Endpoint memerlukan Authorization header (Bearer token) |
| | | | | ✅ Validate dan decode JWT token |
| | | | | ✅ Response success: 200 OK dengan user data lengkap |
| | | | | ✅ Response error: 401 Unauthorized jika token invalid/expired |
| PBI-BE-M1-04 | | API: POST /business-profile | UMKM | ✅ Endpoint menerima body: company_name, address, production_capacity_per_month, year_established |
| | | | | ✅ Validasi: user belum memiliki BusinessProfile (1-to-1) |
| | | | | ✅ Validasi: semua field wajib terisi |
| | | | | ✅ Validasi: year_established <= current year |
| | | | | ✅ Auto-assign user_id dari token |
| | | | | ✅ Default certifications = [] (empty array) |
| | | | | ✅ Response success: 201 Created dengan business profile data |
| | | | | ✅ Response error: 400 Bad Request jika validasi gagal |
| | | | | ✅ Response error: 409 Conflict jika sudah ada profile |
| PBI-BE-M1-05 | | API: GET /business-profile | Admin, UMKM | ✅ Jika role = UMKM: return profile milik user (by user_id dari token) |
| | | | | ✅ Jika role = Admin: return semua profile (dengan pagination) |
| | | | | ✅ Admin dapat filter by user_id (query param) |
| | | | | ✅ Response success: 200 OK dengan profile data |
| | | | | ✅ Response error: 404 Not Found jika UMKM belum punya profile |
| PBI-BE-M1-06 | | API: PUT /business-profile/:id | UMKM | ✅ Endpoint menerima body: company_name, address, production_capacity_per_month, year_established |
| | | | | ✅ Validasi: profile_id milik user yang login |
| | | | | ✅ Validasi: semua field yang dikirim valid |
| | | | | ✅ Update hanya field yang dikirim |
| | | | | ✅ Response success: 200 OK dengan updated data |
| | | | | ✅ Response error: 403 Forbidden jika bukan milik user |
| | | | | ✅ Response error: 404 Not Found jika profile tidak ada |
| PBI-BE-M1-07 | | API: PATCH /business-profile/:id/certifications | UMKM | ✅ Endpoint menerima body: certifications (array of strings) |
| | | | | ✅ Validasi: nilai hanya boleh ["Halal", "ISO", "HACCP", "SVLK"] |
| | | | | ✅ Validasi: profile_id milik user yang login |
| | | | | ✅ Update field certifications (replace entire array) |
| | | | | ✅ Response success: 200 OK dengan updated certifications |
| PBI-BE-M1-08 | | API: GET /users (Admin) | Admin | ✅ Return daftar semua user dengan pagination |
| | | | | ✅ Query params: page, limit, role, search |
| | | | | ✅ Search by email atau full_name (LIKE query) |
| | | | | ✅ Response: array of users dengan total count |
| | | | | ✅ Response tidak include password_hash |
| PBI-BE-M1-09 | | API: DELETE /users/:id | UMKM | ✅ UMKM hanya bisa delete akun sendiri |
| | | | | ✅ Cascade delete: BusinessProfile, Product, ProductEnrichment, ExportAnalysis, Costing |
| | | | | ✅ Response success: 200 OK dengan message |
| | | | | ✅ Response error: 403 Forbidden jika bukan akun sendiri |
| PBI-BE-M1-10 | | Middleware: Auth Guard | System | ✅ Middleware untuk protect routes |
| | | | | ✅ Extract token dari Authorization header |
| | | | | ✅ Validate JWT token |
| | | | | ✅ Attach user data ke request object |
| | | | | ✅ Return 401 jika token tidak ada atau invalid |
| PBI-BE-M1-11 | | Middleware: Role Guard | System | ✅ Middleware untuk check role |
| | | | | ✅ Accept array of allowed roles |
| | | | | ✅ Check user role dari request object |
| | | | | ✅ Return 403 jika role tidak sesuai |
| PBI-BE-M1-12 | | API: GET /dashboard/summary | Admin, UMKM | ✅ Return summary counts untuk dashboard |
| | | | | ✅ UMKM: product_count, analysis_count, costing_count (milik sendiri) |
| | | | | ✅ Admin: total_users, total_products, total_analysis |
| | | | | ✅ Include: has_business_profile (boolean) |
| | | | | ✅ Response: 200 OK dengan summary object |

---

## 🟨 MODUL 2: MANAJEMEN PRODUK & SPESIFIKASI (Product & ProductEnrichment)

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M2-01 | | API: GET /products | Admin, UMKM | ✅ UMKM: return products milik user (by business_id) |
| | | | | ✅ Admin: return semua products (dengan filter by business_id) |
| | | | | ✅ Query params: page, limit, category, search |
| | | | | ✅ Search by name_local (LIKE query) |
| | | | | ✅ Include basic ProductEnrichment data (hs_code, sku) jika ada |
| | | | | ✅ Response: array of products dengan pagination info |
| PBI-BE-M2-02 | | API: GET /products/:id | Admin, UMKM | ✅ Return detail lengkap product by id |
| | | | | ✅ Include ProductEnrichment data (full) |
| | | | | ✅ Validasi: UMKM hanya bisa akses product miliknya |
| | | | | ✅ Response success: 200 OK dengan product + enrichment |
| | | | | ✅ Response error: 404 Not Found |
| | | | | ✅ Response error: 403 Forbidden |
| PBI-BE-M2-03 | | API: POST /products | UMKM | ✅ Endpoint menerima body lengkap sesuai schema Product |
| | | | | ✅ Auto-assign business_id dari user's BusinessProfile |
| | | | | ✅ Validasi: user harus punya BusinessProfile |
| | | | | ✅ Validasi: semua required field terisi |
| | | | | ✅ Validasi: dimensions dan weight bernilai positif |
| | | | | ✅ quality_specs disimpan sebagai JSON |
| | | | | ✅ dimensions_l_w_h disimpan sebagai JSON {l, w, h} |
| | | | | ✅ Auto-trigger AI Enrichment setelah create |
| | | | | ✅ Response success: 201 Created dengan product data |
| PBI-BE-M2-04 | | API: PUT /products/:id | UMKM | ✅ Update product by id |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Update hanya field yang dikirim |
| | | | | ✅ Auto-trigger AI Enrichment setelah update |
| | | | | ✅ Response success: 200 OK dengan updated data |
| PBI-BE-M2-05 | | API: DELETE /products/:id | UMKM | ✅ Delete product by id |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Cascade delete: ProductEnrichment, ExportAnalysis, Costing |
| | | | | ✅ Response success: 200 OK |
| PBI-BE-M2-06 | | Service: AI HS Code Mapper | System | ✅ Input: name_local, material_composition, category |
| | | | | ✅ Logic Step 1: Extract keywords dari input |
| | | | | ✅ Logic Step 2: Query HSCode table dengan keyword matching |
| | | | | ✅ Logic Step 3: Jika tidak exact match, gunakan LLM untuk suggest |
| | | | | ✅ LLM Prompt: "Berikan HS Code 8 digit untuk produk: {name} dengan material: {material}" |
| | | | | ✅ Validate hasil LLM terhadap HSCode master |
| | | | | ✅ Output: hs_code_recommendation (string) |
| | | | | ✅ Fallback: return null jika tidak ditemukan |
| PBI-BE-M2-07 | | Service: AI Description Rewriter | System | ✅ Input: description_local, name_local, material_composition |
| | | | | ✅ LLM Prompt: "Translate dan rewrite deskripsi produk berikut ke bahasa Inggris formal untuk B2B: {description}. Produk: {name}, Material: {material}. Max 300 kata, professional tone." |
| | | | | ✅ Output: description_english_b2b (text) |
| | | | | ✅ Post-process: trim, remove extra whitespace |
| PBI-BE-M2-08 | | Service: AI SKU Generator | System | ✅ Input: category, material_composition, product_id, business_id |
| | | | | ✅ Logic: Extract 3 huruf dari category → CAT |
| | | | | ✅ Logic: Extract 3 huruf dari material → MAT |
| | | | | ✅ Logic: Generate sequential number per business |
| | | | | ✅ Format: {CAT}-{MAT}-{SEQ} contoh: BAG-LTH-001 |
| | | | | ✅ Validasi: SKU unique dalam business |
| | | | | ✅ Output: sku_generated (string) |
| PBI-BE-M2-09 | | API: POST /products/:id/enrich | UMKM | ✅ Trigger manual AI Enrichment untuk product |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Call semua AI Services (HS Code, Description, SKU) |
| | | | | ✅ Create atau Update ProductEnrichment |
| | | | | ✅ Update last_updated_ai timestamp |
| | | | | ✅ Response: 200 OK dengan enrichment result |
| PBI-BE-M2-10 | | API: PATCH /products/:id/enrichment | UMKM | ✅ Manual override AI results |
| | | | | ✅ Body: hs_code_recommendation, sku_generated, description_english_b2b |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Update only fields yang dikirim |
| | | | | ✅ Tandai sebagai "manually_edited" (optional flag) |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M2-11 | | Database: Product Table | System | ✅ Create table dengan schema sesuai ER Diagram |
| | | | | ✅ Foreign key ke BusinessProfile |
| | | | | ✅ JSON columns untuk quality_specs dan dimensions |
| | | | | ✅ Index pada business_id dan category |
| | | | | ✅ Timestamps: created_at, updated_at |
| PBI-BE-M2-12 | | Database: ProductEnrichment Table | System | ✅ Create table dengan schema sesuai ER Diagram |
| | | | | ✅ Foreign key ke Product (1-to-1) |
| | | | | ✅ Foreign key ke HSCode (nullable) |
| | | | | ✅ Unique constraint pada product_id |
| | | | | ✅ Timestamp: last_updated_ai |

---

## 🟦 MODUL 3: ANALISIS KELAYAKAN EKSPOR (Country, CountryRegulation, ExportAnalysis)

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M3-01 | | API: GET /export-analysis | Admin, UMKM | ✅ UMKM: return analysis untuk products miliknya |
| | | | | ✅ Admin: return semua analysis |
| | | | | ✅ Query params: page, limit, country_code, score_min, score_max, search |
| | | | | ✅ Include: product name, country name |
| | | | | ✅ Response: array dengan pagination |
| PBI-BE-M3-02 | | API: GET /export-analysis/:id | Admin, UMKM | ✅ Return detail lengkap analysis |
| | | | | ✅ Include: product details, country details, compliance_issues, recommendations |
| | | | | ✅ Validasi: UMKM hanya bisa akses analysis untuk product miliknya |
| | | | | ✅ Response: 200 OK atau 403/404 |
| PBI-BE-M3-03 | | API: POST /export-analysis | UMKM | ✅ Body: product_id, target_country_code |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Validasi: product sudah punya ProductEnrichment |
| | | | | ✅ Validasi: kombinasi product + country belum ada |
| | | | | ✅ Trigger AI Compliance Checker |
| | | | | ✅ Response: 201 Created dengan analysis result |
| PBI-BE-M3-04 | | Service: AI Compliance Checker - Ingredient | System | ✅ Input: material_composition (Product), target_country_code |
| | | | | ✅ Query: CountryRegulation WHERE country_code = target AND regulation_type = 'ingredient_ban' |
| | | | | ✅ Logic: Check if any banned ingredient exists in material |
| | | | | ✅ LLM Assist: "Apakah material '{material}' mengandung bahan terlarang: {banned_list}?" |
| | | | | ✅ Output: Array of issues dengan severity (critical/major/minor) |
| | | | | ✅ Issue format: {type, rule_key, your_value, required_value, description, severity} |
| PBI-BE-M3-05 | | Service: AI Compliance Checker - Specification | System | ✅ Input: quality_specs (Product), target_country_code |
| | | | | ✅ Query: CountryRegulation WHERE regulation_type = 'quality_std' |
| | | | | ✅ Logic: Compare each spec dengan country standard |
| | | | | ✅ Contoh: product.tolerance = "5mm", country.max_tolerance = "1mm" → issue |
| | | | | ✅ LLM Assist untuk interpretasi jika format berbeda |
| | | | | ✅ Output: Array of issues |
| PBI-BE-M3-06 | | Service: AI Compliance Checker - Packaging | System | ✅ Input: packaging_type (Product), target_country_code |
| | | | | ✅ Query: CountryRegulation WHERE regulation_type = 'packaging_std' |
| | | | | ✅ Logic: Check packaging requirements |
| | | | | ✅ Contoh: packaging = "Kayu" + country = "AU" → require ISPM-15 |
| | | | | ✅ Output: Array of issues dengan required certifications |
| PBI-BE-M3-07 | | Service: Calculate Readiness Score | System | ✅ Input: Array of all compliance issues |
| | | | | ✅ Base score = 100 |
| | | | | ✅ Deduction: critical = -20, major = -10, minor = -5 |
| | | | | ✅ Minimum score = 0 |
| | | | | ✅ Output: readiness_score (integer 0-100) |
| PBI-BE-M3-08 | | Service: Generate Recommendations | System | ✅ Input: Array of compliance issues |
| | | | | ✅ LLM Prompt: "Berdasarkan issues berikut, berikan rekomendasi perbaikan yang actionable: {issues}" |
| | | | | ✅ Format: numbered list, bahasa Indonesia |
| | | | | ✅ Output: recommendations (text) |
| PBI-BE-M3-09 | | API: POST /export-analysis/:id/reanalyze | UMKM | ✅ Re-run analysis dengan data product terbaru |
| | | | | ✅ Validasi: analysis milik user |
| | | | | ✅ Fetch latest product data |
| | | | | ✅ Re-run semua AI Compliance Checker |
| | | | | ✅ Update: compliance_issues, readiness_score, recommendations, analyzed_at |
| | | | | ✅ Response: 200 OK dengan updated result |
| PBI-BE-M3-10 | | API: DELETE /export-analysis/:id | UMKM | ✅ Delete analysis by id |
| | | | | ✅ Validasi: analysis untuk product milik user |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M3-11 | | API: GET /countries | Admin, UMKM | ✅ Return list semua countries |
| | | | | ✅ Query params: region, search |
| | | | | ✅ Include: regulations_count |
| | | | | ✅ Response: array of countries |
| PBI-BE-M3-12 | | API: GET /countries/:code | Admin, UMKM | ✅ Return country detail dengan regulations |
| | | | | ✅ Include: semua CountryRegulation grouped by type |
| | | | | ✅ Response: country object dengan nested regulations |
| PBI-BE-M3-13 | | API: POST /export-analysis/compare | UMKM | ✅ Body: product_id, country_codes (array, max 5) |
| | | | | ✅ Run analysis untuk setiap country |
| | | | | ✅ Return comparison data |
| | | | | ✅ Response: array of analysis results |
| PBI-BE-M3-14 | | Database: ExportAnalysis Table | System | ✅ Create table sesuai ER Diagram |
| | | | | ✅ Foreign key ke Product dan Country |
| | | | | ✅ Unique constraint pada (product_id, target_country_code) |
| | | | | ✅ JSON column untuk compliance_issues |
| | | | | ✅ Index pada product_id dan target_country_code |

---

## 🟧 MODUL 4: KALKULATOR KEUANGAN & LOGISTIK (Costing)

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M4-01 | | API: GET /costings | Admin, UMKM | ✅ UMKM: return costings untuk products miliknya |
| | | | | ✅ Admin: return semua costings |
| | | | | ✅ Query params: page, limit, search, sort_by |
| | | | | ✅ Include: product name |
| | | | | ✅ Response: array dengan pagination |
| PBI-BE-M4-02 | | API: GET /costings/:id | Admin, UMKM | ✅ Return detail lengkap costing |
| | | | | ✅ Include: product details |
| | | | | ✅ Validasi access control |
| | | | | ✅ Response: costing object |
| PBI-BE-M4-03 | | API: POST /costings | UMKM | ✅ Body: product_id, cogs_per_unit, packing_cost, target_margin_percent |
| | | | | ✅ Validasi: product milik user |
| | | | | ✅ Validasi: semua nilai positif |
| | | | | ✅ Trigger AI Price Calculation |
| | | | | ✅ Trigger AI Container Optimizer |
| | | | | ✅ Response: 201 Created dengan full costing result |
| PBI-BE-M4-04 | | API: PUT /costings/:id | UMKM | ✅ Update costing inputs |
| | | | | ✅ Body: cogs_per_unit, packing_cost, target_margin_percent |
| | | | | ✅ Validasi: costing untuk product milik user |
| | | | | ✅ Re-trigger calculations |
| | | | | ✅ Response: 200 OK dengan updated result |
| PBI-BE-M4-05 | | API: DELETE /costings/:id | UMKM | ✅ Delete costing by id |
| | | | | ✅ Validasi access control |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M4-06 | | Service: AI Price Calculator - EXW | System | ✅ Input: cogs_per_unit, packing_cost, target_margin_percent |
| | | | | ✅ Formula: EXW = (cogs + packing) × (1 + margin/100) |
| | | | | ✅ Convert IDR to USD using exchange rate |
| | | | | ✅ Output: recommended_exw_price (decimal, USD) |
| PBI-BE-M4-07 | | Service: AI Price Calculator - FOB | System | ✅ Input: EXW price, business address (untuk estimasi trucking) |
| | | | | ✅ Estimasi trucking cost berdasarkan lokasi ke pelabuhan terdekat |
| | | | | ✅ Estimasi document cost (flat rate atau percentage) |
| | | | | ✅ Formula: FOB = EXW + trucking + document |
| | | | | ✅ Output: recommended_fob_price (decimal, USD) |
| PBI-BE-M4-08 | | Service: AI Price Calculator - CIF | System | ✅ Input: FOB price, target_country (jika ada dari ExportAnalysis) |
| | | | | ✅ Estimasi freight berdasarkan negara tujuan |
| | | | | ✅ Insurance = 0.5% dari nilai barang (default) |
| | | | | ✅ Formula: CIF = FOB + freight + insurance |
| | | | | ✅ Output: recommended_cif_price (decimal, USD) |
| | | | | ✅ Jika tidak ada target country, CIF = null |
| PBI-BE-M4-09 | | Service: AI Container Optimizer | System | ✅ Input: dimensions_l_w_h (dari Product) |
| | | | | ✅ Container 20ft dimensions: 5.9m × 2.35m × 2.39m internal |
| | | | | ✅ Algorithm: 3D bin packing calculation |
| | | | | ✅ Output: container_20ft_capacity (integer, units) |
| | | | | ✅ Generate optimization_notes jika ada saran improvement |
| | | | | ✅ Contoh notes: "Kurangi tinggi 1cm untuk +200 units" |
| PBI-BE-M4-10 | | Service: Currency Exchange Rate | System | ✅ Get current IDR-USD exchange rate |
| | | | | ✅ Option 1: Fetch dari external API (currencyapi, exchangerate-api) |
| | | | | ✅ Option 2: Manual update oleh Admin |
| | | | | ✅ Cache rate untuk mengurangi API calls |
| | | | | ✅ Store: rate value, source, timestamp |
| PBI-BE-M4-11 | | API: GET /exchange-rate | Admin, UMKM | ✅ Return current exchange rate IDR-USD |
| | | | | ✅ Response: {rate, source, updated_at} |
| PBI-BE-M4-12 | | API: PUT /exchange-rate (Admin) | Admin | ✅ Manual update exchange rate |
| | | | | ✅ Body: rate (decimal) |
| | | | | ✅ Update stored rate |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M4-13 | | API: GET /costings/:id/pdf | UMKM | ✅ Generate PDF costing report |
| | | | | ✅ Include: company profile, product details, price breakdown, container info |
| | | | | ✅ Professional format untuk buyer |
| | | | | ✅ Response: PDF file (application/pdf) |
| PBI-BE-M4-14 | | Database: Costing Table | System | ✅ Create table sesuai ER Diagram |
| | | | | ✅ Foreign key ke Product |
| | | | | ✅ Decimal columns dengan precision yang tepat |
| | | | | ✅ Index pada product_id |

---

## 🟪 MODUL 5: MASTER DATA (Admin Only)

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M5-01 | | API: GET /hs-codes | Admin | ✅ Return list HS Codes dengan pagination |
| | | | | ✅ Query params: page, limit, chapter, search |
| | | | | ✅ Search by hs_code atau description |
| | | | | ✅ Response: array dengan pagination info |
| PBI-BE-M5-02 | | API: POST /hs-codes | Admin | ✅ Create new HS Code |
| | | | | ✅ Body: hs_code, description_id, description_en, keywords |
| | | | | ✅ Auto-extract: hs_chapter (2 digit), hs_heading (4 digit), hs_subheading (6 digit) |
| | | | | ✅ Validasi: hs_code format (8 digit) |
| | | | | ✅ Validasi: hs_code unique |
| | | | | ✅ Response: 201 Created |
| PBI-BE-M5-03 | | API: PUT /hs-codes/:code | Admin | ✅ Update HS Code |
| | | | | ✅ hs_code tidak dapat diubah |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M5-04 | | API: DELETE /hs-codes/:code | Admin | ✅ Delete HS Code |
| | | | | ✅ Validasi: tidak ada ProductEnrichment yang reference |
| | | | | ✅ Response: 200 OK atau 409 Conflict |
| PBI-BE-M5-05 | | API: POST /hs-codes/import | Admin | ✅ Bulk import dari CSV |
| | | | | ✅ Accept: multipart/form-data dengan CSV file |
| | | | | ✅ Parse CSV dan validate each row |
| | | | | ✅ Skip duplicates atau update existing |
| | | | | ✅ Response: {success_count, failed_count, errors} |
| PBI-BE-M5-06 | | API: POST /countries | Admin | ✅ Create new country |
| | | | | ✅ Body: country_code, country_name, region |
| | | | | ✅ Validasi: country_code format (2 char ISO) |
| | | | | ✅ Validasi: country_code unique |
| | | | | ✅ Response: 201 Created |
| PBI-BE-M5-07 | | API: PUT /countries/:code | Admin | ✅ Update country |
| | | | | ✅ country_code tidak dapat diubah |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M5-08 | | API: DELETE /countries/:code | Admin | ✅ Delete country |
| | | | | ✅ Cascade delete: CountryRegulation |
| | | | | ✅ Validasi: tidak ada ExportAnalysis yang reference |
| | | | | ✅ Response: 200 OK atau 409 Conflict |
| PBI-BE-M5-09 | | API: GET /countries/:code/regulations | Admin | ✅ Return regulations untuk country tertentu |
| | | | | ✅ Query params: regulation_type |
| | | | | ✅ Response: array of regulations |
| PBI-BE-M5-10 | | API: POST /countries/:code/regulations | Admin | ✅ Create regulation untuk country |
| | | | | ✅ Body: regulation_type, rule_key, rule_value, description |
| | | | | ✅ Validasi: regulation_type enum valid |
| | | | | ✅ Response: 201 Created |
| PBI-BE-M5-11 | | API: PUT /regulations/:id | Admin | ✅ Update regulation |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M5-12 | | API: DELETE /regulations/:id | Admin | ✅ Delete regulation |
| | | | | ✅ Response: 200 OK |
| PBI-BE-M5-13 | | API: POST /regulations/import | Admin | ✅ Bulk import regulations dari CSV |
| | | | | ✅ CSV format: country_code, regulation_type, rule_key, rule_value, description |
| | | | | ✅ Response: import result summary |
| PBI-BE-M5-14 | | Database: All Master Tables | System | ✅ Create HSCode table sesuai ER Diagram |
| | | | | ✅ Create Country table sesuai ER Diagram |
| | | | | ✅ Create CountryRegulation table sesuai ER Diagram |
| | | | | ✅ Proper indexes dan constraints |
| | | | | ✅ Seed data untuk initial countries dan regulations |

---

## 📊 SUMMARY BACKEND

| Modul | Jumlah Backlog | Komponen Utama |
|-------|----------------|----------------|
| 🟩 M1: Identitas Bisnis | 12 items | Auth API, Profile API, Middleware |
| 🟨 M2: Manajemen Produk | 12 items | Product CRUD, AI Services (HS, SKU, Desc) |
| 🟦 M3: Kelayakan Ekspor | 14 items | Analysis API, AI Compliance Checker |
| 🟧 M4: Kalkulator Finansial | 14 items | Costing API, Price Calculator, Container Optimizer |
| 🟪 M5: Master Data | 14 items | HS Code CRUD, Country CRUD, Regulation CRUD |
| **TOTAL** | **66 items** | |

---

## 🔗 SYNC MAPPING FE ↔ BE

| Frontend | Backend | Description |
|----------|---------|-------------|
| PBI-FE-M1-01 (Register Page) | PBI-BE-M1-01 (POST /auth/register) | User registration |
| PBI-FE-M1-02 (Login Page) | PBI-BE-M1-02 (POST /auth/login) | User login |
| PBI-FE-M2-03 (Create Product) | PBI-BE-M2-03 (POST /products) | Create product |
| PBI-FE-M2-06 (AI Loading State) | PBI-BE-M2-06,07,08 (AI Services) | AI processing |
| PBI-FE-M3-02 (Create Analysis) | PBI-BE-M3-03 + M3-04,05,06,07,08 | Full analysis flow |
| PBI-FE-M4-02 (Create Costing) | PBI-BE-M4-03 + M4-06,07,08,09 | Full costing flow |

---

*Document Generated: December 2024*
*Version: 1.0*
*Project: ExportReady.AI - Backend Backlog*
