#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  printf '%s\n' "usage: scripts/vendor_manifest.sh <directory>" >&2
  exit 64
fi

target=$1
if [ ! -d "$target" ]; then
  printf '%s\n' "directory not found: $target" >&2
  exit 66
fi

find "$target" -type f \
  ! -path '*/.git/*' \
  ! -path '*/node_modules/*' \
  ! -path '*/dist/*' \
  -print0 \
  | sort -z \
  | xargs -0 shasum -a 256
