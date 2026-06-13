# Options

After the integration is set up, you can adjust its behaviour without removing and re-adding
it.

Go to **Settings → Devices & Services → Pinergy → Configure**.

| Option | Default | Range | Effect |
|---|---|---|---|
| **Update interval (minutes)** | 30 | 10–1440 | How often the Pinergy API is polled for new data. |
| **Fetch average home comparisons** | On | On/Off | Whether to fetch the "average home" usage/cost comparison each poll. |

Changing an option reloads the integration immediately so the new settings take effect on the
next refresh.

## Update interval

The default of **30 minutes** matches how often Pinergy smart meters typically report. Lowering
it makes data fresher at the cost of more API calls; raising it is gentler on the API and is
fine if you mostly look at the Energy Dashboard.

!!! tip
    The meter itself only reports periodically, so polling far more often than every 30 minutes
    rarely surfaces new readings — it mostly re-fetches the same values.

## Fetch average home comparisons

The *average home* comparison (what a similar home used/spent today) is a non-essential
insight, and it isn't available for every account type — legacy, no-WAN, and level-pay meters
may not return it.

- **On** (default): the integration fetches the comparison each poll. The
  [Average home usage/cost today](entities.md#sensors) sensors are populated (they remain
  disabled by default — enable them on the device page to see the values).
- **Off**: the comparison endpoint is skipped entirely, trimming one API call per refresh.

!!! note
    Turning comparisons off never affects balance or usage data. And even with comparisons on,
    a temporary failure of the comparison endpoint will never break the main refresh — it's
    fetched defensively and logged at debug level if unavailable.
