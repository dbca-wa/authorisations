# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

