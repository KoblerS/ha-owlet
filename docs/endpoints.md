# Endpoints

Every host and endpoint observed in the captures, grouped by service. Account
ID, profile ID and device serial are redacted as `<ACCOUNT_ID>`,
`<PROFILE_ID>`, `<DSN>`.

## Auth

| Method | URL | Purpose |
|--------|-----|---------|
| POST | `googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=<KEY>` | Email+password → Firebase idToken/refreshToken |
| POST | `googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key=<KEY>` | Firebase account info for the idToken |
| POST | `securetoken.googleapis.com/v1/token?key=<KEY>` | Refresh idToken from refreshToken |
| GET  | `ayla-sso.eu.owletdata.com/mini/` | idToken → Ayla `mini_token` |
| POST | `user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in` | mini_token → Ayla `access_token` |

## Ayla device service (ADS) — live data

Base (EU): `https://ads-eu-1a2039d9.aylanetworks.com/apiv1`
(library/world base host: `ads-field-eu-1a2039d9` / `ads-field-1a2039d9`).
Auth: `Authorization: auth_token <ACCESS_TOKEN>`.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/devices.json` | List socks (DSN, model, mac, connection status…) |
| GET  | `/dsns/<DSN>/properties.json` | All device properties incl. `REAL_TIME_VITALS` |
| GET  | `/dsns/<DSN>/properties.json?names[]=APP_ACTIVE&names[]=REAL_TIME_VITALS&names[]=FW_UPDATE_STATUS&names[]=MOBILE_VITALS&names[]=APP_CMD_RESPONSE` | Targeted property fetch |
| POST | `/dsns/<DSN>/properties/APP_ACTIVE/datapoints.json` | Set `APP_ACTIVE=1` so the sock pushes fresh readings |

The app polls these roughly every ~90 s while in the foreground
("Scheduling Next Sleep Response Request" ≈ 99 s later in the logs). The sock
is a cloud-polled device (`transport: cloud polling`).

## Owlet data micro-services — history & insights

Auth: `Authorization: Bearer <ID_TOKEN>`.

### vital-data.eu.owletdata.com

| Method | Path | Query |
|--------|------|-------|
| GET | `/v1/accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/vitals` | `resolution=600&startTime=<epoch>&endTime=<epoch>&version=smartSock4` |

### sleep-data.eu.owletdata.com

| Method | Path | Query |
|--------|------|-------|
| GET | `/v1/accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/sleep` | `startTime&endTime&timeZone&returnBodyPositions=True&version=smartSock4` |
| GET | `/v1/accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/sleep-sessions` | `timeZone&startDate&endDate` |

### accounts.eu.owletdata.com

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v2/accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/sleep-window` | Configured night window (start/end time) |
| GET | `/v2/accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>/insights` | Health/sleep/camera summaries + morning reports |
| GET | `/v2/accounts/<ACCOUNT_ID>/events` | Alert & thermometer events (filtered by `eventType`, time range) |
| PATCH | `/v1/clients/<CLIENT_ID>` | Register the app client (push token, language, device type) |

`insights` query flags observed: `temperatureUnit=c`, `sleepSummary`,
`healthSummary`, `cryReports`, `morningReports`, `morningReportStartDate`,
`morningReportEndDate`, `cameraSummary`, `morningReportDates`, `timeZone`.

`events` filter example (URL-decoded):
`eventType = EVENT_TYPE_PROFILE_THERMOMETER_READING AND (startTime >= …) AND (startTime <= …) AND profile = "accounts/<ACCOUNT_ID>/profiles/<PROFILE_ID>"`
and alert types `EVENT_TYPE_PROFILE_HIGH_HR_ALRT`, `…_LOW_HR_ALRT`,
`…_LOW_OX_ALRT`.

## Rate limits

Responses carry `x-ratelimit-limit` / `-remaining` / `-reset`. Observed caps:

| Service | Limit (per 60 s window) |
|---------|-------------------------|
| ayla-sso `/mini/` | 10 |
| accounts (`/profiles/*`) | 70–80 |
| vital-data | 45–55 |
| sleep-data | 25–35 |
| accounts `/clients` PATCH | 90 |

The integration polls ADS every 30 s per device, well within limits.
