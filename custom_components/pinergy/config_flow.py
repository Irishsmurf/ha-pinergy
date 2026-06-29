"""Config flow for the Pinergy integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from pypinergy import (
    LoginResponse,
    PinergyAuthError,
    PinergyClient,
    PinergyError,
)

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    callback,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.selector import (
    BooleanSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_FETCH_COMPARISONS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class PinergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pinergy."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow for this handler."""
        return PinergyOptionsFlow()

    async def _async_validate_credentials(
        self, email: str, password: str
    ) -> tuple[dict[str, str], LoginResponse | None]:
        """Try to log in with the given credentials.

        Returns a (errors, login_response) tuple; on success errors is empty.
        """
        client = PinergyClient(email, password)
        try:
            login = await self.hass.async_add_executor_job(client.login)
        except PinergyAuthError:
            return {"base": "invalid_auth"}, None
        except PinergyError:
            return {"base": "cannot_connect"}, None
        except Exception:
            _LOGGER.exception("Unexpected exception while validating credentials")
            return {"base": "unknown"}, None
        return {}, login

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, login = await self._async_validate_credentials(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            if login is not None:
                await self.async_set_unique_id(login.premises_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_EMAIL], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication after the password changed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new password and validate it."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            errors, login = await self._async_validate_credentials(
                reauth_entry.data[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            if login is not None:
                await self.async_set_unique_id(login.premises_number)
                self._abort_if_unique_id_mismatch(reason="unique_id_mismatch")
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            description_placeholders={CONF_EMAIL: reauth_entry.data[CONF_EMAIL]},
            errors=errors,
        )


class PinergyOptionsFlow(OptionsFlow):
    """Handle options flow for Pinergy."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FETCH_COMPARISONS,
                        default=self.config_entry.options.get(
                            CONF_FETCH_COMPARISONS, True
                        ),
                    ): BooleanSelector(),
                }
            ),
        )
