# Changelog

All notable changes to MobileClaw Daily are documented in this file.

## [1.0.1] - 2026-11-24

### Fixed

- Scheduled GitHub Actions runs now skip the claim cleanly when no credential
  Secret is configured instead of reporting a configuration failure.
- Added an explicit credentials preflight while keeping script failures fatal
  whenever credentials are present.
- Synchronized the Chinese README and all five translated guides with the
  workflow behavior.

## [1.0.0] - 2026-11-23

### Added

- Standalone MobileClaw daily token welfare runner.
- Multi-account Bearer token and Cookie credential parsing.
- `status -> claim -> status / credits` server-side readback flow.
- Ineligible classification for unregistered and real-name verification cases.
- Per-account JSON output plus a final aggregate summary.
- Windows, Linux, Qinglong, and GitHub Actions deployment documentation.
- GitHub Actions tests on push and a single daily scheduled claim run.
- Chinese README, five translated guides, usage policy, and third-party notices.
- Donation QR assets, MIT license, and project metadata.
