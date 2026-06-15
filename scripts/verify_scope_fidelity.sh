#!/usr/bin/env sh
set -eu

if find app tests examples libraries scripts -name '*.html' -print | grep -q .; then
  printf '%s\n' 'unexpected web UI artifact' >&2
  exit 1
fi
if find . -path './src/context7--upstash-context7-mcp-3.2.1' -prune -o -name '*k8s*' -o -name '*.kube.yaml' -print | grep -q .; then
  printf '%s\n' 'unexpected Kubernetes artifact' >&2
  exit 1
fi
if rg -n 'OIDC|oauth|team auth|LLM snippet|sitemap crawl' app tests; then
  printf '%s\n' 'unexpected out-of-scope implementation marker' >&2
  exit 1
fi
printf '%s\n' 'SCOPE FIDELITY APPROVED'
