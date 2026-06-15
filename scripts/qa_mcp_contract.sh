#!/usr/bin/env sh
set -eu
export PYTHONDONTWRITEBYTECODE=1

mkdir -p .omo/evidence
if command -v pnpm >/dev/null 2>&1; then
  pnpm_cmd=pnpm
else
  pnpm_cmd="corepack pnpm"
fi

CI=true $pnpm_cmd --dir src/context7--upstash-context7-mcp-3.2.1 --filter @upstash/context7-mcp build
uv run context7-backend ingest --library /internal/platform --version main --source-dir examples/platform-docs

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 > .omo/evidence/task-T19-server.log 2>&1 &
pid=$!
cleanup() {
  if kill "$pid" 2>/dev/null; then
    wait "$pid" 2>/dev/null || true
    printf '%s\n' "cleanup: killed MCP QA backend $pid"
  else
    printf '%s\n' "cleanup: MCP QA backend already exited $pid"
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

node scripts/qa_mcp_contract.mjs | tee .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
grep -q '/internal/platform' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
grep -q 'Available Libraries' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
grep -q 'TITLE:' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
grep -q 'MCP QA APPROVED' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
cleanup | tee -a .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
trap - EXIT
