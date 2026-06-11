# Pinergy for Home Assistant

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

### Binary sensors

| Entity | Description |
|---|---|
| Power | Off when the supply has been disconnected |
| Emergency credit | On when the meter is drawing on emergency credit |
| Credit low | On when the balance is below your alert threshold |

**Today's usage** can be added to the Home Assistant [Energy Dashboard](https://www.home-assistant.io/home-energy-management/) as a grid consumption source.

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

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Pinergy.
