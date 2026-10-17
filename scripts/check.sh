#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ] || [ ! -d frontend/node_modules ]; then
  echo 'Install the pinned backend and frontend dependencies first; see README.md.' >&2
  exit 1
fi

PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
PYTHONPATH=backend .venv/bin/python scripts/evaluate.py
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python scripts/check_docs.py
