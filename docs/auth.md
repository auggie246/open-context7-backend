# Open Context7 Backend Auth

Purpose: document the current bearer-token auth behavior for Open Context7 Backend.

Source of truth: `app/auth.py`, `app/settings.py`, `app/main.py`, `app/routes.py`, `docker-compose.yml`, and `tests/test_settings_auth.py`.

## Default Behavior

Auth is disabled by default when `DOCS_API_KEYS` is empty. In that state, protected route dependencies return without requiring a token.

`/healthz` is unauthenticated. It is registered outside the `/api/v2` router and remains available for health checks.

When one or more API keys are configured, `/api/v2/*` routes are protected by bearer auth because the versioned API router depends on `require_bearer_auth`.

## Configuring Keys

Set `DOCS_API_KEYS` to a comma-separated list:

```sh
DOCS_API_KEYS=<key>
```

Clients send the selected key with the standard bearer format:

```sh
Authorization: Bearer <key>
```

Missing tokens, malformed authorization headers, and invalid tokens return HTTP 401 with a JSON body containing `error: unauthorized`.

## Constant-Time Comparison

`app/auth.py` compares presented tokens against every configured key with `secrets.compare_digest`. It does not stop at the first matching key. Keep that constant-time comparison guarantee intact when changing auth code.

## Response Headers

The backend does not emit `X-Context7-Auth-Prompt` on auth failures. Tests assert that missing and invalid bearer responses do not include that header.

## Docker Compose Default

`docker-compose.yml` sets:

```sh
DOCS_API_KEYS=${DOCS_API_KEYS:-dev-local-secret}
```

That means Compose-provided `/api/v2/*` calls require `Authorization: Bearer dev-local-secret` unless the caller overrides `DOCS_API_KEYS`. `/healthz` remains unauthenticated.

## Scope Boundaries

OIDC is not implemented. OpenID Connect and team auth are out of scope for the current backend and are not planned behavior in this repository. Do not document them as available behavior unless app code and tests change first.

## Gotchas

- `/healthz` remains unauthenticated even when `DOCS_API_KEYS` is set.
- Compose sets `DOCS_API_KEYS` to `dev-local-secret` unless overridden.
- The backend does not emit `X-Context7-Auth-Prompt`; clients should handle normal 401 responses.

## Verification

Useful focused checks:

```sh
rg -q '/healthz.*unauthenticated|X-Context7-Auth-Prompt|dev-local-secret|Bearer' docs/auth.md
DOCS_API_KEYS=dev-local-secret PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_settings_auth.py
```

## Next

- Read [configuration](configuration.md) for environment variables.
- Read [API](api.md) for endpoint-specific auth behavior.
