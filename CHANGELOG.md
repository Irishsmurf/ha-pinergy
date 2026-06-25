# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-06-25

### Fixed
- Specify `mean_type` in statistics metadata to resolve the Home Assistant 2026.11 `has_mean` deprecation warning, guarded so the integration still imports on older HA (2025.1+) that lack `StatisticMeanType`.

## [0.2.1] - 2026-06-12

### Added
- Updated brand logo with text.

## [0.2.0] - 2026-06-12

### Added
- Long-term statistics import for the Energy Dashboard.
- Diagnostics platform with credential redaction.
- Weekly/monthly usage, timestamp, comparison, and top-up entities.
- Options Flow for polling interval and comparisons.
- Event entities for top-ups and meter readings.

### Changed
- Compatibility update for Home Assistant 2025 OptionsFlow config_entry assignment.
- General quality-scale fixes across the integration.

## [0.1.5] - 2026-06-12

### Added
- Redesigned brand icons with a Pinergy-inspired halo mark.

## [0.1.4] - 2026-06-11

### Changed
- Self-heal expired authentication tokens during coordinator refresh.
- Bumped `pypinergy` to `0.1.7`.

## [0.1.3] - 2026-06-11

### Added
- Branding assets to integration folder.

## [0.1.2] - 2026-06-11

### Changed
- Bumped `pypinergy` to `0.1.6`.

## [0.1.1] - 2026-06-11

### Added
- Emoji-based brand icons.
- Claude Code configuration, ruff isort convention, and lint fixes.

## [0.1.0] - 2026-06-11

### Added
- Initial release of the Pinergy integration.
