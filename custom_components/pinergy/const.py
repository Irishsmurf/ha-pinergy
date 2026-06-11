"""Constants for the Pinergy integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "pinergy"

MANUFACTURER: Final = "Pinergy"

DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=30)
