# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Home Assistant custom integration (HACS) for Pinergy, an Irish prepay energy provider, built on the `pypinergy` API client.

## Critical constraints

- `pypinergy` is **synchronous** (requests-based). Never call a `PinergyClient` method directly from async code — always wrap with `await hass.async_add_executor_job(...)`.
- Targets HA 2025.1+ APIs: `entry.runtime_data` (no `hass.data`), coordinator `_async_setup`, `_get_reauth_entry()` / `async_update_reload_and_abort()`.

## Deliberate design decisions (not bugs)

- Monetary sensors use `state_class: total` — HA forbids `measurement`/`total_increasing` with `device_class: monetary`.
- The `power` binary sensor is inverted relative to the API: `is_on = not balance.power_off` (on = supply connected), matching POWER device-class semantics.
- Token expiry surfaces in two forms: `PinergyAuthError` (HTTP 401) or `PinergyAPIError` whose message mentions the auth token (the API reports expiry as HTTP 200 `success: false` with "Auth_token is not correct."). On either, the coordinator re-logins via `client.login()` and retries once (token expiry self-heals) before raising `ConfigEntryAuthFailed`. Never use `client.logout()` to force a re-login — pypinergy's `logout()` discards the stored credentials, making any later `login()` fail.

## Gotchas

- `custom_components/pinergy/strings.json` and `custom_components/pinergy/translations/en.json` must stay identical — update both.
- `pypinergy` is installed locally as an editable package from `~/dev/pypinergy`, which may lag PyPI. The manifest pin must always reference a version published on PyPI.

## Releases

Use `/release` or `gh release create vX.Y.Z`. The Release workflow stamps `manifest.json` with the tag version and attaches `pinergy.zip` to the release — never hand-bump the manifest version for a release.

## Tests

Run with `pytest`. Fixtures in `tests/conftest.py` mock `PinergyClient` and build real `pypinergy` dataclasses (`build_login_response`, `build_balance_response`, `build_usage_response`) — extend those builders rather than creating ad-hoc mocks.

### Local dev env

`requirements_test.txt` pins `pytest-homeassistant-custom-component>=0.13.205`, whose modern Home Assistant requires **Python 3.13** — install it (e.g. `pyenv install 3.13.x`) and use a project `.venv`; older Python silently caps the plugin at a 0.12.x release that pulls an ancient HA. CI (`.github/workflows/validate.yml`) already runs Python 3.13 on `ubuntu-latest`.

On Debian bullseye (and other OSes with system SQLite < 3.40.1) the HA recorder refuses to start. Work around it **locally only** by `pip install pysqlite3-binary` and adding a `.venv/.../site-packages/sitecustomize.py` that does `sys.modules["sqlite3"] = pysqlite3`. Keep this in the gitignored `.venv` — never commit it; CI runs a modern OS SQLite and needs no shim.
