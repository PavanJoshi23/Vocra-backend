#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"

cd "$BACKEND"

if ! conda env list | grep -qE '^vocra\s'; then
  echo "Creating conda env 'vocra'..."
  conda env create -f environment.yml
fi

eval "$(conda shell.bash hook)"
conda activate vocra

exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
