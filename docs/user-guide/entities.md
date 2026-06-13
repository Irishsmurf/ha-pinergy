# Entities

Every entity belongs to a single **Pinergy Account** device. All entities use
`has_entity_name`, so they appear as *Pinergy Account &lt;name&gt;* in the UI.

There are three platforms: [sensors](#sensors), [binary sensors](#binary-sensors), and
[events](#events).

## Sensors

| Entity | Description | Unit | Device class | State class |
|---|---|---|---|---|
| **Current balance** | Current credit balance | € | `monetary` | `total` |
| **Days remaining** | Estimated days until credit runs out | days | — | `measurement` |
| **Last top-up amount** | Amount of the most recent top-up | € | `monetary` | `total` |
| **Today's usage** | Energy consumed so far today | kWh | `energy` | `total_increasing` |
| **Today's cost** | Cost of today's usage | € | `monetary` | `total` |
| **This week's usage** | Energy consumed so far this week | kWh | `energy` | `total_increasing` |
| **This week's cost** | Cost of this week's usage | € | `monetary` | `total` |
| **This month's usage** | Energy consumed so far this month | kWh | `energy` | `total_increasing` |
| **This month's cost** | Cost of this month's usage | € | `monetary` | `total` |
| **Last meter reading** | When the meter last reported | timestamp | `timestamp` | — |
| **Last top-up** ¹ | When the most recent top-up was made | timestamp | `timestamp` | — |
| **Average home usage today** ¹ | What a similar home used today | kWh | — | `measurement` |
| **Average home cost today** ¹ | What a similar home spent today | € | — | `measurement` |

¹ *Disabled by default.* Enable from the Pinergy Account device page if you want it.

!!! note "Why monetary sensors use `state class: total`"
    Home Assistant forbids `measurement` and `total_increasing` state classes on
    `monetary` device-class sensors, so all euro values use `total`. This is deliberate, not a
    bug.

!!! note "Why comparisons have no device class"
    The *average home* sensors are point-in-time comparisons, not account totals. The `energy`
    device class forbids the `measurement` state class they need, so they intentionally carry a
    unit but no device class.

### Availability

The period and comparison sensors expose an **availability** check: they report `unavailable`
until the meter has actually reported data for that period. This avoids showing a misleading
`0` before the day/week/month's first reading lands, or when the *average home* comparison is
absent for your account type.

## Binary sensors

| Entity | On when… | Device class |
|---|---|---|
| **Power** | The supply **is connected** | `power` |
| **Emergency credit** | The meter is drawing on emergency credit | `safety` |
| **Credit low** | The balance is below your alert threshold | `problem` |
| **Pending top-up** | A top-up is waiting to be applied to the meter | — |

!!! warning "Power is inverted relative to the raw API"
    The Pinergy API reports a `power_off` flag, but the **Power** binary sensor is `on` when
    the supply is *connected* (`is_on = not power_off`). This matches Home Assistant's `power`
    device-class semantics, where *on = power detected*. A disconnected supply reads as `off`.

## Events

Event entities let automations react the moment something changes, rather than polling a
sensor. They fire only when a newer timestamp is observed than the one seen on the previous
refresh (so they never re-fire historical data on restart).

| Entity | Event type | Attributes |
|---|---|---|
| **Top-up** | `top_up_received` | `amount` — the top-up value |
| **Meter reading** | `new_meter_reading` | — |

### Example automation

```yaml
automation:
  - alias: "Notify on Pinergy top-up"
    triggers:
      - trigger: state
        entity_id: event.pinergy_account_top_up
    actions:
      - action: notify.notify
        data:
          title: "Pinergy top-up received"
          message: >-
            A top-up of €{{ trigger.to_state.attributes.amount }} was applied.
```

## Naming and entity IDs

Each entity's unique ID is `‹premises_number›_‹key›`, keeping IDs stable across restarts and
reconfiguration. The friendly name comes from the integration's translations, so it follows
your Home Assistant language setting where available.
