# SCRIPTS KNOWLEDGE BASE

**Generated:** 2026-06-18

## OVERVIEW

Shell and Node contract harnesses for quality gates, real HTTP/MCP/Qdrant QA, plan compliance, and scope fidelity.

## WHERE TO LOOK

| Script | Role | Notes |
| --- | --- | --- |
| `verify_code_quality.sh` | local quality gate | Ruff, BasedPyright, pytest, bytecode cleanup |
| `qa_full.sh` | full QA orchestrator | writes `.omo/evidence/*`, starts/stops services |
| `qa_http_contract.sh` | real HTTP API contract | starts uvicorn on `127.0.0.1:8000` |
| `qa_qdrant_contract.sh` | Qdrant integration contract | starts Compose Qdrant on `127.0.0.1:6333` |
| `qa_mcp_contract.sh` | MCP contract wrapper | builds vendored package, runs Node harness |
| `qa_mcp_contract.mjs` | MCP stdio client | newline-delimited JSON SDK behavior |
| `verify_plan_compliance.sh` | plan acceptance strings | checks repo surfaces and required markers |
| `verify_scope_fidelity.sh` | scope guard | forbids out-of-scope drift |

## CONVENTIONS

- Keep scripts POSIX `sh` unless a file is already Node (`.mjs`).
- Set `PYTHONDONTWRITEBYTECODE=1` in Python-running scripts.
- Use traps for every background `uvicorn` or Compose-backed process.
- Evidence files under `.omo/evidence/` are local agent artifacts; do not commit them unless explicitly requested.
- Contract scripts should print their `... QA APPROVED` marker only after all assertions pass.

## ANTI-PATTERNS

- Do not leave ports `8000` or `6333` bound after QA scripts finish.
- Do not run `docker compose down -v` unless intentionally deleting Qdrant data.
- Do not change contract scripts to skip auth, response-shape, or cleanup assertions.
- Do not edit vendored MCP source as part of MCP contract QA; build/use it as reference.

## COMMANDS

```bash
rtk scripts/verify_code_quality.sh
rtk scripts/qa_http_contract.sh
rtk scripts/qa_qdrant_contract.sh
rtk scripts/qa_mcp_contract.sh
rtk scripts/qa_full.sh
```
