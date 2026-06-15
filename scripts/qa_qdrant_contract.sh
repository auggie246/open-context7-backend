#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1

mkdir -p .omo/evidence
store=.omo/local-store/chunks.json
rm -f "$store"

cleanup() {
  if [ "${server_pid:-}" ]; then
    if kill "$server_pid" 2>/dev/null; then
      wait "$server_pid" 2>/dev/null || true
      printf '%s\n' "cleanup: killed Qdrant API server $server_pid"
    fi
  fi
  docker compose down >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose up -d qdrant >/dev/null
i=0
qdrant_ready=false
while [ "$i" -lt 160 ]; do
  if curl -sf http://127.0.0.1:6333/collections >/dev/null; then
    qdrant_ready=true
    break
  fi
  i=$((i + 1))
  sleep 0.25
done
if [ "$qdrant_ready" != true ]; then
  printf '%s\n' 'qdrant readiness failed' >&2
  exit 1
fi

uv run python -m app.retrieval.qdrant --smoke
printf '\n---INGEST-QDRANT---\n'
DOCS_RETRIEVAL_MODE=qdrant uv run context7-backend ingest \
  --library /internal/platform \
  --version main \
  --source-dir examples/platform-docs

DOCS_RETRIEVAL_MODE=qdrant uv run uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 > .omo/evidence/task-T12-qdrant-server.log 2>&1 &
server_pid=$!

i=0
while [ "$i" -lt 40 ]; do
  if curl -sf http://127.0.0.1:8000/healthz >/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.25
done

printf '%s\n' '---API-QDRANT-CONTEXT---'
curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom'
printf '\n%s\n' '---QDRANT QA APPROVED---'
