#!/usr/bin/env bash

set -euo pipefail

echo "== Compile backend =="
python -m compileall -q \
  app \
  tests \
  scripts

echo "== Run unit tests =="
python -m unittest discover \
  -s tests \
  -v

echo "== Verify Alembic revision =="
python -m alembic \
  -c alembic.ini \
  current

python -m alembic \
  -c alembic.ini \
  heads

if [[ "${RUN_E2E:-0}" == "1" ]]; then
  echo "== Run live API E2E check =="

  python scripts/backend_e2e_check.py \
    ${E2E_ARGS:-}
fi

echo "Backend final checks passed."