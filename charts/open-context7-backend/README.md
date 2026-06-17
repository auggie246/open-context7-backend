# open-context7-backend Helm chart

This chart deploys the Context7-compatible FastAPI backend. By default it also
runs Qdrant as a sidecar container in the same Deployment, matching the local
Docker Compose stack.

## Install

```sh
helm install open-context7-backend ./charts/open-context7-backend
```

The default API image is `ghcr.io/auggie246/open-context7-backend` and the
default tag is the chart `appVersion`.

## Qdrant

Bundled Qdrant is controlled by `qdrant.enabled`.

```sh
helm install open-context7-backend ./charts/open-context7-backend \
  --set qdrant.enabled=false \
  --set config.qdrantUrl=http://qdrant:6333
```

When `qdrant.enabled=true`, the backend uses `http://127.0.0.1:6333` inside the
pod. When it is false, set `config.qdrantUrl` for an external Qdrant service.

## Auth

`config.apiKeys` defaults to `dev-local-secret`, matching Docker Compose. Set it
to an empty string to disable API key auth, or set `config.existingApiKeysSecret`
to read `DOCS_API_KEYS` from an existing Secret.
