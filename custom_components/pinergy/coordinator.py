"""DataUpdateCoordinator for the Pinergy integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pypinergy import (
    BalanceResponse,
    LoginResponse,
    PinergyAPIError,
    PinergyAuthError,
    PinergyClient,
    PinergyHTTPError,
    UsageResponse,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class PinergyData:
    """Container for the data fetched from the Pinergy API on each refresh."""

    balance: BalanceResponse
    usage: UsageResponse


class PinergyDataUpdateCoordinator(DataUpdateCoordinator[PinergyData]):
    """Coordinator that polls the Pinergy API for balance and usage data."""

    config_entry: ConfigEntry
    login_response: LoginResponse

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: PinergyClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_setup(self) -> None:
        """Log in once before the first refresh to capture account details."""
        try:
            self.login_response = await self.hass.async_add_executor_job(
                self.client.login
            )
        except PinergyAuthError as err:
            raise ConfigEntryAuthFailed(f"Invalid credentials: {err}") from err
        except (PinergyAPIError, PinergyHTTPError) as err:
            raise UpdateFailed(f"Error connecting to the Pinergy API: {err}") from err

    def _fetch(self) -> PinergyData:
        """Fetch balance and usage synchronously (runs in the executor)."""
        return PinergyData(
            balance=self.client.get_balance(),
            usage=self.client.get_usage(),
        )

    async def _async_update_data(self) -> PinergyData:
        """Fetch the latest data from the Pinergy API."""
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except PinergyAuthError:
            # The session token likely expired; clear it so the client logs in
            # again lazily, and retry once before asking the user to reauth.
            _LOGGER.debug("Auth token rejected, retrying with a fresh login")
            self.client.logout()
            try:
                return await self.hass.async_add_executor_job(self._fetch)
            except PinergyAuthError as err:
                raise ConfigEntryAuthFailed(f"Invalid credentials: {err}") from err
            except (PinergyAPIError, PinergyHTTPError) as err:
                raise UpdateFailed(
                    f"Error communicating with the Pinergy API: {err}"
                ) from err
        except (PinergyAPIError, PinergyHTTPError) as err:
            raise UpdateFailed(
                f"Error communicating with the Pinergy API: {err}"
            ) from err
