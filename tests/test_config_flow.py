"""Tests for the Pinergy config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pypinergy import PinergyAuthError, PinergyHTTPError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pinergy.const import DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "super-secret"
TEST_USER_INPUT = {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full happy path of the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_EMAIL
    assert result["data"] == TEST_USER_INPUT
    assert result["result"].unique_id == "PN123456"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_flow_invalid_auth(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that bad credentials show an error and the flow can recover."""
    mock_pinergy_client.login.side_effect = PinergyAuthError("Login failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # The flow recovers once the credentials validate.
    mock_pinergy_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_cannot_connect(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that a network error shows an error and the flow can recover."""
    mock_pinergy_client.login.side_effect = PinergyHTTPError("timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_pinergy_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_unknown_error(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that an unexpected exception maps to the unknown error."""
    mock_pinergy_client.login.side_effect = ValueError("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that a second entry for the same premises aborts."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        data=TEST_USER_INPUT,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test a successful reauthentication updates the stored password."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        data=TEST_USER_INPUT,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"


async def test_reauth_flow_invalid_auth(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test that reauth shows an error on bad credentials and can recover."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        data=TEST_USER_INPUT,
    )
    entry.add_to_hass(hass)

    mock_pinergy_client.login.side_effect = PinergyAuthError("Login failed")

    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "still-wrong"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mock_pinergy_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"

async def test_options_flow(
    hass: HomeAssistant,
    mock_pinergy_client: MagicMock,
) -> None:
    """Test the options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="PN123456",
        data=TEST_USER_INPUT,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "scan_interval": 15,
            "fetch_comparisons": False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        "scan_interval": 15,
        "fetch_comparisons": False,
    }
