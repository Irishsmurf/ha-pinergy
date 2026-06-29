"""DataUpdateCoordinator for the Pinergy integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pypinergy import (
    BalanceResponse,
    CompareResponse,
    LoginResponse,
    PinergyAPIError,
    PinergyAuthError,
    PinergyClient,
    PinergyError,
    PinergyHTTPError,
    PinergyTimeoutError,
    UsageResponse,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_FETCH_COMPARISONS, DEFAULT_SCAN_INTERVAL, DOMAIN
from .statistics import async_insert_statistics

if TYPE_CHECKING:
    from . import PinergyConfigEntry

_LOGGER = logging.getLogger(__name__)


def _is_token_error(err: PinergyAPIError) -> bool:
    """Return True if an application-level error means the token was rejected.

    The Pinergy API reports an expired session as HTTP 200 with
    ``success: false`` and a message like "Auth_token is not correct.", which
    pypinergy raises as PinergyAPIError rather than PinergyAuthError.
    """
    message = str(err).lower()
    return "auth_token" in message or "auth token" in message


@dataclass
class PinergyData:
    """Container for the data fetched from the Pinergy API on each refresh."""

    balance: BalanceResponse
    usage: UsageResponse
    compare: CompareResponse | None


class PinergyDataUpdateCoordinator(DataUpdateCoordinator[PinergyData]):
    """Coordinator that polls the Pinergy API for balance and usage data."""

    config_entry: PinergyConfigEntry
    login_response: LoginResponse

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: PinergyConfigEntry,
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
        except PinergyTimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to the Pinergy API: {err}") from err
        except (PinergyAPIError, PinergyHTTPError) as err:
            raise UpdateFailed(f"Error connecting to the Pinergy API: {err}") from err

    def _fetch(self) -> PinergyData:
        """Fetch balance, usage, and comparison synchronously (in the executor)."""
        balance = self.client.get_balance()
        usage = self.client.get_usage()
        # The compare endpoint is a non-essential insight that may not exist
        # for every account type (legacy/no-WAN/level-pay meters); never let
        # it break the balance refresh.
        compare: CompareResponse | None = None
        if self.config_entry.options.get(CONF_FETCH_COMPARISONS, True):
            try:
                compare = self.client.compare_usage()
            except PinergyError as err:
                _LOGGER.debug("Usage comparison unavailable: %s", err)
        return PinergyData(balance=balance, usage=usage, compare=compare)

    def _relogin_and_fetch(self) -> PinergyData:
        """Re-authenticate and fetch again (runs in the executor).

        Calls login() rather than logout(): pypinergy's logout() discards the
        stored credentials, which would make any later login impossible.
        """
        self.client.login()
        return self._fetch()

    async def _async_update_data(self) -> PinergyData:
        """Fetch the latest data and feed the long-term statistics."""
        data = await self._async_fetch_data()
        try:
            await async_insert_statistics(
                self.hass, self.login_response.premises_number, data.usage
            )
        except Exception:
            # A statistics hiccup must never take the entities down.
            _LOGGER.exception("Error inserting Pinergy long-term statistics")
        return data

    async def _async_fetch_data(self) -> PinergyData:
        """Fetch the latest data from the Pinergy API."""
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except PinergyTimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to the Pinergy API: {err}") from err
        except (PinergyAuthError, PinergyAPIError) as err:
            if isinstance(err, PinergyAPIError) and not _is_token_error(err):
                raise UpdateFailed(
                    f"Error communicating with the Pinergy API: {err}"
                ) from err
            # The session token expired; refresh it with the stored
            # credentials and retry once before asking the user to reauth.
            _LOGGER.debug("Auth token rejected (%s), retrying with a fresh login", err)
            try:
                return await self.hass.async_add_executor_job(self._relogin_and_fetch)
            except PinergyAuthError as relogin_err:
                raise ConfigEntryAuthFailed(
                    f"Invalid credentials: {relogin_err}"
                ) from relogin_err
            except PinergyTimeoutError as relogin_err:
                raise UpdateFailed(
                    f"Timeout connecting to the Pinergy API: {relogin_err}"
                ) from relogin_err
            except (PinergyAPIError, PinergyHTTPError) as relogin_err:
                raise UpdateFailed(
                    f"Error communicating with the Pinergy API: {relogin_err}"
                ) from relogin_err
        except PinergyHTTPError as err:
            raise UpdateFailed(
                f"Error communicating with the Pinergy API: {err}"
            ) from err
