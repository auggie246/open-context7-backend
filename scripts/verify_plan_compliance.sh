#!/usr/bin/env sh
set -eu

plan=${1:-.omo/plans/context7-backend-reverse-engineer.md}
vendor=src/context7--upstash-context7-mcp-3.2.1
after=.omo/evidence/vendor-context7-after.sha256

require_file() {
  test -s "$1"
}

require_rg() {
  rg -q "$1" "$2"
}

require_file "$plan"
require_file pyproject.toml
require_file Dockerfile
require_file docker-compose.yml
require_file app/main.py
require_file app/routes.py
require_file app/catalog.py
require_file app/ingest/parser.py
require_file app/retrieval/qdrant.py
require_file app/retrieval/lexical.py
require_file scripts/qa_http_contract.sh
require_file scripts/qa_mcp_contract.sh
require_file scripts/qa_mcp_contract.mjs
require_file scripts/qa_qdrant_contract.sh
require_file .omo/evidence/vendor-context7-before.sha256

require_rg 'prefix="/api/v2"' app/routes.py
require_rg '"/libs/search"' app/routes.py
require_rg '"/context"' app/routes.py
require_rg 'searchFilterApplied: bool = False' app/models.py
require_rg 'DOCS_' README.md
require_rg 'CONTEXT7_API_URL=http://localhost:8000/api' README.md
require_rg 'X-Context7-Auth-Prompt' README.md
require_rg 'create_payload_index' app/retrieval/qdrant.py
require_rg 'query_points' app/retrieval/qdrant.py
require_rg 'FilterSelector' app/retrieval/qdrant.py
require_rg 'DOCS_RETRIEVAL_MODE: qdrant' docker-compose.yml
require_rg 'DOCS_API_KEYS' docker-compose.yml
require_rg '127.0.0.1:8000:8000' docker-compose.yml
require_rg '127.0.0.1:6333:6333' docker-compose.yml
require_rg 'compare_digest' app/auth.py
require_rg 'is_relative_to' app/cli.py
! rg -q 'reportAny = "none"' pyproject.toml
require_rg 'DOCS_RETRIEVAL_MODE=qdrant' scripts/qa_qdrant_contract.sh
require_rg 'task-T12-qdrant-server.log' scripts/qa_qdrant_contract.sh
require_rg 'SDK_STDIO_FRAMING' scripts/qa_mcp_contract.mjs
require_rg 'JSON.stringify\(message\) \+ .\\n' \
  "$vendor/node_modules/.pnpm/@modelcontextprotocol+sdk@1.29.0_zod@4.4.3/node_modules/@modelcontextprotocol/sdk/dist/esm/shared/stdio.js"
require_rg 'tee .*evidence' scripts/qa_http_contract.sh

test ! -d k8s
test ! -d kubernetes
test ! -d app/static
test ! -d app/templates
! rg -q 'OIDC|OpenID|oauth|sitemap|BeautifulSoup|playwright|LLM|ChatOpenAI' app tests scripts README.md

scripts/vendor_manifest.sh "$vendor" > "$after"
diff -u .omo/evidence/vendor-context7-before.sha256 "$after"

if [ -s .omo/evidence/task-T18-context7-backend-reverse-engineer.http ]; then
  require_rg 'HTTP/1.1 200 OK' .omo/evidence/task-T18-context7-backend-reverse-engineer.http
  require_rg '"searchFilterApplied":false' .omo/evidence/task-T18-context7-backend-reverse-engineer.http
  require_rg 'TEXT-SLASH-VERSION' .omo/evidence/task-T18-context7-backend-reverse-engineer.http
  require_rg 'TEXT-AT-VERSION' .omo/evidence/task-T18-context7-backend-reverse-engineer.http
  require_rg 'HTTP/1.1 401 Unauthorized' .omo/evidence/task-T18-context7-backend-reverse-engineer.http
fi

if [ -s .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt ]; then
  require_rg '/internal/platform' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
  require_rg 'Available Libraries' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
  require_rg 'TITLE:' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
  require_rg 'MCP QA APPROVED' .omo/evidence/task-T19-context7-backend-reverse-engineer.mcp.txt
fi

if [ -s .omo/evidence/final-qdrant-qa.txt ]; then
  require_rg 'payload_indexes:' .omo/evidence/final-qdrant-qa.txt
  require_rg 'query_results:1' .omo/evidence/final-qdrant-qa.txt
  require_rg 'API-QDRANT-CONTEXT' .omo/evidence/final-qdrant-qa.txt
  require_rg 'TITLE:' .omo/evidence/final-qdrant-qa.txt
  require_rg 'QDRANT QA APPROVED' .omo/evidence/final-qdrant-qa.txt
fi

printf '%s\n' 'PLAN COMPLIANCE APPROVED'
