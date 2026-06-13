---
title: Home
hide:
  - navigation
---

<div class="pinergy-hero" markdown>

![Pinergy for Home Assistant](assets/brand/logo.png#only-light){ width="360" }
![Pinergy for Home Assistant](assets/brand/dark_logo.png#only-dark){ width="360" }

<p class="pinergy-tagline">Monitor your Pinergy prepay electricity account from Home Assistant.</p>

</div>

[Pinergy](https://www.pinergy.ie/) is an Irish prepay energy provider. This unofficial
[Home Assistant](https://www.home-assistant.io/) custom integration polls the Pinergy
smart-meter API (via [`pypinergy`](https://pypi.org/project/pypinergy/)) every 30 minutes and
exposes your **credit balance**, **energy usage**, and **meter status** as native entities —
ready for dashboards, automations, and the
[Energy Dashboard](https://www.home-assistant.io/home-energy-management/).

!!! note "Unofficial integration"
    This project is not affiliated with, endorsed by, or supported by Pinergy. It is a
    community effort built on the public Pinergy app API.

## What you get

<div class="grid cards" markdown>

-   :material-cash-multiple: __Credit & runway__

    Current balance, estimated days remaining, and the amount of your last top-up.

-   :material-flash: __Usage & cost__

    Energy consumed and money spent for today, this week, and this month.

-   :material-power-plug: __Meter status__

    Power, emergency credit, low-credit, and pending top-up binary sensors.

-   :material-bell-ring: __Events__

    Fire automations the instant a top-up lands or the meter reports a new reading.

-   :material-chart-areaspline: __Energy Dashboard__

    Daily history backfills into long-term statistics, accurate across HA downtime.

-   :material-tune: __Configurable__

    Tune the polling interval and toggle "average home" comparisons.

</div>

## Get started

<div class="grid cards" markdown>

-   :material-download: __[Install](getting-started/installation.md)__

    Add the integration through HACS or manually.

-   :material-cog: __[Configure](getting-started/configuration.md)__

    Connect your Pinergy account and sign in.

-   :material-format-list-bulleted: __[Entities](user-guide/entities.md)__

    Browse every sensor, binary sensor, and event.

-   :material-sitemap: __[Architecture](architecture/index.md)__

    Understand how the integration is built.

</div>

## At a glance

| | |
|---|---|
| **Domain** | `pinergy` |
| **Integration type** | Service (cloud polling) |
| **Config** | UI config flow — no YAML |
| **Default poll interval** | 30 minutes (configurable, 10–1440) |
| **Minimum Home Assistant** | 2025.1 |
| **Backing client** | [`pypinergy`](https://pypi.org/project/pypinergy/) |
| **Platforms** | `sensor`, `binary_sensor`, `event` |
