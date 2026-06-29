<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/dark_logo.png">
    <img src="assets/brand/logo.png" alt="Pinergy for Home Assistant" width="360">
  </picture>
</p>

<h1 align="center">Pinergy for Home Assistant</h1>

<p align="center">
  Monitor your <a href="https://www.pinergy.ie/">Pinergy</a> prepay electricity account &mdash; balance, usage, and meter status &mdash; from <a href="https://www.home-assistant.io/">Home Assistant</a>.
</p>

<p align="center">
  <a href="https://github.com/Irishsmurf/ha-pinergy/releases"><img src="https://img.shields.io/github/v/release/Irishsmurf/ha-pinergy?style=flat-square" alt="Release"></a>
  <a href="https://github.com/Irishsmurf/ha-pinergy/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/Irishsmurf/ha-pinergy/validate.yml?style=flat-square&label=validate" alt="Validate"></a>
  <a href="https://irishsmurf.github.io/ha-pinergy/"><img src="https://img.shields.io/badge/docs-mkdocs-526CFE?style=flat-square" alt="Documentation"></a>
</p>

---

Pinergy is an Irish prepay energy provider. This integration polls the Pinergy smart-meter API (via [`pypinergy`](https://pypi.org/project/pypinergy/)) every 30 minutes and surfaces your **credit balance**, **energy usage**, and **meter status** as native Home Assistant entities &mdash; ready for dashboards, automations, and the [Energy Dashboard](https://www.home-assistant.io/home-energy-management/).

> [!NOTE]
> This integration is being prepared for submission to Home Assistant core, where it will ship as a built-in integration. This branch holds the core-ready code (no HACS metadata). This is an unofficial integration and is not affiliated with or endorsed by Pinergy.

## ✨ Highlights

- **Credit balance & runway** &mdash; current balance, estimated days remaining, and last top-up amount.
- **Usage & cost** &mdash; energy and spend for today, this week, and this month.
- **Meter status** &mdash; power, emergency credit, low-credit, and pending top-up binary sensors.
- **Events** &mdash; fire automations the moment a top-up lands or the meter reports a new reading.
- **Energy Dashboard ready** &mdash; daily history is backfilled into long-term statistics, so it stays accurate even across Home Assistant downtime.
- **Configurable** &mdash; toggle "average home" comparisons from the options flow.

## 🚀 Quick start

### Install

This branch tracks the code submitted to Home Assistant core. Once merged, the integration will be
built in and available directly from **Settings → Devices & Services → Add Integration** with no
custom-repository step. Until then, the HACS-installable version lives on the `main` branch.

### Configure

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Pinergy** and select it.
3. Enter the email and password you use for the Pinergy app.

No `configuration.yaml` setup is required or supported.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pinergy)

## 📚 Documentation

Full documentation lives at **[irishsmurf.github.io/ha-pinergy](https://irishsmurf.github.io/ha-pinergy/)**:

| Guide | What's inside |
|---|---|
| [Installation](https://irishsmurf.github.io/ha-pinergy/getting-started/installation/) | HACS and manual install, requirements |
| [Configuration](https://irishsmurf.github.io/ha-pinergy/getting-started/configuration/) | Adding the integration, re-authentication |
| [Entities](https://irishsmurf.github.io/ha-pinergy/user-guide/entities/) | Every sensor, binary sensor, and event explained |
| [Energy Dashboard](https://irishsmurf.github.io/ha-pinergy/user-guide/energy-dashboard/) | Wiring up long-term statistics |
| [Options](https://irishsmurf.github.io/ha-pinergy/user-guide/options/) | Average home comparison toggle |
| [Troubleshooting](https://irishsmurf.github.io/ha-pinergy/user-guide/troubleshooting/) | Common issues and diagnostics |
| [Architecture](https://irishsmurf.github.io/ha-pinergy/architecture/) | How the integration is built |
| [Contributing](https://irishsmurf.github.io/ha-pinergy/contributing/) | Dev setup, tests, releases |

To preview the docs locally:

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

## 🛠️ Development

```bash
pip install -r requirements_test.txt
pytest
```

See the [Contributing guide](https://irishsmurf.github.io/ha-pinergy/contributing/) for the full workflow, coding conventions, and release process.

## ⚠️ Disclaimer

This is an unofficial, community-built integration. It is not affiliated with, endorsed by, or supported by Pinergy. "Pinergy" and related marks belong to their respective owners; the bundled brand assets are an unofficial lockup created for this project.
