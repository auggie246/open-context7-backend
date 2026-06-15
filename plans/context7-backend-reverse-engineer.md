# Self-Hosted Context7-Compatible Doc Server — Design

**Goal:** Run Context7-style documentation retrieval fully inside an air-gapped network: your own ingestion, your own index, your own retrieval API. No calls to context7.com.

---

## 0. Key finding: you don't need to fork the client

Reading the current `upstash/context7` source (`packages/mcp/src/lib/constants.ts`):

```ts
export const CONTEXT7_API_BASE_URL = process.env.CONTEXT7_API_URL || "https://context7.com/api";
```

The official MCP server already supports a custom backend via the **`CONTEXT7_API_URL`** environment variable. So the architecture is:

```
MCP client (OpenCode / Claude Code / Cursor)
        │  stdio or streamable-http
        ▼
@upstash/context7-mcp  (unmodified, vendored npm package)
        │  CONTEXT7_API_URL=https://docs-api.internal/api
        ▼
YOUR BACKEND (FastAPI)  ──►  Vector DB (Qdrant)
        │                          ▲
        ▼                          │
Embedding service (TEI/vLLM)   Ingestion pipeline (offline jobs)
```

A *light fork* is still recommended (see §5) to strip auth-prompt/telemetry behavior and rebrand tool descriptions, but it's ~20 lines of deletions, not a rewrite.

---

## 1. The API contract you must implement

The MCP server makes exactly **two HTTP GET calls**. Implement these and the client works unmodified.

### 1.1 `GET {BASE}/v2/libs/search`

Query params:

| param | meaning |
|---|---|
| `query` | the user's task/question (use for relevance ranking) |
| `libraryName` | library name to match against the catalog |

Response: `200` with JSON

```jsonc
{
  "results": [
    {
      "id": "/internal/my-platform-docs",   // your library ID, format /org/project[/version]
      "title": "My Platform Docs",
      "description": "Internal platform engineering docs",
      "branch": "main",
      "lastUpdateDate": "2026-06-01T00:00:00Z",
      "state": "finalized",                  // must be "finalized" to be usable
      "totalTokens": 120000,
      "totalSnippets": 450,
      "stars": 0,                            // optional
      "trustScore": 10,                      // optional
      "benchmarkScore": 95,                  // optional
      "versions": ["v1.2.0", "v1.1.0"]       // optional
    }
  ],
  "error": null
}
```

Errors: return JSON `{ "message": "..." }` with 404/429/401 — the client surfaces `message` verbatim.

### 1.2 `GET {BASE}/v2/context`

Query params:

| param | meaning |
|---|---|
| `query` | natural-language question |
| `libraryId` | exact ID from search, e.g. `/internal/my-platform-docs` or `/org/project/v1.2.0` |

Response: `200` with **plain text** (not JSON) — the body is injected directly into the LLM context. An empty body triggers the client's "documentation not found" message. Recommended snippet format (matches what Context7 emits, so models are already primed for it):

```
TITLE: Configure HelmRelease with valuesFrom
DESCRIPTION: How to reference a ConfigMap for chart values in FluxCD.
SOURCE: https://git.internal/platform/docs/-/blob/main/flux/helmrelease.md
LANGUAGE: yaml
CODE:
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
...
----------------------------------------
TITLE: ...
```

### 1.3 Headers the client sends (handle or ignore)

- `Authorization: Bearer <key>` — only if `CONTEXT7_API_KEY` is set. Use this for your own auth (per-team static keys, or validate against your IdP).
- `X-Context7-Source`, `X-Context7-Server-Version`, `X-Context7-Client-IDE`, `X-Context7-Transport`, `mcp-client-ip` (encrypted) — safe to ignore; useful free telemetry if you log them.
- Response header `X-Context7-Auth-Prompt: 1` triggers a sign-in elicitation in the client — **never set it**.

---

## 2. Backend service (FastAPI)

Single stateless container, ~300 lines.

```
app/
├── main.py            # FastAPI app, /v2/libs/search, /v2/context, /healthz
├── retrieval.py       # hybrid search + rerank
├── catalog.py         # library registry (Postgres table or YAML-in-git)
├── auth.py            # bearer-key middleware (optional)
└── settings.py        # env config
```

### `/v2/libs/search` logic
1. Fuzzy/BM25 match `libraryName` against the catalog (name, aliases, description).
2. Optionally embed `query` and boost libraries whose centroid is close — usually overkill; name matching covers 95% of cases.
3. Return all matches; the *LLM* picks one (that's how the official tool works — selection logic lives in the tool description).

### `/v2/context` logic
1. Resolve `libraryId` (+ optional `/version` suffix) → collection + filter.
2. **Hybrid retrieval:** dense (embedding) + sparse (BM25/SPLADE) over chunks, RRF fusion. Qdrant does this natively.
3. **Rerank** top ~50 → top ~15 with a cross-encoder (e.g. `bge-reranker-v2-m3` on TEI). This is the single biggest quality lever; Context7's "intelligent reranked context" is essentially this step.
4. Concatenate snippets in the format above, capped at a token budget (env: `MAX_CONTEXT_TOKENS`, default ~10k).

---

## 3. Ingestion pipeline (offline jobs, not in the request path)

Run as CI jobs or CronJobs per library. Each library is defined by a config (mirroring Context7's `context7.json` idea):

```yaml
# libraries/my-platform-docs.yaml
id: /internal/my-platform-docs
title: My Platform Docs
source:
  type: git                      # git | dir | sitemap
  url: https://git.internal/platform/docs.git
  branch: main
  include: ["docs/**/*.md", "**/*.mdx"]
  exclude: ["**/CHANGELOG*"]
versions: [main, v1.2.0]
```

Pipeline stages:

1. **Fetch** — clone/pull from internal git, or read a mounted directory. (HTML sources: crawl with a sitemap + readability extraction; keep this for vendor docs you've mirrored inside the air gap.)
2. **Parse & chunk** — heading-aware Markdown chunking; **extract fenced code blocks as first-class snippets** with their preceding heading/paragraph as TITLE/DESCRIPTION. This snippet-centric structure is what makes Context7 output good for coding agents — don't just blind-window the text.
   - Target ~200–500 token chunks, code blocks kept intact (never split a fence).
3. **Embed** — batch through the embedding service.
4. **Upsert** — into Qdrant collection `docs`, payload: `{library_id, version, title, description, source_url, language, kind: code|prose, text}`. Index `library_id`+`version` as payload filters.
5. **Update catalog** — set `state: finalized`, `totalSnippets`, `lastUpdateDate`.

Idempotency: hash each chunk (`sha256(library_id+source_path+content)`) as the point ID, so re-ingestion only writes deltas and deletes orphans.

Don't build the parser from scratch unless you want to — `arabold/docs-mcp-server` and `rakuv3r/open-context7` both have usable ingestion code to crib from; you'd be wrapping it behind the Context7 API shape.

---

## 4. Model serving (all in-network)

| Component | Recommendation | Notes |
|---|---|---|
| Embeddings | `BAAI/bge-m3` or `nomic-embed-text-v1.5` on **Text Embeddings Inference (TEI)** | CPU-viable; GPU if you have it. ~1024-dim dense. bge-m3 also emits sparse vectors → free hybrid search. |
| Reranker | `BAAI/bge-reranker-v2-m3` on TEI | Biggest quality win. Skippable for v1. |
| Vector DB | **Qdrant** | Single binary, hybrid search, payload filtering, snapshots for backup. pgvector is fine if you'd rather not add a component. |

Air-gap transfer: pull model weights + container images outside, push through your artifact registry / one-way transfer process. Everything above is Apache-2/MIT licensed.

---

## 5. The (minimal) MCP fork

Vendor `@upstash/context7-mcp` into your internal npm registry, then patch:

1. **Delete** `lib/auth/`, Clerk constants, `maybeElicitAuthSignIn` calls, and the `X-Context7-Auth-Prompt` handling — dead weight pointing at their SaaS.
2. **Delete/no-op** `lib/encryption.ts` client-IP encryption (it encrypts toward their public key).
3. **Rewrite tool descriptions** — remove "do not include confidential information" warnings (yours is internal; you *want* internal terms in queries) and the context7.com URLs in error fallbacks.
4. **Default `CONTEXT7_API_URL`** to your endpoint so clients need zero config.
5. Keep the tool names (`resolve-library-id`, `query-docs`) and schemas identical — clients and prompts that already know Context7 keep working.

Build, publish as `@yourorg/docs-mcp` internally. Total diff: small enough to rebase when upstream releases.

Alternatively, skip the fork entirely for v1: run the stock package with `CONTEXT7_API_URL` set. The auth-prompt code only fires if your backend sends the header, and the proxy/CA-cert support (`HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`) already handles internal TLS.

---

## 6. Deployment sketch (Kubernetes)

- **docs-api** (FastAPI): Deployment, 2 replicas, HPA on CPU. Stateless.
- **qdrant**: StatefulSet, PVC, nightly snapshot CronJob to object storage.
- **tei-embed / tei-rerank**: Deployments (GPU node selector if available).
- **ingest**: CronJob per library or a single job iterating the catalog repo; catalog configs live in git → GitOps-friendly.
- **Ingress/TLS**: internal CA cert; clients set `NODE_EXTRA_CA_CERTS` if running stdio MCP locally.
- **Auth**: start with static bearer keys in a Secret; graduate to OIDC token validation at the API if needed.

For LLM-gateway setups (e.g. LiteLLM MCP gateway): register the forked MCP server as a streamable-HTTP server behind the gateway instead of running stdio per-client — one deployment, centrally logged.

---

## 7. Build order

1. **Day 1–2:** Qdrant + TEI up; FastAPI with the two endpoints returning hardcoded data; point stock MCP at it via `CONTEXT7_API_URL`; confirm end-to-end in your editor.
2. **Day 3–5:** Ingestion for one Markdown git repo (chunker + embed + upsert + catalog).
3. **Week 2:** Hybrid search + reranker; snippet formatting polish; 3–5 real libraries.
4. **Later:** versioned libraries, HTML/sitemap sources, per-team auth, the client fork, eval harness (golden queries → recall@k on known doc sections).

## 8. Risks / gotchas

- **API drift:** Upstash renamed endpoints before (`/v1` → `/v2`, `get-library-docs` → `query-docs`). Pin the MCP package version; you control both sides, so drift only matters when you choose to rebase.
- **Empty-body semantics:** `/v2/context` returning `""` is treated as "not found" — always return at least a "no relevant snippets" sentence on a valid library.
- **Chunking quality > model choice.** A mediocre embedder with snippet-aware chunking beats a great embedder over blind 512-token windows.
- **Licensing:** MCP client is MIT; reimplementing the API shape is clean-room-by-construction since the contract is visible in the open client.
