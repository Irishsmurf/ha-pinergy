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
    PinergyTimeoutError,
    UsageResponse,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

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
        except PinergyTimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to the Pinergy API: {err}") from err
        except (PinergyAPIError, PinergyHTTPError) as err:
            raise UpdateFailed(f"Error connecting to the Pinergy API: {err}") from err

    def _fetch(self) -> PinergyData:
        """Fetch balance and usage synchronously (runs in the executor)."""
        return PinergyData(
            balance=self.client.get_balance(),
            usage=self.client.get_usage(),
        )

    def _relogin_and_fetch(self) -> PinergyData:
        """Re-authenticate and fetch again (runs in the executor).

        Calls login() rather than logout(): pypinergy's logout() discards the
        stored credentials, which would make any later login impossible.
        """
        self.client.login()
        return self._fetch()

    async def _async_update_data(self) -> PinergyData:
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
