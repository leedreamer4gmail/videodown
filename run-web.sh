#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export VIDEODOWN_DOWNLOAD_DIR="${VIDEODOWN_DOWNLOAD_DIR:-$ROOT/downloads}"
mkdir -p "$VIDEODOWN_DOWNLOAD_DIR"
exec "$ROOT/.venv/bin/uvicorn" videodown.web.server:app --host 127.0.0.1 --port 8765
