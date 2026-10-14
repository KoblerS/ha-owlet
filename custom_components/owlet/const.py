"""Constants for the Owlet Dream Sock integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "owlet"

CONF_REGION: Final = "region"
CONF_TOKEN: Final = "token"
CONF_EXPIRY: Final = "expiry"
CONF_REFRESH: Final = "refresh"

DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

MANUFACTURER: Final = "Owlet Baby Care"

# Region specific endpoints and credentials.
#
# The Firebase ``apiKey`` values below were taken from the current Owlet Dream
# app (v3.48.0) network captures.  The Ayla ``app_id``/``app_secret`` pairs are
# the long-standing public mobile-app credentials used by the Owlet apps.
REGION_INFO: Final[dict[str, dict[str, str]]] = {
    "europe": {
        "url_mini": "https://ayla-sso.eu.owletdata.com/mini/",
        "url_signin": "https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
        "url_base": "https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1",
        "api_key": "AIzaSyCCVPALBrbhZIPArEIBHbsWbSZKloOUVRk",
        "app_id": "OwletCare-Android-EU-fw-id",
        "app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
    },
    "world": {
        "url_mini": "https://ayla-sso.owletdata.com/mini/",
        "url_signin": "https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
        "url_base": "https://ads-field-1a2039d9.aylanetworks.com/apiv1",
        "api_key": "AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA",
        "app_id": "sso-prod-3g-id",
        "app_secret": "sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU",
    },
}

REGIONS: Final = list(REGION_INFO)

# Headers used against the Google identitytoolkit / securetoken APIs so the
# request looks like it originates from the official app.
GOOGLE_HEADERS: Final[dict[str, str]] = {
    "X-Android-Package": "com.owletcare.owletcare",
    "X-Android-Cert": "2A3BC26DB0B8B0792DBE28E6FFDC2598F9B12B74",
}

# --- Property decoding -------------------------------------------------------
#
# Dream Sock (version 3) devices report their live readings as a JSON blob in
# the Ayla ``REAL_TIME_VITALS`` property.  Older Smart Sock 2 devices expose
# each reading as an individual Ayla property.  The maps below translate the
# raw Ayla keys into normalised attribute names used by the entities.

# Boolean "alert" style properties (version independent).
BOOL_PROPERTIES: Final[dict[str, str]] = {
    "high_oxygen_alert": "HIGH_OX_ALRT",
    "low_battery_alert": "LOW_BATT_ALRT",
    "low_heart_rate_alert": "LOW_HR_ALRT",
    "high_heart_rate_alert": "HIGH_HR_ALRT",
    "low_oxygen_alert": "LOW_OX_ALRT",
    "firmware_update_available": "FW_UPDATE_STATUS",
    "lost_power_alert": "LOST_POWER_ALRT",
    "sock_disconnected": "SOCK_DISCON_ALRT",
    "sock_off": "SOCK_OFF",
    "critical_battery_alert": "CRIT_BATT_ALRT",
    "critical_oxygen_alert": "CRIT_OX_ALRT",
}

# version 3 (Dream Sock) – keys inside the REAL_TIME_VITALS JSON blob.
VITALS_3: Final[dict[str, tuple[str, type]]] = {
    "oxygen_saturation": ("ox", float),
    "heart_rate": ("hr", float),
    "battery_percentage": ("bat", float),
    "battery_minutes": ("btt", float),
    "signal_strength": ("rsi", float),
    "oxygen_10_av": ("oxta", float),
    "base_station_on": ("bso", bool),
    "sock_connection": ("sc", int),
    "skin_temperature": ("st", int),
    "sleep_state": ("ss", int),
    "movement": ("mv", int),
    "alert_paused_status": ("aps", int),
    "charging": ("chg", int),
    "alerts_mask": ("alrt", int),
    "update_status": ("ota", int),
    "readings_flag": ("srf", int),
    "brick_status": ("sb", int),
    "movement_bucket": ("mvb", int),
    "wellness_alert": ("onm", int),
    "monitoring_start_time": ("mst", int),
    "base_battery_status": ("bsb", int),
    "hardware_version": ("hw", str),
}

# version 2 (Smart Sock 2) – individual Ayla properties.
VITALS_2: Final[dict[str, tuple[str, type]]] = {
    "signal_strength": ("BLE_RSSI", float),
    "base_station_on": ("BASE_STATION_ON", bool),
    "sock_connection": ("SOCK_CONNECTION", bool),
    "oxygen_saturation": ("OXYGEN_LEVEL", int),
    "heart_rate": ("HEART_RATE", int),
    "battery_percentage": ("BATT_LEVEL", int),
    "movement": ("MOVEMENT", int),
    "charging": ("CHARGE_STATUS", int),
    "update_status": ("OTA_STATUS", int),
    "hardware_version": ("oem_sock_version", str),
}

# Human readable sleep states (Dream Sock).
SLEEP_STATES: Final[dict[int, str]] = {
    0: "unknown",
    1: "awake",
    8: "light_sleep",
    15: "deep_sleep",
}
