"""Self-contained async client for the Owlet (Ayla Networks) cloud API.

The Owlet Dream app authenticates in three steps:

1. ``POST`` the e-mail/password to Google's Firebase *identitytoolkit*
   ``verifyPassword`` endpoint for the account's region, which returns a
   Firebase ``idToken`` and a ``refreshToken``.
2. ``GET`` the region's ``ayla-sso .../mini/`` endpoint with the Firebase
   ``idToken`` to obtain a short lived Ayla ``mini_token``.
3. ``POST`` the ``mini_token`` to Ayla's ``token_sign_in`` with the mobile
   app's ``app_id``/``app_secret`` to receive an Ayla ``access_token`` used as
   ``Authorization: auth_token <token>`` for all subsequent device calls.

Live readings come from the Ayla device-service (ADS) ``properties.json``
endpoint; Dream Socks pack them into a single ``REAL_TIME_VITALS`` JSON blob.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import aiohttp

from .const import (
    BOOL_PROPERTIES,
    GOOGLE_HEADERS,
    REGION_INFO,
    VITALS_2,
    VITALS_3,
)
from .exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletCredentialsError,
    OwletDevicesError,
    OwletError,
)

_LOGGER = logging.getLogger(__name__)

# Refresh a little before the real expiry to avoid races.
_EXPIRY_MARGIN = 60


class OwletAPI:
    """Client against the Owlet/Ayla cloud for a single account."""

    def __init__(
        self,
        region: str,
        user: str | None = None,
        password: str | None = None,
        token: str | None = None,
        expiry: float | None = None,
        refresh: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialise the client.

        Either ``user``/``password`` or a previously stored ``refresh`` token
        (plus optional ``token``/``expiry``) must be supplied.
        """
        if region not in REGION_INFO:
            raise OwletAuthenticationError(f"Unsupported region: {region}")

        self._region = region
        self._user = user
        self._password = password
        self._auth_token = token
        self._expiry = expiry
        self._refresh = refresh
        self._tokens_changed = False
        self._owns_session = session is None
        self.session = session or aiohttp.ClientSession()
        self.headers: dict[str, str] = {}
        if self._auth_token:
            self.headers["Authorization"] = f"auth_token {self._auth_token}"

        self._region_info = REGION_INFO[region]
        self._api_url = self._region_info["url_base"]

    # -- token bookkeeping ---------------------------------------------------

    @property
    def tokens(self) -> dict[str, Any]:
        """Return the current token set for persistence."""
        return {
            "token": self._auth_token,
            "expiry": self._expiry,
            "refresh": self._refresh,
        }

    def _update_tokens(
        self,
        *,
        token: str | None,
        expiry: float | None,
        refresh: str | None,
    ) -> None:
        if (self._auth_token, self._expiry, self._refresh) != (token, expiry, refresh):
            self._auth_token = token
            self._expiry = expiry
            self._refresh = refresh
            if token:
                self.headers["Authorization"] = f"auth_token {token}"
            self._tokens_changed = True

    def consume_token_update(self) -> dict[str, Any] | None:
        """Return new tokens exactly once after they changed, else ``None``."""
        if self._tokens_changed:
            self._tokens_changed = False
            return self.tokens
        return None

    # -- authentication steps ------------------------------------------------

    async def _password_verification(self) -> None:
        """Step 1: exchange e-mail/password for a Firebase refresh token."""
        api_key = self._region_info["api_key"]
        url = (
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/"
            f"verifyPassword?key={api_key}"
        )
        try:
            async with self.session.post(
                url,
                json={
                    "email": self._user,
                    "password": self._password,
                    "returnSecureToken": True,
                },
                headers=GOOGLE_HEADERS,
            ) as response:
                data = await response.json()
                if response.status != 200:
                    self._raise_identitytoolkit_error(response.status, data)
                self._update_tokens(
                    token=self._auth_token,
                    expiry=self._expiry,
                    refresh=data["refreshToken"],
                )
        except aiohttp.ClientError as err:
            raise OwletConnectionError(f"Error contacting Firebase: {err}") from err

    @staticmethod
    def _raise_identitytoolkit_error(status: int, data: dict[str, Any]) -> None:
        message = ""
        if isinstance(data, dict):
            message = str(data.get("error", {}).get("message", ""))
        head = message.split(":")[0]
        if status == 400 and head in (
            "INVALID_LOGIN_CREDENTIALS",
            "EMAIL_NOT_FOUND",
            "INVALID_PASSWORD",
            "INVALID_EMAIL",
        ):
            raise OwletCredentialsError("Invalid login credentials")
        if status == 400 and head == "TOO_MANY_ATTEMPTS_TRY_LATER":
            raise OwletAuthenticationError("Too many incorrect attempts, try later")
        raise OwletAuthenticationError(
            f"Firebase sign-in failed ({status}): {message or 'unknown error'}"
        )

    async def _get_mini_token(self, id_token: str) -> str:
        """Step 2: exchange the Firebase id token for an Ayla mini token."""
        try:
            async with self.session.get(
                self._region_info["url_mini"],
                headers={"Authorization": id_token},
            ) as response:
                if response.status == 401:
                    raise OwletAuthenticationError("Rejected Firebase id token")
                if response.status != 200:
                    raise OwletAuthenticationError(
                        f"Ayla mini token error ({response.status})"
                    )
                data = await response.json()
                return data["mini_token"]
        except aiohttp.ClientError as err:
            raise OwletConnectionError(f"Error contacting Ayla SSO: {err}") from err

    async def _token_sign_in(self, mini_token: str) -> None:
        """Step 3: exchange the mini token for an Ayla access token."""
        try:
            async with self.session.post(
                self._region_info["url_signin"],
                json={
                    "app_id": self._region_info["app_id"],
                    "app_secret": self._region_info["app_secret"],
                    "provider": "owl_id",
                    "token": mini_token,
                },
            ) as response:
                if response.status == 401:
                    raise OwletAuthenticationError("Rejected Ayla mini token")
                if response.status != 200:
                    raise OwletAuthenticationError(
                        f"Ayla sign-in error ({response.status})"
                    )
                data = await response.json()
                self._update_tokens(
                    token=data["access_token"],
                    expiry=time.time() - _EXPIRY_MARGIN + data["expires_in"],
                    refresh=self._refresh,
                )
        except aiohttp.ClientError as err:
            raise OwletConnectionError(f"Error contacting Ayla: {err}") from err

    async def _refresh_authentication(self) -> None:
        """Use the stored Firebase refresh token to obtain a fresh id token."""
        if not self._refresh:
            raise OwletAuthenticationError("No refresh token available")
        api_key = self._region_info["api_key"]
        try:
            async with self.session.post(
                f"https://securetoken.googleapis.com/v1/token?key={api_key}",
                data={
                    "grantType": "refresh_token",
                    "refreshToken": self._refresh,
                },
                headers=GOOGLE_HEADERS,
            ) as response:
                data = await response.json()
                if response.status != 200:
                    if response.status == 400:
                        raise OwletAuthenticationError("Refresh token not valid")
                    raise OwletError(f"Token refresh failed ({response.status})")
                self._update_tokens(
                    token=self._auth_token,
                    expiry=self._expiry,
                    refresh=data["refresh_token"],
                )
                id_token = data["id_token"]
        except aiohttp.ClientError as err:
            raise OwletConnectionError(f"Error refreshing token: {err}") from err

        mini_token = await self._get_mini_token(id_token)
        await self._token_sign_in(mini_token)

    async def authenticate(self) -> None:
        """Ensure the client holds a valid Ayla access token."""
        if self._auth_token is None and self._refresh is None:
            if not self._user or not self._password:
                raise OwletAuthenticationError("Username or password not supplied")
            await self._password_verification()

        if (
            self._auth_token is None
            or self._expiry is None
            or self._expiry <= time.time()
        ):
            await self._refresh_authentication()

    async def close(self) -> None:
        """Close the owned aiohttp session, if any."""
        if self._owns_session and self.session and not self.session.closed:
            await self.session.close()

    # -- device data ---------------------------------------------------------

    async def get_devices(self) -> list[dict[str, Any]]:
        """Return the list of socks on the account (raw Ayla device dicts)."""
        response = await self._request("GET", "/devices.json")
        if not isinstance(response, list):
            raise OwletError("Unexpected device list response")
        devices = [d for d in response if "device" in d]
        if not devices:
            raise OwletDevicesError("No devices found on account")
        return devices

    async def activate(self, dsn: str) -> None:
        """Set APP_ACTIVE so the sock pushes fresh readings."""
        await self._request(
            "POST",
            f"/dsns/{dsn}/properties/APP_ACTIVE/datapoints.json",
            data={"datapoint": {"metadata": {}, "value": 1}},
        )

    async def get_properties(self, dsn: str) -> dict[str, dict[str, Any]]:
        """Return the raw Ayla properties for a device keyed by property name."""
        await self.activate(dsn)
        response = await self._request("GET", f"/dsns/{dsn}/properties.json")
        properties: dict[str, dict[str, Any]] = {}
        for item in response:
            prop = item["property"]
            properties[prop["name"]] = prop
        return properties

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated request against the Ayla device service."""
        await self.authenticate()
        try:
            async with self.session.request(
                method,
                self._api_url + path,
                headers=self.headers,
                json=data,
            ) as response:
                if response.status == 401:
                    # Token might have been revoked – retry once after refresh.
                    self._auth_token = None
                    await self.authenticate()
                    async with self.session.request(
                        method,
                        self._api_url + path,
                        headers=self.headers,
                        json=data,
                    ) as retry:
                        if retry.status not in (200, 201):
                            raise OwletConnectionError(
                                f"Owlet API error ({retry.status})"
                            )
                        return await retry.json()
                if response.status not in (200, 201):
                    raise OwletConnectionError(f"Owlet API error ({response.status})")
                return await response.json()
        except aiohttp.ClientError as err:
            raise OwletConnectionError(f"Error contacting Owlet API: {err}") from err


def detect_version(raw_properties: dict[str, dict[str, Any]]) -> int:
    """Return the sock generation (3 = Dream Sock, 2 = Smart Sock 2, 0 = ?)."""
    if "REAL_TIME_VITALS" in raw_properties:
        return 3
    if "CHARGE_STATUS" in raw_properties:
        return 2
    return 0


def normalise_properties(raw_properties: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Flatten the raw Ayla properties into normalised attribute names."""
    result: dict[str, Any] = {}

    for key, ayla_name in BOOL_PROPERTIES.items():
        prop = raw_properties.get(ayla_name)
        if prop is not None and prop.get("value") is not None:
            result[key] = bool(prop["value"])

    version = detect_version(raw_properties)
    result["version"] = version

    if version == 3:
        try:
            vitals = json.loads(raw_properties["REAL_TIME_VITALS"]["value"])
        except (KeyError, ValueError, TypeError):
            vitals = {}
        for key, (vital_key, cast) in VITALS_3.items():
            if vital_key in vitals and vitals[vital_key] is not None:
                try:
                    result[key] = cast(vitals[vital_key])
                except (ValueError, TypeError):
                    result[key] = vitals[vital_key]
        updated_at = raw_properties.get("REAL_TIME_VITALS", {}).get("data_updated_at")
        if updated_at:
            result["last_updated"] = updated_at
    elif version == 2:
        for key, (ayla_name, cast) in VITALS_2.items():
            prop = raw_properties.get(ayla_name)
            if prop is not None and prop.get("value") is not None:
                try:
                    result[key] = cast(prop["value"])
                except (ValueError, TypeError):
                    result[key] = prop["value"]

    return result


__all__ = [
    "OwletAPI",
    "detect_version",
    "normalise_properties",
]
