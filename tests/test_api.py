"""Tests for the Owlet API property decoding (no network, no Home Assistant)."""

import json

from custom_components.owlet.api import detect_version, normalise_properties


def _dream_sock_raw():
    vitals = {
        "hr": 163,
        "ox": 98,
        "oxta": 97,
        "bat": 95,
        "btt": 480,
        "rsi": -55,
        "bso": True,
        "sc": 1,
        "st": 34,
        "ss": 8,
        "mv": 3,
        "chg": 0,
        "hw": "4.0.0",
    }
    return {
        "REAL_TIME_VITALS": {
            "value": json.dumps(vitals),
            "data_updated_at": "2026-10-14T19:17:35Z",
        },
        "LOW_OX_ALRT": {"value": False},
        "SOCK_OFF": {"value": True},
        "FW_UPDATE_STATUS": {"value": False},
    }


def test_detect_version_dream_sock():
    assert detect_version(_dream_sock_raw()) == 3


def test_detect_version_smart_sock_2():
    assert detect_version({"CHARGE_STATUS": {"value": 0}}) == 2


def test_detect_version_unknown():
    assert detect_version({"SOMETHING_ELSE": {"value": 1}}) == 0


def test_normalise_dream_sock_vitals():
    norm = normalise_properties(_dream_sock_raw())
    assert norm["version"] == 3
    assert norm["heart_rate"] == 163.0
    assert norm["oxygen_saturation"] == 98.0
    assert norm["oxygen_10_av"] == 97.0
    assert norm["battery_percentage"] == 95.0
    assert norm["battery_minutes"] == 480.0
    assert norm["signal_strength"] == -55.0
    assert norm["skin_temperature"] == 34
    assert norm["sleep_state"] == 8
    assert norm["movement"] == 3
    assert norm["base_station_on"] is True
    assert norm["sock_connection"] == 1
    assert norm["hardware_version"] == "4.0.0"
    assert norm["last_updated"] == "2026-10-14T19:17:35Z"


def test_normalise_boolean_alerts():
    norm = normalise_properties(_dream_sock_raw())
    assert norm["sock_off"] is True
    assert norm["low_oxygen_alert"] is False
    assert norm["firmware_update_available"] is False


def test_normalise_smart_sock_2():
    raw = {
        "CHARGE_STATUS": {"value": 0},
        "HEART_RATE": {"value": 150},
        "OXYGEN_LEVEL": {"value": 99},
        "BATT_LEVEL": {"value": 80},
        "SOCK_CONNECTION": {"value": 1},
        "BLE_RSSI": {"value": -60},
    }
    norm = normalise_properties(raw)
    assert norm["version"] == 2
    assert norm["heart_rate"] == 150
    assert norm["oxygen_saturation"] == 99
    assert norm["battery_percentage"] == 80
    assert norm["sock_connection"] is True
    assert norm["signal_strength"] == -60.0


def test_normalise_handles_malformed_vitals():
    raw = {"REAL_TIME_VITALS": {"value": "not-json"}}
    norm = normalise_properties(raw)
    # Still reports version 3 but no decoded vitals.
    assert norm["version"] == 3
    assert "heart_rate" not in norm
