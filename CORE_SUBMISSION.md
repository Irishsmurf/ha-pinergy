# Submitting Pinergy to Home Assistant core

This branch holds the Home Assistant **core-ready** version of the integration. The code under
`custom_components/pinergy/` is written to core conventions (UI config flow with reauth,
`DataUpdateCoordinator`, `entry.runtime_data`, `_attr_has_entity_name`, stable unique IDs,
`quality_scale.yaml` at Bronze, identical `strings.json` / `translations/en.json`, diagnostics with
redaction, full test coverage).

Once merged into [`home-assistant/core`](https://github.com/home-assistant/core) the integration
becomes a *built-in* integration and is no longer a "custom component".

## The one custom-component-only field: `manifest.json` → `version`

Home Assistant **requires** a `version` key for integrations loaded from `custom_components/` (the
loader blocks them otherwise), but **forbids** it for built-in integrations (hassfest rejects it).
The same conflict applies to `issue_tracker` (core generates the link automatically — already removed
here).

So `version` is kept here only so the repo loads and its test suite runs. When copying into core,
**delete the `version` line**. Everything else in `manifest.json` is already core-correct
(`documentation` points at `https://www.home-assistant.io/integrations/pinergy`, `quality_scale` is
`bronze`).

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
