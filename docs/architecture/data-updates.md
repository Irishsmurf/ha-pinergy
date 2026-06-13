# Data updates & authentication

All polling is owned by `PinergyDataUpdateCoordinator`. It handles login, periodic fetches, the
optional comparison call, and the trickiest part: transparently recovering from session-token
expiry.

## The data container

Each refresh returns a single typed container, consumed by every entity via its `value_fn`:

```python
@dataclass
class PinergyData:
    balance: BalanceResponse
    usage: UsageResponse
    compare: CompareResponse | None
```

## Setup vs. refresh

| Phase | Method | Work |
|---|---|---|
| One-time | `_async_setup` | `client.login()` once, capturing `login_response` (premises number, account type) for device info and statistic IDs. |
| Periodic | `_async_update_data` | Fetch data, then feed long-term statistics. |

Splitting login into `_async_setup` means the account metadata is captured a single time, and
the entities can rely on `coordinator.login_response` being present.

## The fetch

`_fetch` runs synchronously inside the executor and makes up to three client calls:

```python
def _fetch(self) -> PinergyData:
    balance = self.client.get_balance()
    usage = self.client.get_usage()
    compare = None
    if self.config_entry.options.get(CONF_FETCH_COMPARISONS, True):
        try:
            compare = self.client.compare_usage()
        except PinergyError as err:
            _LOGGER.debug("Usage comparison unavailable: %s", err)
    return PinergyData(balance=balance, usage=usage, compare=compare)
```

The comparison call is wrapped in its own `try/except`: it's a non-essential insight that
doesn't exist for every account type, so it must never break the balance refresh.

## Token expiry & the re-login retry

This is the subtlest behaviour in the integration. The Pinergy session token expires
periodically, and the API signals it in **two different shapes**:

| Form | How it arrives |
|---|---|
| `PinergyAuthError` | A clean HTTP 401. |
| `PinergyAPIError` mentioning the auth token | HTTP **200** with `success: false` and a message like *"Auth_token is not correct."* |

A small helper disambiguates the second form:

```python
def _is_token_error(err: PinergyAPIError) -> bool:
    message = str(err).lower()
    return "auth_token" in message or "auth token" in message
```

On either form, the coordinator re-logs in with the stored credentials and retries the fetch
**once** before giving up. Token expiry therefore self-heals without bothering the user.

```text
fetch ──► PinergyAuthError ────────────────┐
      └─► PinergyAPIError (token message) ──┤
                                            ▼
                              client.login() + _fetch()   ← retry once
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              ▼                              ▼                             ▼
     PinergyAuthError              PinergyTimeoutError            success → PinergyData
              │                              │
     ConfigEntryAuthFailed          UpdateFailed (transient)
     (prompts reauth)
```

A `PinergyAPIError` whose message does **not** mention the token is treated as a transient
`UpdateFailed`, not an auth problem — re-logging in wouldn't help.

!!! danger "Never call `client.logout()` to force a re-login"
    `pypinergy`'s `logout()` **discards the stored credentials**, which makes any later
    `login()` fail. The recovery path always calls `login()` directly. This is a deliberate
    constraint, not an oversight.

## Error mapping

| Exception | Mapped to | User-visible result |
|---|---|---|
| `PinergyAuthError` (after retry) | `ConfigEntryAuthFailed` | Reauth prompt |
| `PinergyTimeoutError` | `UpdateFailed` | Temporary "unavailable", auto-retried |
| `PinergyAPIError` (non-token) | `UpdateFailed` | Temporary "unavailable", auto-retried |
| `PinergyHTTPError` | `UpdateFailed` | Temporary "unavailable", auto-retried |

## Statistics never break entities

After a successful fetch, `_async_update_data` calls `async_insert_statistics`. That call is
wrapped so any failure is logged and swallowed:

```python
try:
    await async_insert_statistics(hass, self.login_response.premises_number, data.usage)
except Exception:
    _LOGGER.exception("Error inserting Pinergy long-term statistics")
return data
```

A statistics hiccup must never take the live entities down — the freshly fetched `data` is still
returned. The import mechanics are covered in [Long-term statistics](statistics.md).
