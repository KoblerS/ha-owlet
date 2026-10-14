# Redaction key

Every secret or account-identifying value from the original captures was
replaced with a named placeholder. This is the legend. **No real values are
stored in this repository** — the raw capture `.zip`s and `extracted_*`
folders are git-ignored.

| Placeholder | What it was | Sensitivity |
|-------------|-------------|-------------|
| `<EMAIL>` | Account login email | Personal data |
| `<PASSWORD>` | Account password | **Secret** |
| `<ID_TOKEN>` | Firebase ID token (JWT) | **Secret** (short-lived) |
| `<REFRESH_TOKEN>` | Firebase refresh token | **Secret** (long-lived) |
| `<MINI_TOKEN>` | Ayla SSO mini token | **Secret** (short-lived) |
| `<ACCESS_TOKEN>` | Ayla device-service access token | **Secret** |
| `<ACCOUNT_ID>` | Owlet/Firebase user id (`user_id`/`sub`) | Account identifier |
| `<PROFILE_ID>` | Child profile id | Account identifier |
| `<DSN>` | Device serial number of the sock | Device identifier |
| `<CLIENT_ID>` | App client UUID (push registration) | Device identifier |
| `<PUSH_TOKEN>` | FCM/APNs push token | **Secret** |
| `<SPLIT_SDK_KEY>` | Split.io SDK bearer key | **Secret** |
| `<EPOCH>` | A unix timestamp | — |
| `<KEY>` / `<FIREBASE_API_KEY>` | Region Firebase API key | **Public** constant (shown verbatim where needed) |

## Not redacted (public app-wide constants)

These are embedded identically in every copy of the Owlet app and are required
to reproduce the flow. They are not account-specific secrets:

- Firebase API keys (EU / World)
- Firebase project IDs (`owletcare-prod-eu`, `owletcare-prod`)
- Ayla `app_id` / `app_secret` (EU / World)
- Firebase GMP app id, iOS bundle id (`com.owletcare.Sleep`)

## If you capture your own traffic

Keep the raw captures **out of git** (the repo `.gitignore` already excludes
`*.zip` and `extracted_*/`). They contain live tokens that grant access to the
account until they expire or are rotated. Rotate your password if a capture
containing `<PASSWORD>` or a `<REFRESH_TOKEN>` ever leaks.
