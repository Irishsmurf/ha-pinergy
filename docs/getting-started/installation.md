# Installation

The Pinergy integration is distributed as a [HACS](https://hacs.xyz/) custom repository. You
can also install it manually.

## Requirements

- **Home Assistant 2025.1** or newer. The integration uses modern APIs
  (`entry.runtime_data`, coordinator `_async_setup`, reauth helpers) that are not available on
  older releases.
- A **Pinergy account** with smart-meter access — the same email and password you use to sign
  in to the Pinergy mobile app.
- The [`recorder`](https://www.home-assistant.io/integrations/recorder/) integration (enabled
  by default), which the long-term statistics import depends on.

## Install with HACS (recommended)

1. In HACS, open **⋮ → Custom repositories**.
2. Add `https://github.com/Irishsmurf/ha-pinergy` with category **Integration**.
3. Search for **Pinergy** in HACS and download it.
4. **Restart Home Assistant.**

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Irishsmurf&repository=ha-pinergy&category=integration)

!!! tip "Don't have HACS yet?"
    Follow the [HACS installation guide](https://hacs.xyz/docs/use/download/download/) first,
    then come back to add the custom repository.

## Manual installation

If you prefer not to use HACS:

1. Download the latest `pinergy.zip` from the
   [Releases page](https://github.com/Irishsmurf/ha-pinergy/releases), or copy the
   `custom_components/pinergy/` folder from the repository.
2. Place it so the path is `‹config›/custom_components/pinergy/` inside your Home Assistant
   configuration directory.
3. **Restart Home Assistant.**

Your directory should look like this:

```text
config/
└── custom_components/
    └── pinergy/
        ├── __init__.py
        ├── manifest.json
        ├── sensor.py
        └── ...
```

## Updating

- **HACS:** updates appear in the HACS dashboard. Download the new version and restart Home
  Assistant.
- **Manual:** replace the `custom_components/pinergy/` folder with the new release and restart.

## Next steps

Once installed and restarted, head to [Configuration](configuration.md) to connect your
Pinergy account.
