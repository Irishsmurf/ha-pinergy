# Long-term statistics

The Pinergy API reports **one aggregated usage entry per day for the last seven days**. On every
coordinator refresh, the integration re-upserts that whole window as
[external statistics](https://developers.home-assistant.io/docs/core/entity/sensor/#long-term-statistics),
so the [Energy Dashboard](../user-guide/energy-dashboard.md) stays accurate across Home
Assistant downtime and today's growing value self-corrects through the day.

Two series are produced per premises:

```text
pinergy:‹premises›_energy_consumption   # kWh, has_sum
pinergy:‹premises›_energy_cost          # €,   has_sum
```

The premises number is slugified (`[^a-z0-9] → _`) to form a valid statistic ID.

## The idempotency problem

Re-importing the same seven days on every poll would double-count if each import simply added
the daily values to the running sum. External statistics carry a **cumulative `sum`**, and
re-writing a row replaces it — but only if the new `sum` is computed from the *same baseline* as
the existing rows.

The fix is `_async_baseline_sum`: before writing, it works out the cumulative sum the window
should *start* from.

```python
async def _async_baseline_sum(hass, statistic_id, window_start) -> float:
    last = await ...get_last_statistics(hass, 1, statistic_id, True, {"sum"})
    if not last:
        return 0.0
    last_row = last[statistic_id][0]
    if last_row["start"] < window_start.timestamp():
        # The window starts after everything we've recorded: continue from the last sum.
        return last_row["sum"] or 0.0
    # The window overlaps earlier rows: rebase on the sum the first overlapping
    # row started from, so re-upserts stay idempotent.
    rows = await ...statistics_during_period(...)
    first_row = rows[statistic_id][0]
    return (first_row["sum"] or 0.0) - (first_row["state"] or 0.0)
```

Two cases:

| Situation | Baseline used |
|---|---|
| The seven-day window is entirely **newer** than what's recorded | The last recorded `sum` — append cleanly. |
| The window **overlaps** rows from a previous import | `sum − state` of the first overlapping row — i.e. the sum *before* that day, so re-writing the overlapping days lands on the exact same cumulative values. |

## Building the rows

With the baseline known, the daily entries (sorted, only `available` ones) are accumulated into
running sums and written for both series:

```python
for entry in entries:
    kwh_sum += entry.kwh
    cost_sum += entry.amount
    consumption.append(StatisticData(start=entry.date, state=entry.kwh, sum=kwh_sum))
    cost.append(StatisticData(start=entry.date, state=entry.amount, sum=cost_sum))

async_add_external_statistics(hass, consumption_meta, consumption)
async_add_external_statistics(hass, cost_meta, cost)
```

- `state` is that day's value; `sum` is the cumulative running total the Energy Dashboard reads.
- Only entries flagged `available` are imported, so a not-yet-reported day is skipped rather than
  recorded as zero.
- If there are no available entries, the import returns early and writes nothing.

## Why this design

- **Backfill** — every poll re-publishes the last seven days, so gaps from downtime fill in
  retroactively.
- **Self-correction** — today's partial value is overwritten with the API's latest figure each
  refresh, converging on the authoritative number.
- **Idempotent** — the baseline rebasing means repeated imports of the same window overwrite
  rather than accumulate.

See it in action on the [Energy Dashboard](../user-guide/energy-dashboard.md) page.
