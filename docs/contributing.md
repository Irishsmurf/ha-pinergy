# Contributing

Contributions are welcome. This page covers local setup, the conventions the codebase follows,
and how releases are cut.

## Development setup

```bash
git clone https://github.com/Irishsmurf/ha-pinergy.git
cd ha-pinergy
pip install -r requirements_test.txt
pytest
```

The integration depends on [`pypinergy`](https://pypi.org/project/pypinergy/). During
development it may be installed as an editable package from a local checkout, which can lag
PyPI.

!!! warning "Keep the manifest pin on a published version"
    `manifest.json`'s `requirements` pin must always reference a `pypinergy` version that is
    **published on PyPI**, even if you're developing against a newer local editable build.

## Tests

Run the suite with:

```bash
pytest
```

Fixtures in `tests/conftest.py` mock `PinergyClient` and build **real** `pypinergy` dataclasses
through helper builders:

- `build_login_response`
- `build_balance_response`
- `build_usage_response`

!!! tip "Extend the builders, don't mock ad-hoc"
    When you need new test data, extend these builders rather than hand-rolling mock objects.
    Tests then exercise the same dataclasses the integration sees at runtime.

## Coding conventions

The project tracks Home Assistant core conventions. A few that are easy to trip on:

- **Never call `pypinergy` from the event loop.** It's synchronous (`requests`-based); always
  wrap calls in `await hass.async_add_executor_job(...)`.
- **Target HA 2025.1+ APIs:** `entry.runtime_data`, coordinator `_async_setup`,
  `_get_reauth_entry()` / `async_update_reload_and_abort()`.
- **Declarative entities.** Add a metric by appending an `EntityDescription` with a `value_fn`
  (and optional `available_fn`) — see [`sensor.py`](architecture/index.md#components).
- **Lint with Ruff.** The selected rule sets are `E, F, I, UP, B, SIM`, target `py312`, with
  `homeassistant` treated as first-party imports (matching HA core import ordering).

### Translations must stay in sync

`custom_components/pinergy/strings.json` and `custom_components/pinergy/translations/en.json`
**must stay identical**. When you change one, change the other.

### Respect the deliberate design decisions

Several things that look like bugs are intentional — read
[Architecture](architecture/index.md) before "fixing" them:

- Monetary sensors use `state_class: total` (HA forbids `measurement`/`total_increasing` with
  `device_class: monetary`).
- The **Power** binary sensor is inverted: `is_on = not power_off`.
- Token expiry self-heals via `client.login()` + one retry. **Never use `client.logout()`** to
  force a re-login — it discards stored credentials. See
  [Data updates & auth](architecture/data-updates.md#token-expiry-the-re-login-retry).

## Documentation

This site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). To work
on it:

```bash
pip install -r docs/requirements.txt
mkdocs serve     # live preview at http://127.0.0.1:8000
mkdocs build     # build the static site into ./site
```

Docs live in `docs/`, with navigation defined in `mkdocs.yml`. The site auto-deploys to GitHub
Pages on every push to `main` via the `Docs` workflow.

## Continuous integration

Pull requests run the **Validate** workflow:

- **Hassfest** — Home Assistant's manifest/structure validation.
- **HACS** — HACS repository validation.
- **Tests** — `pytest` on Python 3.13.

Please make sure these pass before requesting review.

## Releases

Releases are tag-driven — **never hand-bump the manifest version**.

1. Create a release tag, e.g. `gh release create vX.Y.Z` (or use the `/release` helper).
2. The **Release** workflow stamps `manifest.json` with the tag version and attaches
   `pinergy.zip` to the GitHub release.

HACS and manual installers then pick up the new version.

## Reporting issues

Open issues at
[github.com/Irishsmurf/ha-pinergy/issues](https://github.com/Irishsmurf/ha-pinergy/issues).
Include your Home Assistant and integration versions, reproduction steps, and a redacted
[diagnostics file](user-guide/troubleshooting.md#collecting-diagnostics) where relevant.
