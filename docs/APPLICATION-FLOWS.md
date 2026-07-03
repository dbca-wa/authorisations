# Authorisations Codebase User-Facing Flows

## Key Findings

### Authentication
- **SSO-based**: Uses `dbca_utils.middleware.SSOLoginMiddleware` (DBCA's single sign-on)
- **No standalone login/registration**: All auth handled externally
- Django REST Framework configured with `SessionAuthentication` and `IsAuthenticated` permission class globally
- All API endpoints require authenticated users by default
- CSRF protection using custom header `X-CsrfToken` (configurable)

### Routes & Pages (Frontend React Router)

#### Main Authenticated Routes:
1. **`/my-applications`** - MyApplications component
   - Lists all user's applications with sorting options
   - Shows application status timeline and metadata
   - Download button for submitted/approved applications
   
2. **`/new-application`** - NewApplication component
   - Create new applications
   - Process-centric UI: processes grouped with questionnaires as tabs
   - Shows questionnaire version info
   
3. **`/assessment`** - ApplicationAssessment component
   - Reviewer-only (conditionally shown via `can_review` flag)
   - Shows assessment queue for applications in SUBMITTED/UNDER_REVIEW/ACTION_REQUIRED/UNDER_ASSESSMENT
   - Sorted by status priority, then oldest first (FIFO)
   
4. **`/a/:key`** - FormLayout component
   - Edit/view individual application form
   - Multi-step questionnaire form with review page
   - Can edit if status = DRAFT, otherwise read-only
   - File attachment upload/delete
   
5. **`/settings`** - Settings page
6. **`/feedback`** - mailto: external link (handled by sidebar, not React Router)

#### Backend Django Views (not SPA):
- `GET /` → Redirect to `/my-applications`
- `GET /my-applications`, `/new-application`, `/assessment`, `/settings` → Render `vite.html` (SPA entry point)
- `GET /a/<uuid:key>` → resume_application() - checks ownership, renders vite.html
- `GET /d/<uuid:appKey>` → download_application() - PDF download (checks `has_access`)
- `GET /d/<uuid:appKey>/<uuid:attachmentKey>` → download_attachment() - file download (checks `has_access`)

### API Endpoints (REST Framework)

**Base URL**: `/api/`  
**Authentication**: All require `SessionAuthentication` (authenticated user in session)

#### 1. **Processes** - `/processes`
- GET (list): All processes, annotated with `can_review` flag for current user
- GET (detail by slug): Single process
- Response includes: id, slug, name, description, image_url, image_credit, sort_order, reviewer_groups, can_review

#### 2. **Questionnaires** - `/questionnaires`
- GET (list): Latest questionnaire versions only, ordered by process/questionnaire sort_order
- GET (detail by id): Full questionnaire with document schema
- Response includes: id, code, version, name, process_slug, sort_order, document (JSON form schema), created_at

#### 3. **Applications** - `/applications`
- GET (list): Current user's applications only (filtered by `owner=user`)
- GET (detail by key): Single application (ownership checked)
- POST (create): Create new application
  - Body: `process_slug`, `questionnaire_id`, `questionnaire_code`, `questionnaire_version`
- PUT (update): Full replacement of document answers
- PATCH (partial update): Update status to SUBMITTED (triggers `submitted_at` timestamp)
- Response includes: key, internal_id, questionnaire_id, process_slug, status, document, created_at, updated_at, owner

#### 4. **Attachments** - `/attachments`
- GET (list filtered): By `application_key` query param, ownership checked
- GET (detail by key): Single attachment (soft-deleted = False, ownership checked)
- POST (create): Upload file with metadata
  - Multipart form-data: application_key, name, question, file
  - Response: key, name, file, created_at
- PATCH (partial update): Rename attachment
- DELETE (soft delete): Mark `is_deleted=True`

#### 5. **Assessment** (Reviewers only) - `/assessment`
- GET (list): Applications in review queue for processes user can review (via group membership)
- GET (detail by key): Single application from queue
- PATCH (partial update): Update application status during review
- Response includes: same as Application + assessment-specific fields

### Interaction Points (Data Submission)

#### 1. **Application Creation Flow**
```
User: Click "Start a New Application" 
  → Browse processes & questionnaires
  → Click "Start" button on questionnaire
  → POST /api/applications {process_slug, questionnaire_id, ...}
  → Navigate to /a/{key} form
```

#### 2. **Application Draft Saving**
```
User: Fill form sections
  → Auto-save on section completion or user click "Save"
  → PUT /api/applications/{key} {document: {...}}
  → Snackbar confirmation
```

#### 3. **File Attachment Upload**
```
User: Click file input in form
  → POST /api/attachments (multipart)
  → onUploadProgress callback updates progress bar
  → New attachment appended to form field
  → Can rename via PATCH /api/attachments/{key}
  → Can delete via DELETE /api/attachments/{key}
```

#### 4. **Application Submission**
```
User: Complete all steps + review page
  → Tick confirmation checkbox
  → Click "Submit Application"
  → PATCH /api/applications/{key} {status: "SUBMITTED"}
  → Status updates, form becomes read-only
  → Application appears in /assessment for reviewers
```

#### 5. **Assessment/Review Flow** (Reviewers)
```
Reviewer: Navigate to /assessment
  → See applications in SUBMITTED/UNDER_REVIEW/ACTION_REQUIRED/UNDER_ASSESSMENT
  → Click to view full application
  → PATCH /api/applications/{key} {status: "UNDER_REVIEW"} (or next status)
  → Application moves through review queue
```

### Public vs Authenticated Endpoints

**All REST API endpoints are AUTHENTICATED** (default DRF permission class: `IsAuthenticated`)

**Public/Template Endpoints** (no auth check):
- `GET /` - redirect
- `GET /my-applications`, `/new-application`, `/assessment`, `/settings` - generic_template() returns vite.html with config (CSRF token injected)
- Note: These render SPA shell; actual API calls in SPA require authentication

**Authentication Enforcement Points**:
- ViewSets: Default queryset filtering by `owner=request.user` or process reviewer groups
- Views: `resume_application()` checks `application.owner == request.user`
- Views: `download_application()` and `download_attachment()` check `application.has_access(user)`

### CSRF Protection
- **Mechanism**: CSRF token in session (`CSRF_USE_SESSIONS = True`)
- **Client**: Axios config includes `xsrfHeaderName`, `xsrfCookieName`
- **Token Injection**: ConfigManager extracts token from DOM element on page load
- **Header**: Custom configurable header (default: `X-CsrfToken`)

### Permissions Model
- **Applicants**: Can create applications, edit DRAFT status, view own submitted/completed applications
- **Reviewers** (group-based): Can view assessment queue for assigned processes, update application status
- **Ownership**: Each application tied to `owner` (User who created it)
- **Group-Based Access**: Process has `assessor_groups` M2M; users in these groups can review that process

---

**See [README.md](README.md) for the documentation index.**
