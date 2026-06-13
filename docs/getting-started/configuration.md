# Configuration

Pinergy is configured entirely through the Home Assistant UI. There is **no
`configuration.yaml` setup** — it is neither required nor supported.

## Add the integration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Pinergy** and select it.
3. Enter the **email** and **password** you use to sign in to the Pinergy app.
4. Select **Submit**.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pinergy)

On success, the integration validates your credentials against the Pinergy API and creates a
single **Pinergy Account** device that owns every entity. The account's premises number is used
as the unique ID, so the same account can't be added twice.

### What happens on first run

| Step | Detail |
|---|---|
| Login | Credentials are verified before the entry is created. |
| Device | A "Pinergy Account" device is created (model = your account/meter type). |
| First refresh | Balance, usage, and (optionally) comparison data are fetched. |
| Statistics | The last seven days of usage are imported into long-term statistics. |

## Credential errors

The config flow reports common problems inline:

| Message | Meaning | Fix |
|---|---|---|
| **Invalid email address or password** | The Pinergy API rejected your credentials. | Re-check what you use in the Pinergy app. |
| **Failed to connect to the Pinergy API** | A network/timeout/server error occurred. | Try again; check the Pinergy app is online. |
| **This Pinergy account is already configured** | The same premises is already set up. | Remove the existing entry first if you're re-adding. |

## Re-authentication

Your Pinergy session token expires periodically, and the integration refreshes it
automatically using your stored credentials — you won't normally notice.

If your **password changes**, the stored credentials become invalid and Home Assistant raises a
repair / reauth prompt:

1. A notification appears under **Settings → Devices & Services**.
2. Select **Reconfigure** / **Re-authenticate**.
3. Enter your **new password** (the email is shown but fixed).

The premises number is checked again on reauth, so you can't accidentally point an existing
entry at a different account.

!!! info "Why only the password?"
    Re-authentication keeps the original email and only asks for the password, because the
    config entry is keyed to a specific Pinergy account (premises). Changing the account means
    adding a new integration entry instead.

## Adjusting behaviour

After setup you can tune the polling interval and comparison fetching from the options flow —
see [Options](../user-guide/options.md).
