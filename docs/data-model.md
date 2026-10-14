# Data model & field decoding

How the response payloads are structured and how the integration decodes them.
Values below are from redacted captures; identifiers replaced per
[`placeholders.md`](placeholders.md).

## Live vitals — Ayla `REAL_TIME_VITALS` (Dream Sock / "version 3")

The ADS `properties.json` response is a list of property objects:

```json
[ { "property": { "name": "REAL_TIME_VITALS", "value": "<JSON string>",
                  "data_updated_at": "2026-10-14T19:17:35Z" } }, ... ]
```

The `value` of `REAL_TIME_VITALS` is itself a **JSON-encoded string**. Its keys
map to entities as follows:

| Key | Meaning | Type | Entity |
|-----|---------|------|--------|
| `hr` | Heart rate (bpm) | float | sensor `heart_rate` |
| `ox` | Oxygen saturation (%) | float | sensor `oxygen_saturation` |
| `oxta` | Oxygen 10-min average (%) | float | sensor `oxygen_10_av` |
| `mv` | Movement | int | sensor `movement` |
| `mvb` | Movement bucket | int | — |
| `st` | Skin temperature | int | sensor `skin_temperature` |
| `bat` | Battery (%) | float | sensor `battery_percentage` |
| `btt` | Battery remaining (minutes) | float | sensor `battery_minutes` |
| `rsi` | Wi-Fi/BLE signal strength | float | sensor `signal_strength` |
| `bso` | Base station on | bool | binary `base_station_on` |
| `sc` | Sock connection | int | binary `sock_connection` |
| `chg` | Charging state | int | binary `charging` |
| `ss` | Sleep state | int | sensor `sleep_state` |
| `aps` | Alert paused status | int | — |
| `alrt` | Alerts mask | int | — |
| `ota` | OTA/update status | int | — |
| `srf` | Readings flag | int | — |
| `sb` | Brick status | int | — |
| `onm` | Wellness alert | int | — |
| `mst` | Monitoring start time | int | — |
| `bsb` | Base battery status | int | — |
| `hw` | Hardware version | str | device info |

**Sleep state (`ss`) values** (also used in sleep-data `sleepStates`):

| Value | Meaning |
|-------|---------|
| 0 | unknown / no data |
| 1 | awake |
| 8 | light sleep |
| 15 | deep sleep |

Separate boolean "alert" properties appear as their own Ayla properties
(version-independent): `HIGH_OX_ALRT`, `LOW_BATT_ALRT`, `LOW_HR_ALRT`,
`HIGH_HR_ALRT`, `LOW_OX_ALRT`, `FW_UPDATE_STATUS`, `LOST_POWER_ALRT`,
`SOCK_DISCON_ALRT`, `SOCK_OFF`, `CRIT_BATT_ALRT`, `CRIT_OX_ALRT`.

### Smart Sock 2 ("version 2")

Older socks expose individual properties instead of `REAL_TIME_VITALS`:
`HEART_RATE`, `OXYGEN_LEVEL`, `BATT_LEVEL`, `MOVEMENT`, `CHARGE_STATUS`,
`BASE_STATION_ON`, `SOCK_CONNECTION`, `BLE_RSSI`, `OTA_STATUS`,
`oem_sock_version`. The integration detects the version by the presence of
`REAL_TIME_VITALS` (→ v3) or `CHARGE_STATUS` (→ v2).

## Aggregated vitals — `vital-data …/vitals`

Time-bucketed arrays (one entry per `resolution` window):

```json
{"data":{
  "counts":{"validSamples":[11,419,533,481]},
  "firstReadingTimes":[...],"lastReadingTimes":[...],
  "timeWindowStartTimes":[...],
  "heartRate":{"avg":[...],"max":[...],"min":[...]},
  "oxygen":{"avg":[...],"max":[...],"min":[...]},
  "movement":{"avg":[...]}
},"cameraData":null}
```

## Sleep — `sleep-data …/sleep`

```json
{"data":{
  "bodyPositions":[...],"positionTimes":[...],
  "sleepStates":[...],"timeWindowStartTimes":[...]
},
"last_reading_time":"2026-10-14T19:17:35+00:00",
"sessions":[{"sessionType":"CURRENT","startTime":...,"endTime":...,
  "sleepQuality":0.61,"sleepOnsetMinutes":5,
  "longestSleepSegmentMinutes":9,"wakingsCount":0,
  "sleepStateDurationsMinutes":{"1":16,"8":14}}]}
```

**Body position codes** (`bodyPositions`): small integers (e.g. 1, 4, 7, 8, 11)
representing posture; `combinedSleepPositionGraph` in `insights` groups them
into `BACK` / `TUMMY` / `SIDE`.

### `sleep-sessions`

Returns `owletDays[]`, each with `nightWindowStart`/`End`, `sleepGraph`
(`sleepStates[]` with `{sleepState,startTime}`) and `sleepSessions[]`
(`startTime`, `endTime`, `sessionType`, `origin`, `sleepSessionId`, …).

## Insights — `accounts …/insights`

Large aggregate payload with four top-level sections:

- `healthSummary` — `sockWearingScore`, `ageInWeeks`/`Months`,
  `pulseRateInsights`, `oxygenInsights`, `comfortTemperatureInsights`,
  `movementInsights`, and a `sevenDay[]` array with per-day
  `pulseRate`/`oxygen` `{min,max,avg,distribution[]}`.
- `morningReports[]` — per night: `sleepGrade`, `totalSleepMinutes`,
  `wakings`, `sleepStateDurationsMinutes`, `sleepGraph`,
  `combinedSleepPositionGraph` (BACK/TUMMY/SIDE with duration %, HR avg, O2 avg).
- `cameraSummary` — room temperature/humidity/noise hourly history (requires
  Owlet Cam; null without one).
- `sleepSummary` — nightly duration/routine/stretch/wakings trend insights.

> `insights` returns localized free-text (German in the capture). It is **not**
> consumed by the integration; documented for completeness.

## Sleep window — `accounts …/sleep-window`

```json
{"name":"accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/sleep-window",
 "startTime":"2026-01-01T00:00:00+00:00",
 "endTime":"2026-01-01T03:00:00+00:00"}
```
