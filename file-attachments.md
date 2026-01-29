## Plan: Revised ApplicationAttachment Model & API

This plan refines the attachment system to use an integer FK to `Application.id`, supports soft deletion, and allows multiple attachments per question with configurable constraints. Filenames are not exposed in URLs or API responses.

### Steps
1. **Create `ApplicationAttachment` model**
   - Fields:
     - `id` (PK, integer)
     - `uuid` (UUID, unique, indexed, used for external reference)
     - `application` (FK to `Application.id`)
     - `question_key` (string, identifies the question in the JSON)
     - `file` (FileField, storage path: `attachments/{application.key}/{uuid}`)
     - `uploaded_at` (DateTime)
     - `is_deleted` (Boolean, default `False`, for soft deletion)
   - Ensure `uuid` is unique per entry and never reused.

2. **Register model in admin as inline within `ApplicationAdmin`**
   - For easy inspection and management.

3. **Create `ApplicationAttachmentSerializer`**
   - Validates file, question key, and ensures the question exists in the application's JSON document.
   - Exposes only the `uuid` as the reference key (not filename).
   - Enforces file type and count constraints per question (configurable).

4. **Draft API endpoints in `ApplicationViewSet`**
   - `GET /applications/{key}/attachments/`: List all non-deleted attachments for the application.
   - `GET /applications/{key}/attachments/{uuid}/`: Download a specific file (no filename in URL/response).
   - `DELETE /applications/{key}/attachments/{uuid}/`: Soft-delete (set `is_deleted=True` and remove from JSON reference).
   - `POST /applications/{key}/attachments/`: Upload a new file (with question key, enforce constraints).

5. **Update file upload logic**
   - On upload, create an `ApplicationAttachment` instance, store the file, and return the `uuid`.
   - Update the application's JSON document to reference the new attachment’s `uuid`.

6. **Add helper methods (optional)**
   - In `Application`, add methods to fetch non-deleted attachments by question key.

### Further Considerations
1. **Soft Deletion:**  
   - Never hard delete files or DB entries; use `is_deleted` flag and remove references from JSON only.
2. **Multiple Attachments per Question:**  
   - Allow multiple attachments, with per-question limits and file type constraints (enforced in serializer).
3. **No Filenames in URLs/Responses:**  
   - API responses and download URLs use only the `uuid` for identification, not the original filename.