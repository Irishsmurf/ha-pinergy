# Energy Dashboard

The integration imports your daily usage history into Home Assistant's
[long-term statistics](https://developers.home-assistant.io/docs/core/entity/sensor/#long-term-statistics)
on every refresh, so the [Energy Dashboard](https://www.home-assistant.io/home-energy-management/)
stays accurate **even across Home Assistant downtime**.

Two external statistics are produced per account:

| Statistic | Measures | Unit |
|---|---|---|
| **Pinergy energy consumption** | Daily electricity consumption | kWh |
| **Pinergy energy cost** | Daily electricity cost | € |

## Add to the Energy Dashboard

1. Go to **Settings → Dashboards → Energy**.
2. Under **Electricity grid → Add consumption**, select the **Pinergy energy consumption**
   statistic.
3. For cost tracking, choose **Use an entity tracking the total costs** and select **Pinergy
   energy cost**.

It can take up to two hours for the Energy Dashboard to render newly added statistics — this is
a Home Assistant behaviour, not specific to this integration.

## Why statistics instead of the live sensors?

You *can* point the Energy Dashboard at the **Today's usage** and **Today's cost** sensors
directly, but the imported statistics are recommended because:

- **They backfill.** The Pinergy API returns the **last seven days** of daily usage on every
  refresh, so gaps from Home Assistant being offline are filled in retroactively.
- **They self-correct.** Today's value grows through the day; each refresh re-upserts the
  window, so the figure converges to the API's authoritative number rather than depending on
  Home Assistant having sampled the sensor continuously.

!!! info "How the import stays idempotent"
    Re-importing the same seven-day window on every poll could double-count. The integration
    rebases each window on the cumulative sum recorded *before* the window started, so repeated
    imports overwrite rather than accumulate. The mechanics are covered in
    [Long-term statistics](../architecture/statistics.md).

## Statistic IDs

The statistic IDs are derived from your premises number, in the form:

```text
pinergy:‹premises›_energy_consumption
pinergy:‹premises›_energy_cost
```

You normally never need these — select the friendly names ("Pinergy energy consumption" /
"Pinergy energy cost") in the dashboard picker — but they're useful when inspecting data under
**Developer Tools → Statistics**.
