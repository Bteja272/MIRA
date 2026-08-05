#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8001}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:5173}"
RUN_E2E="${RUN_E2E:-0}"

print_step() {
  printf '\n==> %s\n' "$1"
}

print_step "Checking project directories"

test -d "$PROJECT_ROOT/app"
test -d "$PROJECT_ROOT/tests"
test -d "$FRONTEND_DIR"

print_step "Running backend tests"

cd "$PROJECT_ROOT"

python -m unittest discover \
  -s tests \
  -v

print_step "Running frontend lint"

cd "$FRONTEND_DIR"

npm run lint

print_step "Running frontend unit and integration tests"

npm run test

print_step "Building frontend production bundle"

npm run build

if [[ "$RUN_E2E" == "1" ]]; then
  print_step "Checking live backend"

  curl \
    --fail \
    --silent \
    --show-error \
    "$BACKEND_URL/health" \
    >/dev/null

  print_step "Checking live frontend"

  curl \
    --fail \
    --silent \
    --show-error \
    "$FRONTEND_URL" \
    >/dev/null

  print_step "Running Cypress end-to-end tests"

  CYPRESS_BASE_URL="$FRONTEND_URL" \
    npm run test:e2e
else
  printf '\nE2E tests skipped. Run with RUN_E2E=1 after starting FastAPI and Vite.\n'
fi

printf '\nAll requested MIRA checks passed.\n'