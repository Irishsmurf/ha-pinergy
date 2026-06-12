"""Diagnostics support for the Pinergy integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import PinergyConfigEntry

TO_REDACT = {
    "auth_token",
    "cc_token",
    "email",
    "password",
    "premises_number",
    "pinergy_id",
    "mobile_number",
    "title",
    "name",
    "first_name",
    "last_name",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PinergyConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "login": async_redact_data(asdict(coordinator.login_response), TO_REDACT),
        "data": async_redact_data(asdict(coordinator.data), TO_REDACT),
    }
