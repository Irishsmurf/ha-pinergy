<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/dark_logo.png">
    <img src="assets/brand/logo.png" alt="Pinergy" width="320">
  </picture>
</p>

<h1 align="center">Pinergy for Home Assistant</h1>

A custom [Home Assistant](https://www.home-assistant.io/) integration for [Pinergy](https://www.pinergy.ie/), the Irish prepay energy provider. It polls the Pinergy smart-meter API (via [pypinergy](https://pypi.org/project/pypinergy/)) every 30 minutes and exposes your credit balance, usage, and meter status as entities.

## Features

All entities belong to a single **Pinergy Account** device.

### Sensors

| Entity | Description | Unit |
|---|---|---|
| Current balance | Current credit balance | € |
| Days remaining | Estimated days until credit runs out | days |
| Last top-up amount | Amount of the most recent top-up | € |
| Today's usage | Energy consumed so far today | kWh |
| Today's cost | Cost of today's usage | € |
| This week's usage | Energy consumed so far this week | kWh |
| This week's cost | Cost of this week's usage | € |
| This month's usage | Energy consumed so far this month | kWh |
| This month's cost | Cost of this month's usage | € |
| Last meter reading | When the meter last reported | timestamp |
| Last top-up | When the most recent top-up was made (disabled by default) | timestamp |
| Average home usage today | What a similar home used today (disabled by default) | kWh |
| Average home cost today | What a similar home spent today (disabled by default) | € |

Entities marked *disabled by default* can be enabled from the Pinergy Account device page.

### Binary sensors

| Entity | Description |
|---|---|
| Power | Off when the supply has been disconnected |
| Emergency credit | On when the meter is drawing on emergency credit |
| Credit low | On when the balance is below your alert threshold |
| Pending top-up | On while a top-up is waiting to be applied to the meter |

## Energy Dashboard

The integration imports your daily usage history into Home Assistant's long-term statistics on every refresh, so the [Energy Dashboard](https://www.home-assistant.io/home-energy-management/) stays accurate even across Home Assistant downtime.

1. Go to **Settings → Dashboards → Energy**.
2. Under **Electricity grid → Add consumption**, select the **Pinergy energy consumption** statistic.
3. For cost tracking, choose **Use an entity tracking the total costs** and select **Pinergy energy cost**.

Alternatively, the **Today's usage** and **Today's cost** sensors can be used directly, but the imported statistics are recommended: they backfill the last seven days from the Pinergy API rather than relying on Home Assistant having been online.

## Installation

### HACS (recommended)

1. In HACS, open **⋮ → Custom repositories**.
2. Add `https://github.com/Irishsmurf/ha-pinergy` with category **Integration**.
3. Search for **Pinergy** in HACS and download it.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/pinergy/` into the `custom_components/` folder of your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Pinergy**.
3. Enter the email address and password you use for the Pinergy app.

No `configuration.yaml` setup is required or supported.

If your password changes, Home Assistant will prompt you to re-authenticate.

## Development

```bash
pip install -r requirements_test.txt
pytest
```

## Branding

The integration ships with brand assets under [`custom_components/pinergy/brand/`](custom_components/pinergy/brand/), mirrored in [`assets/brand/`](assets/brand/) for documentation use.

| Asset | Preview | Usage |
|---|---|---|
| Icon | <img src="assets/brand/icon.png" alt="Pinergy icon" width="64"> | Square mark shown for the integration in Home Assistant |
| Logo | <img src="assets/brand/logo.png" alt="Pinergy logo" width="160"> | Full logo for light backgrounds |
| Dark logo | <img src="assets/brand/dark_logo.png" alt="Pinergy dark logo" width="160"> | Full logo for dark backgrounds |

Each asset is provided as `.svg`, `.png`, and `@2x.png` (high-DPI) variants.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Pinergy.
