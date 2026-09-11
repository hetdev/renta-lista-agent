#!/usr/bin/env bash
# Build AgentCore CodeZip for Python 3.13 arm64.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/dist/agent"
rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$ROOT/src/rentalista" "$OUT/"
cd "$ROOT"
uv export --no-dev --no-emit-project -o /tmp/rentalista-req.txt
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.13 \
  --only-binary=:all: \
  --target "$OUT" \
  -r /tmp/rentalista-req.txt
# AgentCore expects a single zip
cd "$OUT"
zip -qr9 "$ROOT/dist/rentalista-agent.zip" .
echo "wrote $ROOT/dist/rentalista-agent.zip ($(du -h "$ROOT/dist/rentalista-agent.zip" | cut -f1))"
