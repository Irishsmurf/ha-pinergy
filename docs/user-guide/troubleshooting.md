# Troubleshooting

## A sensor shows `unavailable`

The period and comparison sensors are deliberately `unavailable` until the meter reports data
for that window:

- **Today's / week's / month's usage and cost** become available once the meter posts the first
  reading for that period.
- **Average home usage/cost today** become available only when the comparison endpoint returns
  data for your account — see [Options](options.md#fetch-average-home-comparisons).

If a value is genuinely missing rather than not-yet-reported, check the Pinergy app shows it
too; the integration can only surface what the API returns.

## I was asked to re-authenticate

This happens when your **Pinergy password changed**. Routine session-token expiry is handled
automatically and shouldn't prompt you. Follow the steps in
[Configuration → Re-authentication](../getting-started/configuration.md#re-authentication).

## "This Pinergy account is already configured"

The integration keys each entry to a premises number, so an account can only be added once. If
you're trying to re-add it, remove the existing **Pinergy** entry first.

## Data looks stale

- Check the [update interval](options.md#update-interval) — the default is 30 minutes.
- The meter only reports periodically; between reports the same values are re-fetched.
- Use **Developer Tools → Statistics** to confirm the long-term statistics are advancing.

## Energy Dashboard isn't updating

- New statistics can take up to two hours to appear in the Energy Dashboard.
- Confirm the **recorder** integration is enabled (it is by default).
- Verify you selected the **Pinergy energy consumption** / **Pinergy energy cost** statistics —
  see [Energy Dashboard](energy-dashboard.md).

## Collecting diagnostics

The integration supports Home Assistant's built-in diagnostics download, with personal data
redacted:

1. Go to **Settings → Devices & Services → Pinergy**.
2. Open the **⋮** menu on the integration entry.
3. Select **Download diagnostics**.

The download includes the (redacted) config entry, login response, and last fetched data —
useful to attach when [opening an issue](https://github.com/Irishsmurf/ha-pinergy/issues).

!!! warning "What is redacted"
    Identifiers and personal fields — auth tokens, email, password, premises number, Pinergy
    ID, mobile number, and name fields — are stripped before the file is written. Always skim a
    diagnostics file before sharing it publicly, just in case.

## Enabling debug logs

Add the following to `configuration.yaml` and restart, or use **Settings → Devices & Services →
Pinergy → ⋮ → Enable debug logging**:

```yaml
logger:
  default: info
  logs:
    custom_components.pinergy: debug
    pypinergy: debug
```

Debug logs include token-refresh attempts and any comparison-endpoint failures, which are the
most common things worth inspecting.

## Still stuck?

Open an issue at
[github.com/Irishsmurf/ha-pinergy/issues](https://github.com/Irishsmurf/ha-pinergy/issues) with
your Home Assistant version, the integration version, a description of the problem, and (ideally)
a redacted diagnostics file.
