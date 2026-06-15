#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1

mkdir -p .omo/evidence
docker compose down >/dev/null 2>&1 || true
uv run pytest -q -p no:cacheprovider
uv run ruff check app tests
uv run basedpyright app tests
docker compose config >/dev/null
scripts/qa_qdrant_contract.sh > .omo/evidence/final-qdrant-qa.txt
scripts/qa_http_contract.sh > .omo/evidence/final-real-qa.http
scripts/qa_mcp_contract.sh > .omo/evidence/final-real-qa.mcp.txt
scripts/verify_plan_compliance.sh .omo/plans/context7-backend-reverse-engineer.md > .omo/evidence/final-plan-compliance.md
scripts/verify_code_quality.sh > .omo/evidence/final-code-quality.md
scripts/verify_scope_fidelity.sh > .omo/evidence/final-scope-fidelity.md
if lsof -i :8000 >/dev/null 2>&1; then
  lsof -i :8000
  exit 1
fi
printf '%s\n' 'FULL QA APPROVED'
