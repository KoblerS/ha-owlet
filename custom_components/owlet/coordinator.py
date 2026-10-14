"""Data update coordinator for the Owlet integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OwletAPI, detect_version, normalise_properties
from .const import (
    CONF_EXPIRY,
    CONF_REFRESH,
    CONF_REGION,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .exceptions import OwletAuthenticationError, OwletError

_LOGGER = logging.getLogger(__name__)


class OwletCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator that polls the Owlet cloud for all socks on an account."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        self.entry = entry
        self.api = OwletAPI(
            region=entry.data[CONF_REGION],
            token=entry.data.get(CONF_TOKEN),
            expiry=entry.data.get(CONF_EXPIRY),
            refresh=entry.data.get(CONF_REFRESH),
            session=async_get_clientsession(hass),
        )
        # dsn -> static device info (name/model/mac/...)
        self.devices: dict[str, dict[str, Any]] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def async_setup(self) -> None:
        """Authenticate and discover the socks on the account."""
        try:
            await self.api.authenticate()
            self._persist_tokens()
            devices = await self.api.get_devices()
        except OwletAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OwletError as err:
            raise UpdateFailed(str(err)) from err

        for device in devices:
            info = device["device"]
            self.devices[info["dsn"]] = info

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch and normalise properties for every known sock."""
        data: dict[str, dict[str, Any]] = {}
        try:
            for dsn in self.devices:
                raw = await self.api.get_properties(dsn)
                normalised = normalise_properties(raw)
                normalised.setdefault("version", detect_version(raw))
                data[dsn] = normalised
            self._persist_tokens()
        except OwletAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OwletError as err:
            raise UpdateFailed(str(err)) from err
        return data

    def _persist_tokens(self) -> None:
        """Write refreshed tokens back into the config entry when they change."""
        tokens = self.api.consume_token_update()
        if tokens is None:
            return
        new_data = {
            **self.entry.data,
            CONF_TOKEN: tokens["token"],
            CONF_EXPIRY: tokens["expiry"],
            CONF_REFRESH: tokens["refresh"],
        }
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
