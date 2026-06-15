#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1

mkdir -p .omo/evidence
evidence=.omo/evidence/task-T18-context7-backend-reverse-engineer.http
store=.omo/local-store/chunks.json
rm -f "$store"
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > .omo/evidence/task-T18-server.log 2>&1 &
pid=$!
printf '%s\n' "$pid" > .omo/evidence/task-T18-server.pid
cleanup() {
  if kill "$pid" 2>/dev/null; then
    wait "$pid" 2>/dev/null || true
    printf '%s\n' "cleanup: killed HTTP QA server $pid"
  else
    printf '%s\n' "cleanup: HTTP QA server already exited $pid"
  fi
}
trap cleanup EXIT

i=0
while [ "$i" -lt 40 ]; do
  if curl -sf http://127.0.0.1:8000/healthz >/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.25
done

{
  curl -i 'http://127.0.0.1:8000/api/v2/libs/search?query=helm&libraryName=platform'
  printf '\n---TEXT---\n'
  curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom'
  printf '\n---TEXT-SLASH-VERSION---\n'
  curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform/main&query=valuesFrom'
  printf '\n---TEXT-AT-VERSION---\n'
  curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform@main&query=valuesFrom'
  printf '\n---JSON---\n'
  curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=valuesFrom&type=json'
  printf '\n---NO-MATCH---\n'
  curl -i 'http://127.0.0.1:8000/api/v2/context?libraryId=/internal/platform&query=zzzznomatch'
} | tee "$evidence"

cleanup
trap - EXIT

DOCS_API_KEYS=secret uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > .omo/evidence/task-T18-auth-server.log 2>&1 &
auth_pid=$!
i=0
while [ "$i" -lt 40 ]; do
  if curl -sf http://127.0.0.1:8000/healthz >/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.25
done
curl -i -H 'Authorization: Bearer wrong' 'http://127.0.0.1:8000/api/v2/libs/search?query=helm&libraryName=platform' | tee -a "$evidence"
if kill "$auth_pid" 2>/dev/null; then
  wait "$auth_pid" 2>/dev/null || true
  printf '%s\n' "cleanup: killed auth QA server $auth_pid" | tee -a "$evidence"
fi

grep -q 'HTTP/1.1 200 OK' "$evidence"
grep -q '"searchFilterApplied":false' "$evidence"
grep -q 'content-type: text/plain' "$evidence"
grep -q 'content-type: application/json' "$evidence"
grep -q 'No relevant snippets found' "$evidence"
grep -q 'TEXT-SLASH-VERSION' "$evidence"
grep -q 'TEXT-AT-VERSION' "$evidence"
grep -q 'HTTP/1.1 401 Unauthorized' "$evidence"
printf '%s\n' 'HTTP QA APPROVED'
