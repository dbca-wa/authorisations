# Application File Attachments: Design & Implementation Plan

This document outlines the design and implementation plan for supporting file attachments in the application management system. The approach is focused on maintainability, auditability, and efficient API usage, while supporting per-question attachments and soft deletion.

---

## Objectives

- Allow each application to have multiple file attachments, each linked to a specific question in the answer document.
- Store files securely and efficiently, with no filename or extension in the download URL.
- Support soft deletion for auditability (no hard deletes).
- Enforce per-question attachment limits and file type constraints.
- Use UUIDs for external reference and integer PKs for efficient DB lookups.
- Keep the API clean, consistent, and easy to extend.

---

## Model Design

### `ApplicationAttachment` Model

- `id`: Integer primary key (for DB efficiency).
- `uuid`: UUID (unique, indexed, used for all external references and URLs).
- `application`: ForeignKey to `Application.id` (integer PK).
- `question_key`: String, identifies the question in the JSON answer document.
- `file`: FileField, stores the file as `attachments/{application.key}/{uuid}` (no extension in storage path), but preserves the original filename in the model.
- `uploaded_at`: DateTime, when the file was uploaded.
- `is_deleted`: Boolean, default `False`. Marks soft-deleted files (never hard delete).

---

## Serializer

- Use the existing `AttachmentSerializer` for all attachment-related API actions.
- Validates:
  - File size and type (enforced via settings and per-question config).
  - That the `question_key` exists in the application's JSON document.
  - Per-question attachment count limits (configurable).
- Exposes only the `uuid` for reference in the API and JSON answers (never the filename or extension).

---

## API Endpoints

All endpoints use `{key}` (the application's UUID) for lookups:

- `GET /applications/{key}/attachments/`  
  List all non-deleted attachments for the application.

- `GET /applications/{key}/attachments/{uuid}/`  
  Download a specific file (no filename or extension in URL/response).

- `DELETE /applications/{key}/attachments/{uuid}/`  
  Soft-delete: sets `is_deleted=True` and removes the reference from the JSON answer document.

- `POST /applications/{key}/attachments/`  
  Upload a new file (with question key, enforcing per-question constraints).

---

## File Storage

- Files are stored as `attachments/{application.key}/{uuid}` (no extension).
- The original filename is preserved in the model for auditing or download headers if needed.
- Filenames and extensions are never exposed in URLs or API responses.

---

## Soft Deletion

- No files or DB entries are hard deleted.
- Soft deletion is implemented via the `is_deleted` flag.
- When an attachment is deleted, its reference is also removed from the application's JSON answer document.

---

## Multiple Attachments per Question

- Multiple attachments per question are supported.
- Per-question limits and file type constraints are enforced via configuration and serializer validation.

---

## Admin Integration

- `ApplicationAttachment` is registered as an inline within `ApplicationAdmin` for easy inspection and management.

---

## Helper Methods (Optional)

- Helper methods can be added to the `Application` model to fetch non-deleted attachments by question key.

---

## Summary

This design provides a robust, auditable, and maintainable solution for file attachments in the application system, balancing efficient DB lookups, secure file storage, and flexible API usage. All references and lookups use UUIDs for security and consistency, while integer PKs ensure DB performance. The approach is extensible for future requirements and easy to review and maintain.