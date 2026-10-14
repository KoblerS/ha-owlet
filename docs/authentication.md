# Authentication flow

The app authenticates in three network steps, then refreshes with a fourth.
All example tokens/IDs are redacted — see [`placeholders.md`](placeholders.md).

## Step 1 — Firebase password sign-in

Exchanges the account email + password for a Firebase ID token and refresh
token. The region determines the API key and the Firebase project.

```
POST https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=<FIREBASE_API_KEY>
Content-Type: application/json
User-Agent: FirebaseAuth.iOS/12.4.0 com.owletcare.Sleep/3.48.0 ...
X-Firebase-GMPID: 1:395737756031:ios:bb3e66338b246bda24aa4a
X-Ios-Bundle-Identifier: com.owletcare.Sleep

{
  "email": "<EMAIL>",
  "password": "<PASSWORD>",
  "returnSecureToken": true,
  "clientType": "CLIENT_TYPE_IOS"
}
```

Response (200) contains `idToken`, `refreshToken`, `expiresIn` (gzip in the
capture; shape is the standard identitytoolkit payload).

The HA integration sends the Android variant of these headers
(`X-Android-Package` / `X-Android-Cert`), which the endpoint also accepts.

### Public (non-secret) region constants

These are the same for every user and are required to reproduce the flow:

| Region | Firebase API key | Firebase project |
|--------|------------------|------------------|
| Europe | `AIzaSyCCVPALBrbhZIPArEIBHbsWbSZKloOUVRk` | `owletcare-prod-eu` |
| World  | `AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA` | `owletcare-prod` |

> The EU key above comes from the v3.48.0 capture and supersedes older keys
> seen in third-party libraries.

## Step 2 — Ayla mini token

The Firebase `idToken` is presented (raw, **not** `Bearer`-prefixed) to the
region's Ayla SSO endpoint, which returns a short-lived `mini_token`.

```
GET https://ayla-sso.eu.owletdata.com/mini/
Authorization: <ID_TOKEN>
User-Agent: OwletDream/3.48.0(42146) (iPhone, iOS 27.0.1)
```

Response (200):

```json
{ "mini_token": "<MINI_TOKEN>" }
```

Rate limited: observed `x-ratelimit-limit: 10, 10;w=60, 20;w=60, 40;w=60`.

World region uses `https://ayla-sso.owletdata.com/mini/`.

## Step 3 — Ayla token sign-in

The `mini_token` plus the mobile app's Ayla credentials are exchanged for an
Ayla `access_token`.

```
POST https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in
Content-Type: application/json

{
  "app_id": "OwletCare-Android-EU-fw-id",
  "app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
  "provider": "owl_id",
  "token": "<MINI_TOKEN>"
}
```

Response (200) contains `access_token`, `refresh_token`, `expires_in`.

| Region | token_sign_in host | app_id |
|--------|--------------------|--------|
| Europe | `user-field-eu-1a2039d9.aylanetworks.com` | `OwletCare-Android-EU-fw-id` |
| World  | `user-field-1a2039d9.aylanetworks.com` | `sso-prod-3g-id` |

> `app_id` / `app_secret` are public app-wide values embedded in the mobile
> apps — not per-user secrets.

## Step 4 — Refreshing

When the Ayla `access_token` expires, the Firebase refresh token mints a new
`idToken` via Google securetoken, and steps 2–3 are repeated.

```
POST https://securetoken.googleapis.com/v1/token?key=<FIREBASE_API_KEY>
Content-Type: application/x-www-form-urlencoded

grantType=refresh_token&refreshToken=<REFRESH_TOKEN>
```

Response contains a new `id_token` and `refresh_token`. Then re-run step 2
(`/mini/`) and step 3 (`token_sign_in`).

## Using the tokens

| Target service | Header |
|----------------|--------|
| Ayla device service (ADS, live vitals) | `Authorization: auth_token <ACCESS_TOKEN>` |
| `*-data` / `accounts` Owlet services (history/insights) | `Authorization: Bearer <ID_TOKEN>` |

## Side services (not needed by the integration)

- `auth.split.io` — Split.io feature-flag SDK auth (`Bearer <SPLIT_SDK_KEY>`).
- `logs.owletdata.com/v1/index/mobile` — app telemetry/log upload.
- `*.app-analytics-services.com`, Braze, Sentry — analytics/crash reporting.

The JWT `idToken` decodes (header + payload only; signature redacted) to:

```json
{
  "iss": "https://securetoken.google.com/owletcare-prod-eu",
  "aud": "owletcare-prod-eu",
  "user_id": "<ACCOUNT_ID>",
  "sub": "<ACCOUNT_ID>",
  "email": "<EMAIL>",
  "email_verified": true,
  "auth_time": <EPOCH>, "iat": <EPOCH>, "exp": <EPOCH>,
  "firebase": { "sign_in_provider": "password" }
}
```

Observed token lifetime (`exp - iat`) was **3600 s**.
