"""Fixtures for the Pinergy integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypinergy import (
    BalanceResponse,
    House,
    LoginResponse,
    UsageEntry,
    UsageResponse,
    User,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""


def build_login_response(premises_number: str = "PN123456") -> LoginResponse:
    """Build a realistic LoginResponse for mocking."""
    return LoginResponse(
        auth_token="test-token",
        is_legacy_meter=False,
        is_no_wan_meter=False,
        is_level_pay=False,
        is_child=False,
        is_business_connect=False,
        premises_number=premises_number,
        account_type="Residential",
        user=User(
            title="Mr",
            name="Test User",
            pinergy_id="12345",
            mobile_number="0851234567",
            sms_notifications=True,
            email_notifications=True,
            first_name="Test",
            last_name="User",
        ),
        house=House(
            type=1,
            heating_type=1,
            bedroom_count=3,
            adult_count=2,
            children_count=1,
        ),
        credit_cards=[],
    )


def build_balance_response() -> BalanceResponse:
    """Build a realistic BalanceResponse for mocking."""
    return BalanceResponse(
        credit_balance=23.45,
        top_up_in_days=7,
        pending_top_up=False,
        pending_top_up_by="",
        last_top_up_amount=20.0,
        credit_low=False,
        emergency_credit=False,
        power_off=False,
        last_top_up_ts=1765800000,
        last_top_up_time=datetime.fromtimestamp(1765800000, tz=UTC),
        last_reading_ts=1765886400,
        last_reading=datetime.fromtimestamp(1765886400, tz=UTC),
    )


def build_usage_response(today_available: bool = True) -> UsageResponse:
    """Build a realistic UsageResponse for mocking."""
    today = UsageEntry(
        available=today_available,
        amount=2.34,
        kwh=8.76,
        co2=0.0,
        date_ts=1765843200,
        date=datetime.fromtimestamp(1765843200, tz=UTC),
    )
    return UsageResponse(day=[today], week=[], month=[])


@pytest.fixture
def mock_pinergy_client() -> Generator[MagicMock]:
    """Mock the PinergyClient used by the config flow and setup."""
    with (
        patch(
            "custom_components.pinergy.config_flow.PinergyClient", autospec=True
        ) as mock_client_cls,
        patch("custom_components.pinergy.PinergyClient", new=mock_client_cls),
    ):
        client = mock_client_cls.return_value
        client.login.return_value = build_login_response()
        client.get_balance.return_value = build_balance_response()
        client.get_usage.return_value = build_usage_response()
        yield client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent the integration from actually being set up."""
    with patch(
        "custom_components.pinergy.async_setup_entry", return_value=True
    ) as mock:
        yield mock
