# Owlet API — reverse-engineering notes

These documents capture how the **Owlet Dream** iOS app (v3.48.0, build 42146)
talks to the Owlet cloud, reconstructed from mitmproxy-style traffic captures.
They are the basis for the Home Assistant integration in
[`../custom_components/owlet`](../custom_components/owlet).

> **Redaction note.** All captures were taken from a real account. Every
> secret — passwords, Firebase ID/refresh tokens, Ayla access tokens, push
> tokens, account IDs, profile IDs, device serial numbers — has been redacted
> and replaced with named placeholders (e.g. `<ACCOUNT_ID>`, `<ID_TOKEN>`,
> `<DSN>`). Only non-secret, app-wide constants that are identical for every
> user (public Firebase API keys, Ayla app IDs) are shown verbatim, because
> they are required to reproduce the flow and are not account-specific.

## Contents

| Document | What it covers |
|----------|----------------|
| [`authentication.md`](authentication.md) | The 3-step Firebase → Ayla login chain and token refresh. |
| [`endpoints.md`](endpoints.md) | Every host/endpoint seen, grouped by service, with purpose. |
| [`data-model.md`](data-model.md) | Live vitals, sleep, and insight response schemas + field decoding. |
| [`placeholders.md`](placeholders.md) | The redaction key: what each `<PLACEHOLDER>` stood for. |

## High-level architecture

```
         ┌─────────────────────────────┐
         │  Owlet Dream app (iOS)       │
         └──────────────┬──────────────┘
                        │ 1. email+password
            ┌───────────▼────────────┐
            │ Google Firebase         │  identitytoolkit / securetoken
            │ (owletcare-prod-eu)     │  → idToken + refreshToken
            └───────────┬────────────┘
                        │ 2. idToken
            ┌───────────▼────────────┐
            │ Ayla SSO                │  ayla-sso[.eu].owletdata.com/mini/
            │                         │  → mini_token
            └───────────┬────────────┘
                        │ 3. mini_token + app_id/app_secret
            ┌───────────▼────────────┐
            │ Ayla device service     │  ads-*-1a2039d9.aylanetworks.com
            │ (ADS)                   │  → access_token, LIVE vitals
            └─────────────────────────┘

   Owlet "data" micro-services (Bearer idToken), used for history/insights:
     • vital-data.eu.owletdata.com   — aggregated vitals (HR/O2/movement)
     • sleep-data.eu.owletdata.com   — sleep sessions, states, body positions
     • accounts.eu.owletdata.com     — profiles, insights, morning reports
```

Two token types are in play:

- **Firebase `idToken`** (a JWT) — used directly as the `Authorization` value
  for the Owlet `*-data`/`accounts` micro-services and for the Ayla SSO mini
  endpoint.
- **Ayla `access_token`** — used as `Authorization: auth_token <token>` for the
  Ayla device service (ADS), which is where **live** heart-rate / oxygen come
  from.
