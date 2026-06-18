# HELM CHART KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

Helm chart for deploying the docs API with optional bundled Qdrant; release workflow packages this subtree to GitHub Pages.

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| Chart metadata | `Chart.yaml` | app/chart version and description |
| Defaults | `values.yaml` | image, service, env config, Qdrant defaults |
| Workloads | `templates/deployment.yaml`, `templates/qdrant-statefulset.yaml` | API and Qdrant runtime shape |
| Services | `templates/service.yaml`, `templates/qdrant-service.yaml` | API/Qdrant ports |
| Secrets | `templates/secret.yaml` | `DOCS_API_KEYS` behavior |
| Release | `.github/workflows/release-helm-chart.yml` | chart releaser on `main` changes under `charts/**` |

## CONVENTIONS

- Keep chart defaults aligned with Compose where behavior overlaps: deterministic embeddings, qdrant retrieval mode, Qdrant `v1.12.6`, API port `8000`, Qdrant port `6333`.
- `values.yaml` defaults are testable deployment contract, not loose examples.
- Prefer Secret-backed API keys for real deployments; the default `dev-local-secret` is local/dev parity only.
- If chart behavior changes, update deployment docs and consider `tests/test_deployment_compose.py` parity where relevant.

## ANTI-PATTERNS

- Do not claim this repo has a Kubernetes deployment beyond this Helm chart.
- Do not remove Qdrant as a separate service without changing docs, tests, and QA scripts.
- Do not expose Qdrant unintentionally when defaults say bundled/local behavior.

## COMMANDS

```bash
rtk helm lint charts/open-context7-backend
rtk git diff -- charts/open-context7-backend .github/workflows/release-helm-chart.yml
```
