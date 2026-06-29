# Submitting Pinergy to Home Assistant core

This branch holds the Home Assistant **core-ready** version of the integration. The code under
`custom_components/pinergy/` is written to core conventions (UI config flow with reauth,
`DataUpdateCoordinator`, `entry.runtime_data`, `_attr_has_entity_name`, stable unique IDs,
`quality_scale.yaml` at Bronze, identical `strings.json` / `translations/en.json`, diagnostics with
redaction, full test coverage).

Once merged into [`home-assistant/core`](https://github.com/home-assistant/core) the integration
becomes a *built-in* integration and is no longer a "custom component".

## `manifest.json` edits to apply when copying into core

Two fields differ between a `custom_components/` integration and a built-in one, because hassfest
validates them differently depending on where the code lives. They are kept in their
custom-component form here so this repo loads and passes its own CI, and **must be changed when the
code is copied into `homeassistant/components/pinergy/`**:

1. **`version`** — required for `custom_components/` (the loader blocks integrations without it) but
   **forbidden** for built-in integrations (hassfest rejects it). **Delete the `version` line.**
2. **`documentation`** — for a custom integration hassfest requires it to point at the custom repo
   (`https://github.com/Irishsmurf/ha-pinergy`); for core it must point at
   **`https://www.home-assistant.io/integrations/pinergy`**. **Change the URL.**

Everything else is already core-correct: `quality_scale` is `bronze`, and `issue_tracker` has been
removed (core generates that link automatically).

## Steps to open the core submission

1. **Brands** — open a PR to [`home-assistant/brands`](https://github.com/home-assistant/brands)
   adding `pinergy` `logo`/`icon` assets (the artwork previously under
   `custom_components/pinergy/brand/`, still available on the `main` branch and in git history).
   hassfest's brands check fails until this is merged.
2. **Documentation** — open a PR to
   [`home-assistant/home-assistant.io`](https://github.com/home-assistant/home-assistant.io) adding
   `source/_integrations/pinergy.markdown` with a high-level description, installation, configuration
   parameters, and removal instructions (satisfies the Bronze `docs-*` rules).
3. **Library** — confirm `pypinergy` meets the core library requirements: published on PyPI
   (`1.2.0`), open-source and licensed, minimal transitive dependencies, and no network/IO at import
   time. The synchronous client is acceptable because every call is wrapped with
   `hass.async_add_executor_job(...)`.
4. **Core** — copy `custom_components/pinergy/*` → `homeassistant/components/pinergy/` and
   `tests/*` → `tests/components/pinergy/`, delete the manifest `version` line, then open the
   new-integration PR. Keep the PR minimal and focused per the core review checklist.
