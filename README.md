# Owlet Dream Sock — Home Assistant integration

A custom [Home Assistant](https://www.home-assistant.io/) integration for the
**Owlet Dream Sock** (and Smart Sock 2) baby monitor. It polls the Owlet cloud
(Firebase → Ayla Networks) and exposes the sock's live readings as entities.

> ⚠️ This is an unofficial integration using the same cloud API as the Owlet
> app. It is **not** a medical device and must not be relied upon for medical
> monitoring. Owlet may change or block the API at any time.

## Features

- Config flow with **Europe / World** region selection and e-mail + password
  login. Tokens are stored and refreshed automatically; a re-auth flow prompts
  for the password again if the refresh token ever becomes invalid.
- Cloud polling every 30 seconds.

### Sensors
Heart rate, oxygen saturation (SpO₂), oxygen 10-min average, movement, skin
temperature, battery %, battery runtime, signal strength, sleep state
(awake / light / deep).

### Binary sensors
Base station on, sock connection, sock off, charging, firmware update
available, and the alert flags: high/low heart rate, low/high oxygen,
low battery, lost power.

## Installation

### HACS (custom repository)
1. HACS → Integrations → ⋮ → *Custom repositories*.
2. Add `https://github.com/KoblerS/ha-owlet` as an *Integration*.
3. Install **Owlet Dream Sock**, then restart Home Assistant.

### Manual
Copy `custom_components/owlet` into your Home Assistant `config/custom_components`
directory and restart.

## Configuration

Settings → Devices & Services → **Add Integration** → *Owlet Dream Sock*.
Pick your region (the Owlet app region your account was created in — the EU
app uses *Europe*), then enter your Owlet account e-mail and password.

## How it works

The integration reproduces the Owlet app's authentication chain entirely in
`custom_components/owlet/api.py`, with no third-party API dependency:

1. **Firebase** `identitytoolkit/verifyPassword` → Firebase `idToken` +
   `refreshToken` (region-specific API key).
2. **Ayla SSO** `ayla-sso[.eu].owletdata.com/mini/` → short-lived `mini_token`.
3. **Ayla** `token_sign_in` (app `app_id`/`app_secret`) → `access_token`.
4. **Ayla device service** `/dsns/<dsn>/properties.json` → live readings.
   Dream Socks pack them into one `REAL_TIME_VITALS` JSON blob which is decoded
   into the individual entity values.

Credits: the Firebase→Ayla flow and the vitals key mapping follow the approach
of the open-source [`pyowletapi`](https://github.com/ryanbdclark/pyowletapi)
project, re-implemented here as a self-contained async client.

## Disclaimer

Not affiliated with or endorsed by Owlet Baby Care, Inc.
