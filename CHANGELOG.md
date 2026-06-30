# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.1 - (Unreleased)

### Added

- Added this `CHANGELOG.md` file using Keep a Changelog structure.

### Changed

- Updated questionnaire admin behaviour so new questionnaire versions inherit `sort_order`.
- Prevented editing of older questionnaire versions in admin workflows.
- Changed the mouse cursor to pointer on the version string for easier discoverability.

### Fixed

- Fixed UI behaviour to display `updated_at` instead of `created_at`.
- Fixed Prince XML licence filename handling and read-permission behaviour.
- Fixed test configuration to use the default staticfiles backend and resolved related test regressions.

