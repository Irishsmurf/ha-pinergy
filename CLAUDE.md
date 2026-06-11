# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Home Assistant custom integration (HACS) for Pinergy, an Irish prepay energy provider, built on the `pypinergy` API client.

## Critical constraints

- `pypinergy` is **synchronous** (requests-based). Never call a `PinergyClient` method directly from async code — always wrap with `await hass.async_add_executor_job(...)`.
- Targets HA 2025.1+ APIs: `entry.runtime_data` (no `hass.data`), coordinator `_async_setup`, `_get_reauth_entry()` / `async_update_reload_and_abort()`.

## Deliberate design decisions (not bugs)

- Monetary sensors use `state_class: total` — HA forbids `measurement`/`total_increasing` with `device_class: monetary`.
- The `power` binary sensor is inverted relative to the API: `is_on = not balance.power_off` (on = supply connected), matching POWER device-class semantics.
- On `PinergyAuthError` during refresh, the coordinator logs out and retries once (token expiry self-heals) before raising `ConfigEntryAuthFailed`.

## Gotchas

- `custom_components/pinergy/strings.json` and `custom_components/pinergy/translations/en.json` must stay identical — update both.
- `pypinergy` is installed locally as an editable package from `~/dev/pypinergy`, which may lag PyPI. The manifest pin must always reference a version published on PyPI.

## Releases

Use `/release` or `gh release create vX.Y.Z`. The Release workflow stamps `manifest.json` with the tag version and attaches `pinergy.zip` to the release — never hand-bump the manifest version for a release.

## Tests

Run with `pytest`. Fixtures in `tests/conftest.py` mock `PinergyClient` and build real `pypinergy` dataclasses (`build_login_response`, `build_balance_response`, `build_usage_response`) — extend those builders rather than creating ad-hoc mocks.
