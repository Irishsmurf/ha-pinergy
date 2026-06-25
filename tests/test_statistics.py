"""Tests for the Pinergy long-term statistics import."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from freezegun.api import FrozenDateTimeFactory
from pypinergy import UsageResponse
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.pinergy.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .conftest import build_usage_entry

CONSUMPTION_ID = "pinergy:pn123456_energy_consumption"
COST_ID = "pinergy:pn123456_energy_cost"

YESTERDAY_TS = 1765756800
TODAY_TS = 1765843200


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        title="user@example.com",
        data={CONF_EMAIL: "user@example.com", CONF_PASSWORD: "super-secret"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _get_stats(hass: HomeAssistant) -> dict[str, list[dict]]:
    return await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        datetime.fromtimestamp(0, tz=UTC),
        None,
        {CONSUMPTION_ID, COST_ID},
        "hour",
        None,
        {"state", "sum"},
    )


async def test_statistics_inserted_on_first_refresh(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that the first refresh inserts both statistic series."""
    await _setup_entry(hass)
    await async_wait_recording_done(hass)

    stats = await _get_stats(hass)

    consumption = stats[CONSUMPTION_ID]
    assert len(consumption) == 2
    assert consumption[0]["start"] == YESTERDAY_TS
    assert consumption[0]["state"] == pytest.approx(10.5)
    assert consumption[0]["sum"] == pytest.approx(10.5)
    assert consumption[1]["start"] == TODAY_TS
    assert consumption[1]["state"] == pytest.approx(8.76)
    assert consumption[1]["sum"] == pytest.approx(19.26)

    cost = stats[COST_ID]
    assert len(cost) == 2
    assert cost[0]["sum"] == pytest.approx(3.21)
    assert cost[1]["state"] == pytest.approx(2.34)
    assert cost[1]["sum"] == pytest.approx(5.55)


async def test_statistics_reupsert_corrects_today(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a later refresh updates today's row instead of duplicating."""
    await _setup_entry(hass)
    await async_wait_recording_done(hass)

    # Today's usage grew between refreshes.
    mock_pinergy_client.get_usage.return_value = UsageResponse(
        day=[
            build_usage_entry(TODAY_TS, 9.5, 2.85),
            build_usage_entry(YESTERDAY_TS, 10.5, 3.21),
        ],
        week=[],
        month=[],
    )
    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)

    stats = await _get_stats(hass)

    consumption = stats[CONSUMPTION_ID]
    assert len(consumption) == 2
    assert consumption[0]["sum"] == pytest.approx(10.5)
    assert consumption[1]["state"] == pytest.approx(9.5)
    assert consumption[1]["sum"] == pytest.approx(20.0)

    cost = stats[COST_ID]
    assert cost[1]["state"] == pytest.approx(2.85)
    assert cost[1]["sum"] == pytest.approx(6.06)


async def test_statistics_skip_unavailable_days(
    hass: HomeAssistant, mock_pinergy_client: MagicMock
) -> None:
    """Test that days the meter has not reported are not inserted."""
    mock_pinergy_client.get_usage.return_value = UsageResponse(
        day=[
            build_usage_entry(TODAY_TS, 0.0, 0.0, available=False),
            build_usage_entry(YESTERDAY_TS, 10.5, 3.21),
        ],
        week=[],
        month=[],
    )
    await _setup_entry(hass)
    await async_wait_recording_done(hass)

    stats = await _get_stats(hass)
    consumption = stats[CONSUMPTION_ID]
    assert len(consumption) == 1
    assert consumption[0]["start"] == YESTERDAY_TS


def test_metadata_builds_without_mean_type_on_older_ha() -> None:
    """_metadata must build valid StatisticMetaData regardless of HA version.

    Older HA (pre-StatisticMeanType) lacks the ``mean_type`` field; the module
    must not unconditionally depend on it or it fails to import/build.
    """
    from custom_components.pinergy.statistics import _metadata

    meta = _metadata("pinergy:premises_consumption", "Consumption", "kWh", "energy")

    assert meta["statistic_id"] == "pinergy:premises_consumption"
    assert meta["has_sum"] is True
    assert meta["unit_of_measurement"] == "kWh"


def test_metadata_specifies_unit_class() -> None:
    """_metadata must specify unit_class where HA supports it (from 2026.11).

    Omitting it logs a deprecation warning and stops working in HA 2026.11.
    Energy series carry the ``energy`` unit class; monetary series have no
    converter, so the key is present but ``None``. Older HA rejects the unknown
    key, so it is only emitted when ``_SUPPORTS_UNIT_CLASS``.
    """
    from unittest.mock import patch

    from custom_components.pinergy.statistics import _metadata

    module = "custom_components.pinergy.statistics._SUPPORTS_UNIT_CLASS"

    with patch(module, True):
        energy = _metadata("pinergy:c", "Consumption", "kWh", "energy")
        cost = _metadata("pinergy:m", "Cost", "EUR", None)
        assert energy["unit_class"] == "energy"
        assert cost["unit_class"] is None

    with patch(module, False):
        energy = _metadata("pinergy:c", "Consumption", "kWh", "energy")
        cost = _metadata("pinergy:m", "Cost", "EUR", None)
        assert "unit_class" not in energy
        assert "unit_class" not in cost
