"""Long-term statistics import for the Pinergy integration.

The Pinergy API reports one aggregated usage entry per day for the last
seven days. Each coordinator refresh re-upserts that window as external
statistics so the Energy Dashboard stays accurate across Home Assistant
downtime and today's growing value self-corrects throughout the day.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from pypinergy import UsageEntry, UsageResponse

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    statistics_during_period,
)
from homeassistant.const import CURRENCY_EURO, UnitOfEnergy
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _statistic_id(premises_number: str, suffix: str) -> str:
    """Build a valid external statistic id for this premises."""
    slug = re.sub(r"[^a-z0-9]+", "_", premises_number.lower())
    return f"{DOMAIN}:{slug}_{suffix}"


def _metadata(statistic_id: str, name: str, unit: str) -> StatisticMetaData:
    """Build the metadata for one external statistic series."""
    return StatisticMetaData(
        has_mean=False,
        has_sum=True,
        name=f"Pinergy {name}",
        source=DOMAIN,
        statistic_id=statistic_id,
        unit_of_measurement=unit,
    )


async def _async_baseline_sum(
    hass: HomeAssistant, statistic_id: str, window_start: datetime
) -> float:
    """Return the cumulative sum accrued before the update window starts."""
    last = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {"sum"}
    )
    if not last:
        return 0.0
    last_row = last[statistic_id][0]
    if last_row["start"] < window_start.timestamp():
        return last_row["sum"] or 0.0
    # The window overlaps rows from an earlier refresh; rebase on the sum
    # the first overlapping row started from, so re-upserts stay idempotent.
    rows = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        window_start,
        None,
        {statistic_id},
        "hour",
        None,
        {"state", "sum"},
    )
    first_row = rows[statistic_id][0]
    return (first_row["sum"] or 0.0) - (first_row["state"] or 0.0)


async def async_insert_statistics(
    hass: HomeAssistant, premises_number: str, usage: UsageResponse
) -> None:
    """Insert the daily consumption and cost history as external statistics."""
    entries: list[UsageEntry] = sorted(
        (entry for entry in usage.day if entry.available),
        key=lambda entry: entry.date,
    )
    if not entries:
        return

    consumption_id = _statistic_id(premises_number, "energy_consumption")
    cost_id = _statistic_id(premises_number, "energy_cost")
    kwh_sum = await _async_baseline_sum(hass, consumption_id, entries[0].date)
    cost_sum = await _async_baseline_sum(hass, cost_id, entries[0].date)

    consumption: list[StatisticData] = []
    cost: list[StatisticData] = []
    for entry in entries:
        kwh_sum += entry.kwh
        cost_sum += entry.amount
        consumption.append(
            StatisticData(start=entry.date, state=entry.kwh, sum=kwh_sum)
        )
        cost.append(StatisticData(start=entry.date, state=entry.amount, sum=cost_sum))

    async_add_external_statistics(
        hass,
        _metadata(consumption_id, "energy consumption", UnitOfEnergy.KILO_WATT_HOUR),
        consumption,
    )
    async_add_external_statistics(
        hass, _metadata(cost_id, "energy cost", CURRENCY_EURO), cost
    )
