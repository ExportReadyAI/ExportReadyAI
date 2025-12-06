# 📋 Product Backlog BACKEND - ExportReady.AI
## MODUL 7: EDUCATIONAL MATERIAL (Learning Path & Content Management)

> **Feature Scope:**
> - Feature 7.1: Learning Path Management
> - Feature 7.2: Multi-Format Content

> **Target Users:**
> - **UMKM** = Learners yang mengakses materi pembelajaran
> - **Admin** = Content managers yang mengelola materi

---

## 🟦 MODUL 7: EDUCATIONAL MATERIAL

### Sub-Module 7A: Learning Path Management
### Sub-Module 7B: Multi-Format Content & Progress Tracking

---

## 🔵 MODUL 7A: LEARNING PATH MANAGEMENT

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M7-01 | | Database: LearningPath Table | System | ✅ Create learning_paths table |
| | | | | ✅ Columns: id (PK), title, description, category, product_category, target_country, difficulty_level, estimated_duration_hours, is_published, order_index, thumbnail_url |
| | | | | ✅ Enum category: 'general', 'product_specific', 'country_specific' |
| | | | | ✅ Enum difficulty_level: 'beginner', 'intermediate', 'advanced' |
| | | | | ✅ Indexes on: category, product_category, target_country, is_published |
| | | | | ✅ Timestamps: created_at, updated_at |
| PBI-BE-M7-02 | | Database: Module Table | System | ✅ Create modules table |
| | | | | ✅ Columns: id (PK), learning_path_id (FK), title, description, order_index, estimated_duration_minutes |
| | | | | ✅ Foreign key to learning_paths with CASCADE delete |
| | | | | ✅ Index on: learning_path_id, order_index |
| | | | | ✅ Timestamps: created_at, updated_at |
| PBI-BE-M7-03 | | Database: Lesson Table | System | ✅ Create lessons table |
| | | | | ✅ Columns: id (PK), module_id (FK), title, content_type, content_body, video_url, file_url, duration_minutes, order_index, is_mandatory, prerequisite_lesson_id |
| | | | | ✅ Enum content_type: 'article', 'video', 'pdf', 'infographic', 'quiz' |
| | | | | ✅ Foreign key to modules with CASCADE delete |
| | | | | ✅ Self-referencing FK: prerequisite_lesson_id (nullable) |
| | | | | ✅ Index on: module_id, order_index, content_type |
| | | | | ✅ Timestamps: created_at, updated_at |
| PBI-BE-M7-04 | | Database: UserEnrollment Table | System | ✅ Create user_enrollments table |
| | | | | ✅ Columns: id (PK), user_id (FK), learning_path_id (FK), enrolled_at, completed_at, progress_percentage, total_points_earned, last_accessed_at |
| | | | | ✅ Foreign keys to users and learning_paths |
| | | | | ✅ Unique constraint on (user_id, learning_path_id) |
| | | | | ✅ Default values: progress_percentage = 0, total_points_earned = 0 |
| | | | | ✅ Index on: user_id, learning_path_id |
| PBI-BE-M7-05 | | Database: LessonProgress Table | System | ✅ Create lesson_progress table |
| | | | | ✅ Columns: id (PK), user_id (FK), lesson_id (FK), status, started_at, completed_at, time_spent_minutes, last_accessed_at |
| | | | | ✅ Enum status: 'not_started', 'in_progress', 'completed' |
| | | | | ✅ Foreign keys to users and lessons |
| | | | | ✅ Unique constraint on (user_id, lesson_id) |
| | | | | ✅ Default: status = 'not_started', time_spent_minutes = 0 |
| | | | | ✅ Index on: user_id, lesson_id, status |
| PBI-BE-M7-06 | | API: GET /learning-paths | Admin, UMKM | ✅ UMKM: return only published paths (is_published = true) |
| | | | | ✅ Admin: return all paths including drafts |
| | | | | ✅ Query params: page, limit, category, difficulty_level, product_category, target_country |
| | | | | ✅ Filter by category: general, product_specific, country_specific |
| | | | | ✅ Filter by difficulty_level: beginner, intermediate, advanced |
| | | | | ✅ For UMKM: include enrollment status (enrolled: true/false) |
| | | | | ✅ For UMKM: include progress_percentage if enrolled |
| | | | | ✅ Sort by: order_index ASC (default) |
| | | | | ✅ Response: array with pagination metadata |
| PBI-BE-M7-07 | | API: GET /learning-paths/:id | Admin, UMKM | ✅ Return complete learning path details |
| | | | | ✅ UMKM: only access if is_published = true |
| | | | | ✅ Admin: access all paths |
| | | | | ✅ Include: nested modules with lesson count |
| | | | | ✅ Include: total_modules, total_lessons count |
| | | | | ✅ For UMKM: include enrollment data if enrolled |
| | | | | ✅ For UMKM: include progress per module |
| | | | | ✅ Response success: 200 OK with path object |
| | | | | ✅ Response error: 404 Not Found |
| | | | | ✅ Response error: 403 Forbidden if unpublished and user is UMKM |
| PBI-BE-M7-08 | | API: POST /learning-paths | Admin | ✅ Endpoint accepts body: title, description, category, product_category, target_country, difficulty_level, estimated_duration_hours, thumbnail_url |
| | | | | ✅ Required fields: title, description, category, difficulty_level |
| | | | | ✅ Validate category enum values |
| | | | | ✅ Validate difficulty_level enum values |
| | | | | ✅ If category = 'product_specific', product_category is required |
| | | | | ✅ If category = 'country_specific', target_country is required |
| | | | | ✅ Default: is_published = false (draft mode) |
| | | | | ✅ Auto-assign order_index (max + 1) |
| | | | | ✅ Response success: 201 Created with path data |
| | | | | ✅ Response error: 400 Bad Request for validation errors |
| PBI-BE-M7-09 | | API: PUT /learning-paths/:id | Admin | ✅ Update learning path by id |
| | | | | ✅ Update only fields provided in body |
| | | | | ✅ Validate enum values if provided |
| | | | | ✅ Response success: 200 OK with updated data |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-10 | | API: PATCH /learning-paths/:id/publish | Admin | ✅ Toggle publish status |
| | | | | ✅ Body: is_published (boolean) |
| | | | | ✅ Validate: path has at least 1 module before publishing |
| | | | | ✅ Update is_published field |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 400 Bad Request if no modules exist |
| PBI-BE-M7-11 | | API: DELETE /learning-paths/:id | Admin | ✅ Delete learning path by id |
| | | | | ✅ Cascade delete: modules, lessons, enrollments, progress |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-12 | | API: GET /learning-paths/:path_id/modules | Admin, UMKM | ✅ Return all modules for a learning path |
| | | | | ✅ Sort by: order_index ASC |
| | | | | ✅ Include: lesson_count per module |
| | | | | ✅ For UMKM: include completion status per module |
| | | | | ✅ For UMKM: include progress_percentage per module |
| | | | | ✅ Response: array of modules |
| PBI-BE-M7-13 | | API: GET /modules/:id | Admin, UMKM | ✅ Return module details with nested lessons |
| | | | | ✅ Include: all lessons sorted by order_index |
| | | | | ✅ For UMKM: include progress status per lesson |
| | | | | ✅ For UMKM: hide lessons if prerequisite not completed |
| | | | | ✅ Response success: 200 OK with module object |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-14 | | API: POST /modules | Admin | ✅ Endpoint accepts body: learning_path_id, title, description, estimated_duration_minutes |
| | | | | ✅ Required fields: learning_path_id, title |
| | | | | ✅ Validate: learning_path_id exists |
| | | | | ✅ Auto-assign order_index (max + 1 within path) |
| | | | | ✅ Response success: 201 Created with module data |
| | | | | ✅ Response error: 400 Bad Request |
| | | | | ✅ Response error: 404 Not Found if path doesn't exist |
| PBI-BE-M7-15 | | API: PUT /modules/:id | Admin | ✅ Update module by id |
| | | | | ✅ Update only fields provided in body |
| | | | | ✅ Cannot change learning_path_id |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-16 | | API: DELETE /modules/:id | Admin | ✅ Delete module by id |
| | | | | ✅ Cascade delete: lessons, lesson progress |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-17 | | API: PATCH /modules/:id/reorder | Admin | ✅ Change order_index of module within path |
| | | | | ✅ Body: new_order_index (integer) |
| | | | | ✅ Re-calculate order_index for affected modules |
| | | | | ✅ Response success: 200 OK |
| PBI-BE-M7-18 | | API: POST /learning-paths/:id/enroll | UMKM | ✅ Enroll UMKM to learning path |
| | | | | ✅ Validate: path is published |
| | | | | ✅ Validate: user not already enrolled (check unique constraint) |
| | | | | ✅ Create UserEnrollment record |
| | | | | ✅ Set enrolled_at = now() |
| | | | | ✅ Response success: 201 Created with enrollment data |
| | | | | ✅ Response error: 409 Conflict if already enrolled |
| | | | | ✅ Response error: 403 Forbidden if path unpublished |
| PBI-BE-M7-19 | | API: GET /my-enrollments | UMKM | ✅ Return all learning paths enrolled by user |
| | | | | ✅ Query params: page, limit, status |
| | | | | ✅ Status filter: 'in_progress' (progress < 100), 'completed' (progress = 100) |
| | | | | ✅ Include: path details, progress_percentage, last_accessed_at |
| | | | | ✅ Sort by: last_accessed_at DESC (default) |
| | | | | ✅ Response: array with pagination |
| PBI-BE-M7-20 | | API: DELETE /my-enrollments/:enrollment_id | UMKM | ✅ Unenroll from learning path |
| | | | | ✅ Validate: enrollment belongs to logged-in user |
| | | | | ✅ Delete UserEnrollment record |
| | | | | ✅ Optional: keep or cascade delete LessonProgress |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 403 Forbidden if not owner |

---

## 🔴 MODUL 7B: MULTI-FORMAT CONTENT & PROGRESS TRACKING

| Kode Backlog | PIC | Backlog Title | Role | Acceptance Criteria |
|--------------|-----|---------------|------|---------------------|
| PBI-BE-M7-21 | | API: GET /modules/:module_id/lessons | Admin, UMKM | ✅ Return all lessons for a module |
| | | | | ✅ Sort by: order_index ASC |
| | | | | ✅ For UMKM: check prerequisite completion |
| | | | | ✅ For UMKM: hide lesson if prerequisite not met |
| | | | | ✅ For UMKM: include progress status per lesson |
| | | | | ✅ Include: content_type, duration_minutes, is_mandatory |
| | | | | ✅ Response: array of lessons |
| PBI-BE-M7-22 | | API: GET /lessons/:id | Admin, UMKM | ✅ Return complete lesson details |
| | | | | ✅ Include: all content fields based on content_type |
| | | | | ✅ For article: return content_body (markdown) |
| | | | | ✅ For video: return video_url |
| | | | | ✅ For pdf: return file_url |
| | | | | ✅ For UMKM: check prerequisite before allowing access |
| | | | | ✅ For UMKM: create/update LessonProgress (status = 'in_progress') |
| | | | | ✅ For UMKM: update last_accessed_at |
| | | | | ✅ Response success: 200 OK with lesson object |
| | | | | ✅ Response error: 403 Forbidden if prerequisite not met |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-23 | | API: POST /lessons | Admin | ✅ Endpoint accepts body: module_id, title, content_type, content_body, video_url, file_url, duration_minutes, is_mandatory, prerequisite_lesson_id |
| | | | | ✅ Required fields: module_id, title, content_type |
| | | | | ✅ Validate: module_id exists |
| | | | | ✅ Validate: content_type enum value |
| | | | | ✅ Validate: prerequisite_lesson_id exists and is in same module |
| | | | | ✅ Content validation based on type: |
| | | | | ✅ - article: content_body required |
| | | | | ✅ - video: video_url required |
| | | | | ✅ - pdf/infographic: file_url required |
| | | | | ✅ Auto-assign order_index (max + 1 within module) |
| | | | | ✅ Response success: 201 Created with lesson data |
| | | | | ✅ Response error: 400 Bad Request for validation errors |
| PBI-BE-M7-24 | | API: PUT /lessons/:id | Admin | ✅ Update lesson by id |
| | | | | ✅ Update only fields provided in body |
| | | | | ✅ Validate content based on content_type if changed |
| | | | | ✅ Cannot change module_id |
| | | | | ✅ Response success: 200 OK with updated data |
| | | | | ✅ Response error: 404 Not Found |
| PBI-BE-M7-25 | | API: DELETE /lessons/:id | Admin | ✅ Delete lesson by id |
| | | | | ✅ Check if any lesson has this as prerequisite |
| | | | | ✅ If yes: remove prerequisite reference or prevent delete |
| | | | | ✅ Cascade delete: lesson_progress records |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response error: 409 Conflict if is prerequisite for other lessons |
| PBI-BE-M7-26 | | API: PATCH /lessons/:id/reorder | Admin | ✅ Change order_index of lesson within module |
| | | | | ✅ Body: new_order_index (integer) |
| | | | | ✅ Re-calculate order_index for affected lessons |
| | | | | ✅ Response success: 200 OK |
| PBI-BE-M7-27 | | API: POST /lessons/:id/upload-file | Admin | ✅ Upload file for PDF/Infographic content |
| | | | | ✅ Accept: multipart/form-data with file |
| | | | | ✅ Validate: lesson content_type is 'pdf' or 'infographic' |
| | | | | ✅ Validate: file type (PDF for pdf, image for infographic) |
| | | | | ✅ Validate: file size (max 10MB for PDF, 5MB for image) |
| | | | | ✅ Upload to cloud storage (S3/GCS) or local storage |
| | | | | ✅ Update lesson.file_url with storage URL |
| | | | | ✅ Response success: 200 OK with file_url |
| | | | | ✅ Response error: 400 Bad Request for validation errors |
| PBI-BE-M7-28 | | API: POST /lessons/:id/start | UMKM | ✅ Mark lesson as started |
| | | | | ✅ Validate: user enrolled in parent learning path |
| | | | | ✅ Validate: prerequisite completed if exists |
| | | | | ✅ Create or update LessonProgress record |
| | | | | ✅ Set status = 'in_progress' if not already |
| | | | | ✅ Set started_at = now() if first time |
| | | | | ✅ Update last_accessed_at = now() |
| | | | | ✅ Response success: 200 OK with progress data |
| | | | | ✅ Response error: 403 Forbidden if prerequisite not met |
| PBI-BE-M7-29 | | API: POST /lessons/:id/complete | UMKM | ✅ Mark lesson as completed |
| | | | | ✅ Validate: user enrolled in parent learning path |
| | | | | ✅ Validate: lesson was started (status = 'in_progress') |
| | | | | ✅ Update LessonProgress: |
| | | | | ✅ - status = 'completed' |
| | | | | ✅ - completed_at = now() |
| | | | | ✅ Award points: +10 to UserEnrollment.total_points_earned |
| | | | | ✅ Trigger progress percentage recalculation |
| | | | | ✅ Response success: 200 OK with updated progress |
| | | | | ✅ Response error: 400 Bad Request if not started |
| PBI-BE-M7-30 | | API: PATCH /lessons/:id/track-time | UMKM | ✅ Update time spent on lesson |
| | | | | ✅ Body: time_spent_seconds (integer) |
| | | | | ✅ Validate: user enrolled in parent learning path |
| | | | | ✅ Update LessonProgress.time_spent_minutes (convert from seconds) |
| | | | | ✅ Increment existing time (additive) |
| | | | | ✅ Update last_accessed_at = now() |
| | | | | ✅ Response success: 200 OK |
| PBI-BE-M7-31 | | Service: Calculate Module Progress | System | ✅ Triggered after lesson completion |
| | | | | ✅ Input: user_id, module_id |
| | | | | ✅ Query: count completed lessons vs total lessons in module |
| | | | | ✅ Calculate: (completed / total) × 100 |
| | | | | ✅ Output: module_progress_percentage |
| | | | | ✅ Used for display purposes (not stored) |
| PBI-BE-M7-32 | | Service: Calculate Path Progress | System | ✅ Triggered after lesson completion |
| | | | | ✅ Input: user_id, learning_path_id |
| | | | | ✅ Query: count completed lessons vs total lessons in entire path |
| | | | | ✅ Calculate: (completed / total) × 100 |
| | | | | ✅ Update: UserEnrollment.progress_percentage |
| | | | | ✅ If progress = 100: set UserEnrollment.completed_at = now() |
| PBI-BE-M7-33 | | API: GET /lessons/:id/progress | UMKM | ✅ Get progress detail for specific lesson |
| | | | | ✅ Validate: user enrolled in parent learning path |
| | | | | ✅ Return: LessonProgress data |
| | | | | ✅ Include: status, started_at, completed_at, time_spent_minutes |
| | | | | ✅ Response success: 200 OK |
| | | | | ✅ Response: 404 Not Found if no progress record |
| PBI-BE-M7-34 | | API: GET /my-progress | UMKM | ✅ Get overall learning progress for user |
| | | | | ✅ Return: all enrollments with progress data |
| | | | | ✅ Include: path name, progress_percentage, total_points_earned |
| | | | | ✅ Include: lessons completed count, total lessons count |
| | | | | ✅ Include: total time spent across all lessons |
| | | | | ✅ Response: summary object with detailed breakdown |
| PBI-BE-M7-35 | | API: GET /learning-paths/:id/statistics | Admin | ✅ Get statistics for a learning path |
| | | | | ✅ Include: total_enrollments count |
| | | | | ✅ Include: completion_rate (% of enrollments completed) |
| | | | | ✅ Include: average_progress_percentage |
| | | | | ✅ Include: average_time_spent |
| | | | | ✅ Include: most_completed_module |
| | | | | ✅ Include: least_completed_module |
| | | | | ✅ Response: statistics object |
| PBI-BE-M7-36 | | API: GET /admin/content-analytics | Admin | ✅ Dashboard analytics for all content |
| | | | | ✅ Include: total paths, modules, lessons |
| | | | | ✅ Include: published vs draft count |
| | | | | ✅ Include: total enrollments, active learners (last 30 days) |
| | | | | ✅ Include: overall completion rate |
| | | | | ✅ Include: content by type breakdown (article, video, pdf, etc) |
| | | | | ✅ Include: average time spent per lesson type |
| | | | | ✅ Response: comprehensive analytics object |
| PBI-BE-M7-37 | | Service: Prerequisite Checker | System | ✅ Input: user_id, lesson_id |
| | | | | ✅ Query: lesson.prerequisite_lesson_id |
| | | | | ✅ If prerequisite exists: check LessonProgress.status = 'completed' |
| | | | | ✅ Output: boolean (can_access) |
| | | | | ✅ Used by: GET /lessons/:id, POST /lessons/:id/start |
| PBI-BE-M7-38 | | Service: File Storage Handler | System | ✅ Support cloud storage (S3/GCS) or local filesystem |
| | | | | ✅ Upload method: accept file, generate unique filename |
| | | | | ✅ Store in organized structure: /lessons/{lesson_id}/{filename} |
| | | | | ✅ Return public URL for access |
| | | | | ✅ Delete method: remove file from storage |
| | | | | ✅ Used by: upload/delete file endpoints |
| PBI-BE-M7-39 | | API: GET /lessons/:id/download | UMKM | ✅ Download PDF/document file |
| | | | | ✅ Validate: user enrolled in parent learning path |
| | | | | ✅ Validate: content_type is 'pdf' or 'infographic' |
| | | | | ✅ Track download: increment download_count (optional) |
| | | | | ✅ Return: file stream or redirect to file_url |
| | | | | ✅ Response headers: Content-Disposition for download |
| | | | | ✅ Response error: 403 Forbidden if not enrolled |
| PBI-BE-M7-40 | | API: GET /search/content | Admin, UMKM | ✅ Search across all learning content |
| | | | | ✅ Query param: q (search query, required) |
| | | | | ✅ Query params: content_type, difficulty_level (filters) |
| | | | | ✅ Search in: path titles, module titles, lesson titles, lesson content |
| | | | | ✅ UMKM: search only published content |
| | | | | ✅ Admin: search all content |
| | | | | ✅ Return: mixed results (paths, modules, lessons) with type indicator |
| | | | | ✅ Sort by: relevance score |
| | | | | ✅ Response: array with pagination |

---

## 📊 SUMMARY MODUL 7 (Features 7.1 & 7.2)

| Sub-Modul | Jumlah Backlog | Komponen Utama |
|-----------|----------------|----------------|
| 🔵 M7A: Learning Path Management | 20 items | Path/Module CRUD, Enrollment System, Reordering |
| 🔴 M7B: Multi-Format Content | 20 items | Lesson CRUD, File Upload, Progress Tracking, Analytics |
| **TOTAL M7** | **40 items** | |

---

## 📊 DATABASE TABLES SUMMARY

| Table Name | Purpose | Key Relationships |
|------------|---------|-------------------|
| `learning_paths` | Main learning curriculum | Parent to modules |
| `modules` | Chapter/section grouping | Parent to lessons, Child of paths |
| `lessons` | Individual content pieces | Child of modules, Self-referencing (prerequisite) |
| `user_enrollments` | Track UMKM enrollment | Links users to paths |
| `lesson_progress` | Track lesson completion | Links users to lessons |

---

## 🔗 API ENDPOINTS SUMMARY

### Learning Paths (10 endpoints)
- `GET /learning-paths` - List all paths
- `GET /learning-paths/:id` - Get path details
- `POST /learning-paths` - Create path (Admin)
- `PUT /learning-paths/:id` - Update path (Admin)
- `PATCH /learning-paths/:id/publish` - Publish/unpublish (Admin)
- `DELETE /learning-paths/:id` - Delete path (Admin)
- `POST /learning-paths/:id/enroll` - Enroll to path (UMKM)
- `GET /my-enrollments` - List enrollments (UMKM)
- `DELETE /my-enrollments/:id` - Unenroll (UMKM)
- `GET /learning-paths/:id/statistics` - Path analytics (Admin)

### Modules (7 endpoints)
- `GET /learning-paths/:path_id/modules` - List modules
- `GET /modules/:id` - Get module details
- `POST /modules` - Create module (Admin)
- `PUT /modules/:id` - Update module (Admin)
- `DELETE /modules/:id` - Delete module (Admin)
- `PATCH /modules/:id/reorder` - Reorder module (Admin)

### Lessons (15 endpoints)
- `GET /modules/:module_id/lessons` - List lessons
- `GET /lessons/:id` - Get lesson details
- `POST /lessons` - Create lesson (Admin)
- `PUT /lessons/:id` - Update lesson (Admin)
- `DELETE /lessons/:id` - Delete lesson (Admin)
- `PATCH /lessons/:id/reorder` - Reorder lesson (Admin)
- `POST /lessons/:id/upload-file` - Upload file (Admin)
- `POST /lessons/:id/start` - Start lesson (UMKM)
- `POST /lessons/:id/complete` - Complete lesson (UMKM)
- `PATCH /lessons/:id/track-time` - Track time (UMKM)
- `GET /lessons/:id/progress` - Get progress (UMKM)
- `GET /lessons/:id/download` - Download file (UMKM)
- `GET /my-progress` - Overall progress (UMKM)

### Admin Analytics (2 endpoints)
- `GET /admin/content-analytics` - Overall analytics
- `GET /search/content` - Search content

---

## 🎯 KEY TECHNICAL HIGHLIGHTS

### Content Type Validation
```javascript
// Validation rules per content type
content_type: 'article'  → content_body required
content_type: 'video'    → video_url required  
content_type: 'pdf'      → file_url required
content_type: 'infographic' → file_url required
content_type: 'quiz'     → handled separately
```

### Progress Calculation
```javascript
// Module progress
module_progress = (completed_lessons / total_lessons_in_module) × 100

// Path progress  
path_progress = (completed_lessons / total_lessons_in_path)