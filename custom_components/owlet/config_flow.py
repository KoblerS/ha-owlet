"""Config flow for the Owlet Dream Sock integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import OwletAPI
from .const import (
    CONF_EXPIRY,
    CONF_REFRESH,
    CONF_REGION,
    CONF_TOKEN,
    DOMAIN,
    REGIONS,
)
from .exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletCredentialsError,
    OwletDevicesError,
)

_LOGGER = logging.getLogger(__name__)


class OwletConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Owlet."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the flow."""
        self._reauth_entry = None

    async def _validate(
        self, region: str, email: str, password: str
    ) -> tuple[dict[str, str], dict[str, Any] | None]:
        """Validate credentials, returning (errors, tokens)."""
        errors: dict[str, str] = {}
        api = OwletAPI(
            region=region,
            user=email,
            password=password,
            session=async_get_clientsession(self.hass),
        )
        try:
            await api.authenticate()
            await api.get_devices()
        except OwletCredentialsError:
            errors["base"] = "invalid_auth"
        except OwletDevicesError:
            errors["base"] = "no_devices"
        except OwletConnectionError:
            errors["base"] = "cannot_connect"
        except OwletAuthenticationError:
            errors["base"] = "invalid_auth"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error validating Owlet credentials")
            errors["base"] = "unknown"
        else:
            return errors, api.tokens
        return errors, None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            region = user_input[CONF_REGION]
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(f"{region}:{email.lower()}")
            self._abort_if_unique_id_configured()

            errors, tokens = await self._validate(region, email, password)
            if not errors and tokens is not None:
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_REGION: region,
                        CONF_EMAIL: email,
                        CONF_TOKEN: tokens["token"],
                        CONF_EXPIRY: tokens["expiry"],
                        CONF_REFRESH: tokens["refresh"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REGION, default="europe"): SelectSelector(
                        SelectSelectorConfig(
                            options=REGIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="region",
                        )
                    ),
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the stored tokens are rejected."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication by re-entering the password."""
        assert self._reauth_entry is not None
        errors: dict[str, str] = {}
        region = self._reauth_entry.data[CONF_REGION]
        email = self._reauth_entry.data[CONF_EMAIL]

        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            errors, tokens = await self._validate(region, email, password)
            if not errors and tokens is not None:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_TOKEN: tokens["token"],
                        CONF_EXPIRY: tokens["expiry"],
                        CONF_REFRESH: tokens["refresh"],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": email},
            errors=errors,
        )
