"""Constants for the Pinergy integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "pinergy"

MANUFACTURER: Final = "Pinergy"

DEFAULT_SCAN_INTERVAL_MINUTES: Final = 30
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)

CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_FETCH_COMPARISONS: Final = "fetch_comparisons"
