# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries should be concise, single-sentence summaries without excessive technical detail. Focus on the user-facing impact rather than implementation details.

## [1.1.0] - Unreleased (Requires DB Migration)

### Added

- Added discard and revert functionality allowing applicants to abandon draft applications by moving them to DISCARDED status, with the ability to restore them back to DRAFT for continued editing.
- Added tab-based filtering system for My Applications page enabling applicants to organise applications by status category (Active, Terminated, Finalised), improving visibility of application lifecycle stages.
- Added permanent links to questionnaire types on the new application page, enabling users to share and bookmark direct links to specific application types.
- Added a full privacy statement page with section-by-section expandable content and dedicated contact details. Also updated the "Collection Notice Disclaimer" that we request applicants to acknowledge and agree prior to creating new applications.
- Added a new favicon, replacing the default placeholder.
- Added comprehensive feature development guide ([FEATURE-DEVELOPMENT.md](docs/FEATURE-DEVELOPMENT.md)) consolidating all mandatory best practices, testing requirements, code quality standards, and common commands in a single reference document for AI agents and developers.
- Added new frontend as well as E2E tests for comprehensive coverage of "New application" page functionality.
- Added formal specification of application status workflow ([STATUS-WORKFLOW.md](docs/STATUS-WORKFLOW.md)) documenting all 13 state transitions, permissions, and business rules with comprehensive test coverage across backend API (19 tests), E2E (6 tests), and frontend (10 statuses verified).
- Added submission modal displayed after successful application submission and on page load for read-only applications, providing confirmation and options to download application PDF or exit the application.
- Added technical officers review page workflow actions enabling reviewers to claim applications for review, reset applications to draft for applicant revision, and proceed applications to assessment stage with confirmation dialogs for each action.
- Added audit logging for reviewer and assessor actions, recording every application status change with user, timestamp, and status transition details in an immutable audit log accessible through the Django admin interface for regulatory compliance and investigation purposes.
- Added file size tracking and display for application attachments, automatically capturing file sizes during upload and displaying human-readable sizes (B, KB, MB) in the frontend attachment list and admin interface.

### Changed

- Renamed "Assessment" terminology to "Review" throughout the application, including API endpoints (/api/assessment → /api/review), menu navigation ("Assessment Queue" → "Review Queue"), and related components and fixtures, to align with domain conventions.
- Standardised on npm for all frontend package management across development, CI, testing, and production environments to ensure identical dependency versions and predictable builds.
- Disabled questionnaire tabs when only a single questionnaire to prevent user confusion from clicking non-functional tabs.
- Improved handling of missing files and file size display in PDF generation, showing placeholder images for missing attachments and displaying human-readable file sizes alongside filenames for all file types.

### Fixed

- Fixed submit button allowing duplicate API submissions by adding loading indicator and disabled state during submission process.
- Fixed attachment file-type icons intermittently disappearing (especially Excel) across both draft form editing and reviewer attachment views, which previously caused blank file tiles due to a static asset processing issue in production mode.

### Removed

- Removed `ACTION_REQUIRED` status; applications now use concrete workflow states (DRAFT → SUBMITTED → UNDER_REVIEW → UNDER_ASSESSMENT → decision outcomes) with explicit transition rules and permission boundaries.

## 1.0.3 - 2026-07-16

### Fixed

- Fixed session cookie collision issue in Firefox by using a distinct, host-scoped session cookie name (`authorisations_sessionid`) to prevent interference from parent-domain cookies set by sibling DBCA applications.

### Changed

- Removed redundant CSRF cookie settings (CSRF_COOKIE_NAME, CSRF_COOKIE_SAMESITE, CSRF_COOKIE_SECURE) as the application uses session-based CSRF protection instead.

## 1.0.2 - 2026-07-14

### Added

- Added attachments dialog for technical officers to view and download application files directly from the assessment queue.
- Added reusable `LoadingState` component with animated spinner for consistent loading states across all main pages.
- Added Settings page placeholder with under-construction message for future implementation.
- Added comprehensive E2E tests for assessment page attachment dialog functionality.
- Added `owner_fullname` field to application API responses (combines User's first_name and last_name).
- Added "Application type" sort option to both My Applications and Assessment pages using hierarchical sort by process and questionnaire order.
- Added `process_sort_order` field to application API responses for frontend application type sorting without additional lookups.
- Added "Submitted: Newest" and "Submitted: Oldest" sort options for applications, conditionally visible only when applications have been submitted (with `submitted_at` values). Unsubmitted applications sort to the end in submitted-date sorts.
- Added helper utilities `hasSubmittedApplications()` and `getAvailableSortOptions()` for conditional sort option visibility based on application data state.
- Added parameter-driven defaults to `getInitialSortOrder()` allowing different default sorts per page: "Updated: Newest" for My Applications, "Submitted: Oldest" for Assessment queue.

### Changed

- Tweaked the content widths to be "responsive fixed" for wide screens.
- Updated all input component error messages for improved visibility and user feedback.
- Moved all input compenent descriptions below the field for consistency.
- Removed the "Actions" column name for the grid inputs for simplicity.
- Made attachment grid display more responsive and visually consistent across different resolutions.
- Renamed `owner` field to `owner_email` in application API endpoints (`/api/applications` and `/api/assessment`) for clarity.
- Redesigned assessment card to display applicant information (name, email with copy-to-clipboard, submission date) instead of application status progression.
- Renamed application sort options to be more explicit: `newest`→`created_newest`, `oldest`→`created_oldest`, `recently_updated`→`updated_newest`, `least_recently_updated`→`updated_oldest`.
- Made application sorting logic reusable across all application listing pages through extracted utilities and reusable components.
- Add strict type checking to frontend TypeScript codebase for improved type safety and maintainability.

### Fixed

- Fixed attachment listing permissions so reviewers can see attachments for applications in processes they are authorised to review (fixes access control bug).
- Fixed attachment renaming to trim leading and trailing whitespace from filenames backend and frontend.

## 1.0.1 - 2026-07-03

### Added

- Added this `CHANGELOG.md` file using Keep a Changelog structure.
- Added one sentence project definition / description.
- Added `process_name` field to questionnaire API responses for form editor display.
- Added reusable `ApplicationIdDisplay` component for internal ID display with copy-to-clipboard functionality.

### Changed

- Updated questionnaire admin behaviour so new questionnaire versions inherit `sort_order`.
- Prevented editing of older questionnaire versions in admin workflows.
- Changed the mouse cursor to pointer on the version string for easier discoverability.
- Reorganised and tidied up the documentation.
- Removed the old Dockerfile.
- Changed the page title to display "proces name" as well for form editor display.
- **Backend dependencies:** Updated 11 packages including dbca-utils (2.2.0 → 3.0.3), cryptography, django-environ, and related dependencies. Django major version upgrade (6.0) deferred for separate handling. All 99 tests passing.
- **Frontend dependencies:** Updated 23 packages across production and development, including MUI ecosystem (@mui/x-data-grid, @mui/x-date-pickers), axios, react-router (stayed on 7.x to avoid breaking changes), and build tooling. Both `bun.lock` and `package-lock.json` synchronised. All 89 tests passing.
- See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for complete updated dependency versions.

### Fixed

- Fixed UI behaviour to display `updated_at` instead of `created_at`.
- Fixed Prince XML licence filename handling and read-permission behaviour.
- Fixed test configuration to use the default staticfiles backend and resolved related test regressions.
- Fixed layout width inconsistencies; all drawers and form containers now scale responsively across different screen sizes (mobile, lg, xl breakpoints).

