# Architecture overview

The Pinergy integration is a thin, well-typed layer between Home Assistant and the synchronous
[`pypinergy`](https://pypi.org/project/pypinergy/) API client. It follows current Home Assistant
conventions (targeting **2025.1+**): `entry.runtime_data`, a `DataUpdateCoordinator` with
`_async_setup`, and the modern reauth helpers.

## Components

```text
custom_components/pinergy/
├── __init__.py        # Setup/unload, platform forwarding, runtime_data wiring
├── config_flow.py     # UI config + reauth + options flows
├── coordinator.py     # Polling, auth refresh, data container
├── statistics.py      # Long-term statistics import (idempotent upsert)
├── entity.py          # Shared base entity → "Pinergy Account" device
├── sensor.py          # 13 sensors (declarative descriptions + value_fn)
├── binary_sensor.py   # 4 status binary sensors
├── event.py           # Top-up & meter-reading event entities
├── diagnostics.py     # Redacted diagnostics download
├── const.py           # Domain, defaults, option keys
├── manifest.json      # Metadata, requirements, version
├── strings.json       # UI/entity translations (source of truth)
└── translations/en.json  # Must mirror strings.json
```

## How a refresh flows

```text
        ┌────────────────────────────────────────────────┐
        │ async_setup_entry (__init__.py)                 │
        │  • build PinergyClient(email, password)         │
        │  • create coordinator                           │
        │  • async_config_entry_first_refresh()           │
        │  • store coordinator in entry.runtime_data      │
        │  • forward platforms (sensor/binary_sensor/event)│
        └───────────────────────┬────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────────────┐
        │ PinergyDataUpdateCoordinator                    │
        │  _async_setup:  client.login() → login_response │
        │  _async_update_data every N minutes:            │
        │    1. _fetch (in executor):                     │
        │         get_balance(), get_usage(),             │
        │         compare_usage()  ← optional, defensive  │
        │    2. async_insert_statistics(...)              │
        │    3. return PinergyData(balance, usage, compare)│
        └───────────────────────┬────────────────────────┘
                                 │  coordinator.data
                                 ▼
        ┌────────────────────────────────────────────────┐
        │ Entities (CoordinatorEntity)                    │
        │  read coordinator.data via value_fn / is_on_fn  │
        └────────────────────────────────────────────────┘
```

## Key design choices

The integration encodes several deliberate decisions worth knowing before changing code:

- **`pypinergy` is synchronous.** Every client call is wrapped in
  `hass.async_add_executor_job(...)`; it is never awaited or called directly from the event
  loop.
- **`runtime_data`, not `hass.data`.** The coordinator lives on the typed config entry
  (`PinergyConfigEntry = ConfigEntry[PinergyDataUpdateCoordinator]`).
- **Declarative entities.** Sensors and binary sensors are tuples of frozen
  `EntityDescription` subclasses carrying a `value_fn`/`is_on_fn` (and optional
  `available_fn`), so adding a metric is a one-entry change.
- **Single device.** Every entity attaches to one "Pinergy Account" device keyed by premises
  number (see [`entity.py`](index.md#components)).
- **Resilient extras.** The comparison endpoint and the statistics import are both treated as
  non-essential: a failure in either is caught and logged, never allowed to take entities down.

The next pages dig into the two areas with the most subtlety:

- [Data updates & auth](data-updates.md) — polling, token expiry, and the re-login retry.
- [Long-term statistics](statistics.md) — the idempotent seven-day upsert.
